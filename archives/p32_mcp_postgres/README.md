# p32_mcp_postgres - MCPサーバー統合のLangGraphエージェント（PostgreSQL対応）

このプロジェクトは、MCP（Model Context Protocol）サーバーを通じてPostgreSQLデータベースに接続し、ユーザーのクエリに基づいてデータベースから情報を取得するLangGraphエージェントです。
Vercel AI SDKのチャットから呼び出せるストリーミング対応で、LangGraph Studio（`langgraph dev`）で使用できます。

## 構造

```
p32_mcp_postgres/
├── my_agent/              # プロジェクトコード
│   ├── utils/             # グラフ用のユーティリティ
│   │   ├── __init__.py
│   │   ├── state.py       # グラフの状態定義
│   │   ├── nodes.py       # グラフ用のノード関数（ログ付き）
│   │   └── logging_config.py  # ロギング設定
│   ├── __init__.py
│   └── agent.py          # グラフを構築するコード（MCP統合、ログ付き）
├── tests/                # テストファイル
│   ├── __init__.py
│   └── test_invoke.py    # invokeのテスト
├── langgraph.json         # LangGraph設定ファイル
├── mcp.json              # MCPサーバー設定ファイル（参考用）
└── README.md             # このファイル
```

## 機能

このエージェントは、以下の処理を行います：

1. **クエリ意図抽出**: メッセージからクエリ意図を抽出します
2. **PostgreSQLクエリ実行**: MCPサーバーを通じてPostgreSQLデータベースにクエリを実行します
3. **結果の整形**: クエリ結果をユーザーにとって分かりやすい形式で説明します

## セットアップ

### 1. 依存関係のインストール

以下の依存関係が必要です：
- langchain
- langchain-openai
- langgraph
- langchain-mcp-adapters
- python-dotenv (オプション)
- Node.js (MCPサーバー実行用)

親フォルダで実行済みの場合、それらを使用できます。

追加で必要なパッケージをインストール：

```bash
pip install langchain-mcp-adapters
```

### 2. 環境変数の設定

`.env`ファイルに以下の環境変数を設定してください：

```bash
# OpenAI API設定
OPENAI_API_KEY=your-api-key-here
OPENAI_MODEL=gpt-4o-mini

# PostgreSQL接続設定（Vercel Postgres）
# 注意: MCPサーバーは直接接続が必要なため、UNPOOLED版を使用してください
POSTGRES_CONNECTION_STRING=postgresql://default:password@ep-xxxxx.aws.neon.tech/verceldb?sslmode=require
# または、Vercelダッシュボードの DATABASE_URL_UNPOOLED の値をそのまま使用
# POSTGRES_CONNECTION_STRING=${DATABASE_URL_UNPOOLED}

# ロギング設定（オプション）
LOG_LEVEL=INFO
LOG_FILE=p32_mcp_postgres.log
LOG_DIR=.
ENVIRONMENT=development
```

**Vercel Postgresの接続文字列の取得方法：**

1. Vercelダッシュボードにログイン
2. プロジェクトを選択
3. Settings > Storage > Postgres を開く
4. `.env.local`タブで接続文字列を確認
5. **`DATABASE_URL_UNPOOLED`の値を`POSTGRES_CONNECTION_STRING`に設定**
   - MCPサーバーは直接接続が必要なため、pgbouncer経由の`DATABASE_URL`ではなく、`DATABASE_URL_UNPOOLED`を使用してください
   - 形式: `postgresql://default:password@ep-xxxxx.aws.neon.tech/verceldb?sslmode=require`

### 3. MCPサーバーの設定

MCPサーバーは、`langchain-mcp-adapters`が自動的に起動・管理します。
環境変数`POSTGRES_CONNECTION_STRING`が設定されていれば、自動的にPostgreSQLに接続されます。

### 4. LangGraph Studioで実行

```bash
cd /root/LearnLangGraph/archives/p32_mcp_postgres
langgraph dev
```

サーバーが起動すると、以下のURLでアクセスできます：
- **APIエンドポイント**: `http://127.0.0.1:2024`
- **Studio UI**: `https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024`

## Vercel AI SDKからの呼び出し

Vercel AI SDKのチャットから呼び出すには、以下の設定を使用します：

