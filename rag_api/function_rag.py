import azure.functions as func

import openai
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
import os
import logging
import uuid
#from datetime import datetime
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from langchain_community.document_loaders import AzureAIDocumentIntelligenceLoader
from langchain.text_splitter import MarkdownHeaderTextSplitter
from langchain_community.vectorstores import AzureSearch
#import requests
#import ipdb
from langchain import hub
from langchain.schema import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough
#from operator import itemgetter
#from langchain.schema.runnable import RunnableMap
from pydantic import BaseModel

# from docx import Document
# from io import BytesIO
# from fpdf import FPDF
# from fastapi import UploadFile, HTTPException
# from magic import Magic
# from pptx import Presentation



# FastAPI アプリケーションの初期化
app = FastAPI()

# 環境変数から設定を取得
intelligence_key = os.getenv("DOCUMENT_INTELLIGENCE_API_KEY")
intelligence_endpoint = os.getenv("DOCUMENT_INTELLIGENCE_ENDPOINT")
vector_store_password = os.getenv("AZURE_SEARCH_ADMIN_KEY")
vector_store_address = os.getenv("AZURE_SEARCH_ENDPOINT")
openai_embedding_key = os.getenv("AZURE_OPENAI_EMBEDDING_API_KEY")
openai_embedding_endpoint = os.getenv("AZURE_OPENAI_EMBEDDING_ENDPOINT")
openai.api_key = os.getenv("AZURE_OPENAI_API_KEY")
openai.azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")  

# リクエストボディのスキーマ定義
class AnswerRequest(BaseModel):
    user_question: str
    conversation_id: str = None  # オプション項目（指定がない場合はNone）

# class PDF(FPDF):
#     def __init__(self):
#         super().__init__()
#         self.add_font("IPAexGothic", fname="ipaexg.ttf", uni=True)

@app.post("/upload")
async def upload(file: UploadFile = File(...), file_type: str = Form(...)):
    """
    フロントエンドからアップロードされたファイルを読み取り、ベクトル化して Azure Search にインデックスする。
    """
    try:
        file_content = await file.read()  # アップロードされたファイルを読み込む
        file_type = file_type

        extracted_text = extract_text(file_content)  # テキスト抽出
        indexed_docs = process_text(extracted_text)  # ベクトル化とインデックス化
        logging.info(f"chanking_text: {indexed_docs}")
        return JSONResponse(
            content={"message": "ファイルのアップロード成功"}
        )
    except Exception as e:
        logging.error(f"エラー: {e}")
        raise HTTPException(status_code=500, detail="ファイルアップロード中にエラーが起きました。")


@app.post("/answer")
async def answer(request: AnswerRequest):
    """
    質問に対する応答を生成し、フロントエンドに返す。
    """
    try:
        user_question = request.user_question
        conversation_id = request.conversation_id if request.conversation_id else str(uuid.uuid4())  # 会話 ID を生成        
        answer = generate_answer(user_question, conversation_id)
        return JSONResponse(content={"answer": answer, "conversation_id": conversation_id})
    except Exception as e:
        logging.error(f"Error generating answer: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate answer")



def extract_text(file_content):
    """
    ファイルのバイト列からテキストを抽出。
    """
    try:
        loader = AzureAIDocumentIntelligenceLoader(
            bytes_source=file_content,
            api_key=intelligence_key,
            api_endpoint=intelligence_endpoint,
            api_model="prebuilt-layout",
        )
        docs = loader.load()
        text_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[("#", "Header 1"), ("##", "Header 2"), ("###", "Header 3")]
        )
        docs_string = "\n\n".join(doc.page_content for doc in docs)
        splits = text_splitter.split_text(docs_string)
        return splits
    except Exception as e:
        logging.error(f"Error extracting text from file: {e}")
        raise


def process_text(splits):
    """
    テキストをベクトル化し、Azure Search にインデックス化。
    """
    try:
        aoai_embeddings = AzureOpenAIEmbeddings(
            azure_deployment="text-embedding-ada-002",
            openai_api_version="2023-05-15",
            openai_api_key=openai_embedding_key,
            azure_endpoint=openai_embedding_endpoint,
        )
        vector_store = AzureSearch(
            azure_search_endpoint=vector_store_address,
            azure_search_key=vector_store_password,
            index_name="idx-rag-dev",
            embedding_function=aoai_embeddings.embed_query,
        )
        vector_store.add_documents(documents=splits)
        return splits
    except Exception as e:
        logging.error(f"Error in vectorization and indexing: {e}")
        raise


def generate_answer(user_question, conversation_id):
    """
    質問に基づいて応答を生成。
    """
    try:
        
        retriever = AzureSearch(
            azure_search_endpoint=vector_store_address,
            azure_search_key=vector_store_password,
            index_name="idx-rag-dev",
            embedding_function=AzureOpenAIEmbeddings(
                azure_deployment="text-embedding-ada-002",
                openai_api_version="2023-05-15",
                openai_api_key=openai_embedding_key,
                azure_endpoint=openai_embedding_endpoint,
            ).embed_query,
        ).as_retriever(search_type="similarity")

        retrieved_docs = retriever.get_relevant_documents(user_question)[:5]
        logging.info(f"retrieved_docs: {retrieved_docs}")

        llm = AzureChatOpenAI(
            openai_api_key=openai.api_key,
            azure_endpoint=openai.azure_endpoint,
            openai_api_version="2023-05-15",
            azure_deployment="gpt-35-turbo",
            temperature=0,
        )

        # ベクトルストアから取り出したdocumentからpage_contentの内容だけを抽出し、連結.
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
        
        # Use a prompt for RAG that is checked into the LangChain prompt hub (https://smith.langchain.com/hub/rlm/rag-prompt?organizationId=989ad331-949f-4bac-9694-660074a208a7)
        prompt = hub.pull("rlm/rag-prompt")
        
        rag_chain = (
            {"context": retriever | format_docs, "question": RunnablePassthrough()} # step1
            | prompt # step2
            | llm # step 3
            | StrOutputParser() # step4
        )

        # 会話の回答生成
        answer = rag_chain.invoke(user_question)
        return answer
    

    except Exception as e:
        logging.error(f"Error generating answer with prompt: {e}")
        raise
