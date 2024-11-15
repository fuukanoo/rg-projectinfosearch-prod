import azure.functions as func
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
import os
import logging
import uuid
from datetime import datetime
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from langchain_community.document_loaders import AzureAIDocumentIntelligenceLoader
from langchain.text_splitter import MarkdownHeaderTextSplitter
from langchain_community.vectorstores import AzureSearch
from azure.functions import AsgiMiddleware

# FastAPIアプリケーションを初期化
app = FastAPI()

# 環境変数から設定を取得
intelligence_key = os.getenv("DOCUMENT_INTELLIGENCE_API_KEY")
intelligence_endpoint = os.getenv("DOCUMENT_INTELLIGENCE_ENDPOINT")
vector_store_password = os.getenv("AZURE_SEARCH_ADMIN_KEY")
vector_store_address = os.getenv("AZURE_SEARCH_ENDPOINT")
openai_embedding_key = os.getenv("AZURE_OPENAI_EMBEDDING_API_KEY")
openai_embedding_endpoint = os.getenv("AZURE_OPENAI_EMBEDDING_ENDPOINT")


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    """
    フロントエンドからアップロードされたファイルを読み取り、ベクトル化してAzure Searchにインデックスする。
    """
    try:
        # アップロードされたファイルを読み込む
        file_content = await file.read()

        # Document Intelligenceを使ってテキストを抽出
        extracted_text = extract_text(file_content)

        # テキストをベクトル化してAzure Searchにインデックス
        indexed_docs = process_text(extracted_text)

        return JSONResponse(
            content={
                "message": "ファイルのアップロード成功",
                "indexed_docs": indexed_docs,
            }
        )

    except Exception as e:
        logging.error(f"エラー: {e}")
        raise HTTPException(status_code=500, detail="ファイルアップロード中にエラーが起きました。")


@app.post("/answer")
async def answer(user_question: str, conversation_id: str = None):
    """
    質問に対する応答を生成し、フロントエンドに返す。
    """
    try:
        # 既存の会話IDがなければ新規作成
        conversation_id = conversation_id or str(uuid.uuid4())

        # 質問に基づいて応答を生成
        answer = generate_answer(user_question, conversation_id)

        return JSONResponse(
            content={"answer": answer, "conversation_id": conversation_id}
        )

    except Exception as e:
        logging.error(f"Error generating answer: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate answer")


def extract_text(file_content):
    """
    アップロードされたファイルのバイト列を直接読み取り、テキストを抽出する。
    """
    try:
        # ファイルコンテンツをDocument Intelligence APIで処理
        loader = AzureAIDocumentIntelligenceLoader(
            file_content=file_content,
            api_key=intelligence_key,
            api_endpoint=intelligence_endpoint,
            api_model="prebuilt-layout",
        )
        docs = loader.load()

        # チャンク分割
        headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        ]
        text_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=headers_to_split_on
        )
        docs_string = "\n\n".join(doc.page_content for doc in docs)
        splits = text_splitter.split_text(docs_string)

        return splits

    except Exception as e:
        logging.error(f"Error extracting text from file: {e}")
        raise


def process_text(splits):
    """
    テキストをベクトル化し、Azure Searchにインデックス。
    """
    try:
        # Azure OpenAIでベクトル化
        aoai_embeddings = AzureOpenAIEmbeddings(
            azure_deployment="text-embedding-ada-002",
            openai_api_version="2023-05-15",
            openai_api_key=openai_embedding_key,
            azure_endpoint=openai_embedding_endpoint,
        )

        # Azure Searchにインデックス
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
    質問に基づきプロンプトから応答を生成。
    """
    try:
        # Azure OpenAIの設定
        llm = AzureChatOpenAI(
            openai_api_key=openai_embedding_key,
            azure_endpoint=openai_embedding_endpoint,
            openai_api_version="2023-05-15",
            azure_deployment="gpt-35-turbo",
            temperature=0,
        )

        # Azure Searchで関連ドキュメントを取得
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

        retrieved_docs = retriever.get_relevant_documents(user_question)

        # ドキュメントをフォーマットし、応答を生成
        formatted_docs = "\n\n".join(doc.page_content for doc in retrieved_docs)
        prompt = f"Context:\n{formatted_docs}\n\nQuestion: {user_question}\nAnswer:"
        answer = llm(prompt=prompt).text

        return answer

    except Exception as e:
        logging.error(f"Error generating answer with prompt: {e}")
        raise


# Azure FunctionsにFastAPIを統合
app_function = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)
app_function.add_route("/", AsgiMiddleware(app))