- **API URL**: `http://localhost:2024` (またはデプロイ先のURL)
- **Assistant ID**: `p32_mcp_postgres`

## テスト

invokeが正常に動作することを確認するテストを実行できます：

```bash
cd /root/LearnLangGraph/archives/p32_mcp_postgres
python -m pytest tests/test_invoke.py -v
```

または、直接実行：

```bash
python tests/test_invoke.py
```

## ロギング機能

### ログファイル

- **通常ログ**: `p32_mcp_postgres.log` (デフォルト)
- **エラーログ**: `p32_mcp_postgres_error.log` (ERROR/CRITICALレベルのみ)

### 環境変数

以下の環境変数でロギングをカスタマイズできます：

- `LOG_LEVEL`: ログレベル (DEBUG, INFO, WARNING, ERROR) - デフォルト: INFO
- `LOG_FILE`: ログファイル名 - デフォルト: `p32_mcp_postgres.log`
- `LOG_DIR`: ログファイルのディレクトリ - デフォルト: `.` (現在のディレクトリ)
- `LOG_USE_PYTHON_ROTATION`: Pythonローテーションを使用するか (true/false) - デフォルト: true
- `ENVIRONMENT`: 環境 (production, development, staging) - デフォルト: development

### ログの内容

自前実装部分（nodes.py, agent.py）に以下のような日本語ログが出力されます：

- **エージェント初期化**: モデルの初期化、MCPツールの作成、グラフの構築
- **クエリ意図抽出**: メッセージからクエリ意図を抽出する処理
- **PostgreSQLクエリ実行**: MCPツールの呼び出し、クエリ結果の取得
- **結果の整形**: LLM呼び出し開始/完了、整形された応答
- **エラー**: エラー発生時の詳細情報

### ログの確認方法

1. **コンソール出力**: 実行時にコンソールにログが表示されます
2. **ログファイル**: `p32_mcp_postgres.log` ファイルを確認
3. **エラーログ**: `p32_mcp_postgres_error.log` ファイルでエラーのみを確認

## MCPサーバーについて

このプロジェクトでは、以下のMCPサーバーを使用しています：

- **postgres-mcp-server**: PostgreSQLデータベースへの接続とクエリ実行を提供
  - GitHub: https://github.com/ahmedmustahid/postgres-mcp-server
  - パッケージ: `@modelcontextprotocol/server-postgres`

MCPサーバーは、`langchain-mcp-adapters`が自動的に起動・管理します。
環境変数`POSTGRES_CONNECTION_STRING`が設定されていれば、自動的にPostgreSQLに接続されます。

## 使用例

### テーブル一覧の取得

```
ユーザー: データベースのテーブル一覧を表示してください
```

### データの検索

```
ユーザー: usersテーブルから最新の10件のデータを取得してください
```

### スキーマの確認

```
ユーザー: productsテーブルのスキーマを表示してください
```

## 元のコードとの違い

- **MCP統合**: langchain-mcp-adaptersを使用してMCPサーバーと統合
- **PostgreSQL対応**: postgres-mcp-serverを通じてPostgreSQLに接続
- **構造化**: p31_streamingの構造に従った実装
- **ストリーミング対応**: Vercel AI SDKのチャットから呼び出し可能
- **Studio対応**: `langgraph dev`で使用可能
- **ロギング機能**: p30_loggingを参考にした日本語ログを追加
- **テスト**: invokeの動作を確認するテストを含む

## トラブルシューティング

### MCPツールが作成されない

- `POSTGRES_CONNECTION_STRING`が正しく設定されているか確認
- `langchain-mcp-adapters`がインストールされているか確認
- Node.jsがインストールされているか確認（`npx`コマンドが必要）

### データベース接続エラー

- Vercel Postgresの接続文字列が正しいか確認
- データベースが起動しているか確認
- ファイアウォール設定を確認

### ログが出力されない

- `LOG_LEVEL`環境変数を`DEBUG`に設定
- ログファイルの書き込み権限を確認

## 参考リソース

- **LangGraph**: https://langchain-ai.github.io/langgraph/
- **langchain-mcp-adapters**: https://github.com/langchain-ai/langchain-mcp-adapters
- **postgres-mcp-server**: https://github.com/ahmedmustahid/postgres-mcp-server
- **Vercel Postgres**: https://vercel.com/docs/storage/vercel-postgres

