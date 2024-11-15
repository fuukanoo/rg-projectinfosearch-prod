# Azure AIサービスを利用したRAG (まだ未完成)
 
 
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
- **Azure Computer Vision**
- **Azure Document Intelligence**
- **Azure AI Search**
- **Azure OpenAI**
- **Azure **
- **Python 3.10**
- **VSCode**
- **Azure CLI**
 
 
 
## 環境構築
 
```
git clone https://github.com/sakuya10969/rag.git
cd rag
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
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "COMPUTER_VISION_KEY": "your_computer_vision_key",
    "COMPUTER_VISION_ENDPOINT": "your_computer_vision_endpoint",
    "OPENAI_KEY": "your_openai_key,
    "OPENAI_ENDPOINT": "your_openai_endpoint",
    "DOCUMENT_INTELLIGENCE_KEY":your_document_intelligence_key",
    "DOCUMENT_INTELLIGENCE_ENDPOINT":"your_document_intelligence_endpoint",
    "BLOB_STORAGE_CONNECTION_STRING":"your_blob_storage_connection_string",
    "AI_SEARCH_KEY":"your_ai_search_key",
    "AI_SEARCH_ENDPOINT":"your_ai_search_endpoint",
    "AI_SEARCH_ADMIN_KEY":"your_ai_search_admin_key"
  }
}
```
 
 
 
## 使用方法
 
```
func start
```
 
上記のコマンドの実行でサーバーを立ち上げます。<br>
 
POSTMANを使い、JSON形式でファイルの指定をすることで画像、ドキュメント内のテキストを抽出し、修正された文章の表示ができます。