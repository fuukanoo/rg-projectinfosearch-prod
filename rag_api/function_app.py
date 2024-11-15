import azure.functions as func
import os
from azure.storage.blob import BlobServiceClient
import logging
import requests
import json
import ipdb
import uuid

# import my library
from process_rag import process_rag

# get API_KEY and ENDPOINT
blob_connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
blob_container = os.getenv("BLOB_CONTAINER")


# route setting
app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.route(route="function_rag")
def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing a request to extract and improve text from an image or document.')

    # リクエストボディからJSONデータを取得
    try:
        req_body = req.get_json()
    except ValueError:
        return func.HttpResponse("Invalid JSON format", status_code=400)

    user_question = req_body.get("user_question")

    if not user_question:
        return func.HttpResponse("Please provide 'user_question' in the request body.", status_code=400)

    # Blobストレージからファイルを取得
    blob_url = "https://strag013.blob.core.windows.net/container-rag-dev/入力データサンプル.pdf?sv=2022-11-02&ss=bfqt&srt=co&sp=rwdlacupiytfx&se=2024-12-08T09:44:49Z&st=2024-11-08T01:44:49Z&spr=https&sig=3%2BdOw91lvdNbf9vCnbzm%2BbMp8rT%2B6Xt4nIObLmPVWrw%3D"
    answer = extract_text_from_blob_url(blob_url, user_question)
    logging.info(f"answer:\n {answer}")
    
    response = {
            "documents": answer["documents"],
            "answer": answer["answer"]
        }

    return func.HttpResponse(
            json.dumps(response),
            status_code=200,
            mimetype="application/json"
        )


def extract_text_from_blob_url(blob_url, user_question):
    """URLからBlobストレージ上のファイルを取得し、適切な方法でテキストを抽出"""
    try:
        # URLからファイルをダウンロード
        response = requests.get(blob_url)
        response.raise_for_status()  # ステータスコードがエラーの場合例外を発生
        # 会話のための一意のIDを生成（新しい会話の場合）
        conversation_id = str(uuid.uuid4())
        return process_rag(blob_url, user_question, conversation_id)
    
    except requests.exceptions.RequestException as e:
        logging.error(f"Error downloading the blob from URL: {e}")
        return f"Error downloading the blob from URL: {e}"
    except Exception as e:
        logging.error(f"Error processing the blob: {e}")
        return f"Error processing the blob: {e}"
