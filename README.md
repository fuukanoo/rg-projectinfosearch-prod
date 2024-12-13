# Azure AIサービスを利用したRAG 
 
 
## 目次
 
1. [プロジェクト概要](#プロジェクト概要)
2. [前提条件](#前提条件)
3. [環境構築](#環境構築)
4. [使用方法](#使用方法)
 
 
 
## プロジェクト概要
 
RAG（Retrieval-Augmented Generation）は、事前に収集した大量のデータから関連する情報を抽出し、その情報を基にユーザーに適切な応答を生成する技術です。
このプロジェクトでは、AzureのAIサービスを活用し、アップロードされた画像やドキュメントからテキストを抽出して、それを検索ベースでリクエスト内容に関連する情報を返答する仕組みを構築しています。
複雑なレイアウトのPDFファイル等も、セマンティックチャンキング法により高精度に抽出することが可能です。
主な利用シナリオとしては、システム開発における要件定義書や設計書といった資料を取り扱い、これらから必要な情報を素早く引き出せる点が挙げられます。
 
 
 
## 前提条件
 
このプロジェクトを動かすために必要なツールやリソース
 
- **Azure サブスクリプション**
- **Azure Functions Core Tools**
- **Azure Cosmos DB**
- **Azure Blob Storage**
- **Azure Document Intelligence**
- **Azure AI Search**
- **Azure OpenAI**
- **Python 3.10**
- **VSCode**
- **Azure CLI**
 
 
 
## 環境構築
 
```
git clone git@gitlab.com:intelligentforce/azure_rag.git
cd azure_rag
```
 
### 仮想環境の構築と必要なライブラリのインストール
 
```
pyenv local 3.10.15
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
 
### local_settings.jsonで環境変数の設定
それぞれのバリューには適切なものを入力してください
```
{
    "IsEncrypted": false,
    "Values": {
      "AzureWebJobsStorage": "seDevelopmentStorage=true",
      "FUNCTIONS_WORKER_RUNTIME": "python",
      "COMPUTER_VISION_API_KEY": "0e9d45323e834cd3a0b566ab8a75e9e9",
      "COMPUTER_VISION_ENDPOINT": "https://cv-rag-dev.cognitiveservices.azure.com/",
      "AZURE_OPENAI_API_KEY":"a501328d19a04df89960b2c636af48f4",
      "AZURE_OPENAI_ENDPOINT":"https://shuns-m2mw0u2v-westeurope.openai.azure.com/openai/deployments/gpt-35-turbo/chat/completions?api-version=2024-08-01-preview",
      "AZURE_OPENAI_EMBEDDING_API_KEY":"a501328d19a04df89960b2c636af48f4",
      "AZURE_OPENAI_EMBEDDING_ENDPOINT":"https://shuns-m2mw0u2v-westeurope.openai.azure.com/openai/deployments/text-embedding-ada-002/embeddings?api-version=2023-05-15",
      "DOCUMENT_INTELLIGENCE_API_KEY":"bb4b80af7f3347a38e44af9acbe92ac7",
      "DOCUMENT_INTELLIGENCE_ENDPOINT":"https://di-rag-dev.cognitiveservices.azure.com/",
      "AZURE_SEARCH_ENDPOINT":"https://srch-rag-dev-013.search.windows.net",
      "AZURE_SEARCH_ADMIN_KEY":"NOI2T2fDQ2gn3ulIqhz1fFIzJ5SR5USRrs9zQTJc2cAzSeBUhqbV",
      "AZURE_STORAGE_CONNECTION_STRING":"DefaultEndpointsProtocol=https;AccountName=strag013;AccountKey=giUJhMCOlk9uaKTg27MQ8q5RxMpcMHebyvK/aUfRLvuczCsbMGfXEhVKFVWNjXlxMN886zBkeDgE+AStPXA1fg==;EndpointSuffix=core.windows.net",
      "BLOB_CONTAINER":"container-rag-dev",
      "COSMOS_DB_ENDPOINT":"https://cosdb-rag-dev.documents.azure.com:443/",
      "COSMOS_DB_KEY":"Vj3kGrgw6Lt9K0EiHB72ExuhFbCrKAmmdxdeufuPo1yj2LZ4IT49O2vCTmWbT7RBoaj1Z3kZhWcIACDbFgYk2A=="

    }
```
 
 
 
## 使用方法
 
```
func start
```
 
上記のコマンドの実行でサーバーを立ち上げます。<br>
 
POSTMANを使い、JSON形式でファイルの指定をすることで画像、ドキュメント内のテキストを抽出し、修正された文章の表示ができます。# azure_rag
