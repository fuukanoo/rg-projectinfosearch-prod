import os
import logging
import ipdb
import openai
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest, AnalyzeResult, ContentFormat
from azure.cosmos import CosmosClient, PartitionKey
from langchain import hub
from langchain_openai import AzureChatOpenAI
from langchain_community.document_loaders import AzureAIDocumentIntelligenceLoader
from langchain_openai import AzureOpenAIEmbeddings
from langchain.schema import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough
from langchain.text_splitter import MarkdownHeaderTextSplitter
from langchain_community.vectorstores import AzureSearch
from operator import itemgetter
from langchain.schema.runnable import RunnableMap
import hashlib
import uuid
from datetime import datetime

# get API_KEY and ENDPOINT
intelligence_key = os.getenv("DOCUMENT_INTELLIGENCE_API_KEY")
intelligence_endpoint = os.getenv("DOCUMENT_INTELLIGENCE_ENDPOINT")
vector_store_password = os.getenv("AZURE_SEARCH_ADMIN_KEY")
vector_store_address = os.getenv("AZURE_SEARCH_ENDPOINT")
openai_embedding_key = os.getenv("AZURE_OPENAI_EMBEDDING_API_KEY")
openai_embedding_endpoint = os.getenv("AZURE_OPENAI_EMBEDDING_ENDPOINT")  
openai.api_key = os.getenv("AZURE_OPENAI_API_KEY")
openai.azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")  

# Cosmos DBの初期設定
cosmos_endpoint = os.getenv("COSMOS_DB_ENDPOINT")
cosmos_key = os.getenv("COSMOS_DB_KEY")
database_name = "DocumentDatabase"
container_name = "ConversationContainer"

# Cosmos DBのクライアント設定
cosmos_client = CosmosClient(cosmos_endpoint, cosmos_key)
database = cosmos_client.create_database_if_not_exists(id=database_name)
container = database.create_container_if_not_exists(
    id=container_name,
    partition_key=PartitionKey(path="/conversation_id"),
    offer_throughput=400
)

def generate_document_id(doc_string):
    """ドキュメントのユニークなIDを生成する"""
    return hashlib.sha256(doc_string.encode()).hexdigest()

def save_conversation(conversation_id, user_question, llm_answer):
    """会話をCosmos DBに保存する"""
    container.upsert_item({
        "id": str(uuid.uuid4()),
        "conversation_id": conversation_id,
        "timestamp": datetime.utcnow().isoformat(),
        "user_question": user_question,
        "llm_answer": llm_answer
    })

def get_conversation_history(conversation_id):
    """会話履歴をCosmos DBから取得する"""
    query = f"SELECT * FROM c WHERE c.conversation_id = '{conversation_id}' ORDER BY c.timestamp"
    items = container.query_items(query=query, enable_cross_partition_query=True)
    return [{"user_question": item["user_question"], "llm_answer": item["llm_answer"]} for item in items]

def process_rag(blob_url, user_question, conversation_id):
    """Document Intelligence APIを使ってドキュメントから文字を抽出し、セマンティックに細かくチャンク分割する"""
    try:
        # 既存の会話履歴を取得
        conversation_history = get_conversation_history(conversation_id)
        context_text = "\n".join([f"User: {entry['user_question']}\nAssistant: {entry['llm_answer']}" for entry in conversation_history])

        # Document Intelligenceでドキュメントのロードとテキスト抽出
        loader = AzureAIDocumentIntelligenceLoader(url_path=blob_url,
                                                   api_key=intelligence_key,
                                                   api_endpoint=intelligence_endpoint,
                                                   api_model="prebuilt-layout")
        docs = loader.load()

        # ドキュメントをチャンク分割
        headers_to_split_on = [("#", "Header 1"), ("##", "Header 2"), ("###", "Header 3")]
        text_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
        docs_string = docs[0].page_content
        splits = text_splitter.split_text(docs_string)

        # Azure OpenAIの埋め込みモデルでベクトルを生成
        aoai_embeddings = AzureOpenAIEmbeddings(
            azure_deployment="text-embedding-ada-002",
            openai_api_version="2023-05-15",
            openai_api_key=openai_embedding_key,
            azure_endpoint=openai_embedding_endpoint
        )
        
        index_name = "idx-rag-dev"  # Azure AI Search上のIndex名
        vector_store = AzureSearch(
            azure_search_endpoint=vector_store_address,
            azure_search_key=vector_store_password,
            index_name=index_name,
            embedding_function=aoai_embeddings.embed_query,
        )
        vector_store.add_documents(documents=splits)

        # 質問に基づき関連ドキュメントを取得
        retriever = vector_store.as_retriever(search_type="similarity")
        retrieved_docs = retriever.get_relevant_documents(user_question)
        logging.info(f"retrieved document:{retrieved_docs[0].page_content}")

        # RAG用のプロンプト生成と回答
        prompt = hub.pull("rlm/rag-prompt")
        llm = AzureChatOpenAI(
            openai_api_key=openai.api_key,
            azure_endpoint=openai.azure_endpoint,
            openai_api_version="2023-05-15",
            azure_deployment="gpt-35-turbo",
            temperature=0,
        )

        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)

        rag_chain_from_docs = (
            {
                "context": lambda input: f"{context_text}\n\n{format_docs(input['documents'])}",
                "question": itemgetter("question"),
            }
            | prompt
            | llm
            | StrOutputParser()
        )
        rag_chain_with_source = RunnableMap(
            {"documents": retriever, "question": RunnablePassthrough()}
        ) | {
            "documents": lambda input: [doc.metadata for doc in input["documents"]],
            "answer": rag_chain_from_docs,
        }

        # 会話の回答生成
        answer = rag_chain_with_source.invoke(user_question)
        
        # Cosmos DBに会話履歴を保存
        save_conversation(conversation_id, user_question, answer)

        return answer

    except Exception as e:
        logging.error(f"Error processing the document: {e}")
        return f"Error processing the document: {e}"
