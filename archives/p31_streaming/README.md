# p31_streaming - ストリーミング対応のLangGraphエージェント

このプロジェクトは、Vercel AI SDKのチャットから呼び出せるストリーミング対応のLangGraphエージェントです。
LangGraph Studio（`langgraph dev`）で使用できます。

## 構造

```
p31_streaming/
├── my_agent/              # プロジェクトコード
│   ├── utils/             # グラフ用のユーティリティ
│   │   ├── __init__.py
│   │   ├── state.py       # グラフの状態定義
│   │   ├── nodes.py       # グラフ用のノード関数（ログ付き）
│   │   └── logging_config.py  # ロギング設定
│   ├── __init__.py
│   └── agent.py          # グラフを構築するコード（ログ付き）
├── tests/                # テストファイル
│   ├── __init__.py
│   └── test_invoke.py    # invokeのテスト
├── langgraph.json         # LangGraph設定ファイル
└── README.md             # このファイル
```

## 機能

このエージェントは、以下の処理を行います：

1. **トピック抽出**: メッセージからトピックを抽出します
2. **トピックの精緻化**: 抽出されたトピックを、より面白く魅力的なトピックに精緻化します
3. **ジョーク生成**: 精緻化されたトピックについて、面白いジョークを生成します

## セットアップ

### 1. 依存関係のインストール

以下の依存関係が必要です：
- langchain
- langchain-openai
- langgraph
- python-dotenv (オプション)

親フォルダで実行済みの場合、それらを使用できます。

### 2. 環境変数の設定

親フォルダで実行済み。

### 3. LangGraph Studioで実行

```bash
cd /root/LearnLangGraph/archives/p31_streaming
langgraph dev
```

サーバーが起動すると、以下のURLでアクセスできます：
- **APIエンドポイント**: `http://127.0.0.1:2024`
- **Studio UI**: `https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024`

## Vercel AI SDKからの呼び出し

Vercel AI SDKのチャットから呼び出すには、以下の設定を使用します：

- **API URL**: `http://localhost:2024` (またはデプロイ先のURL)
- **Assistant ID**: `p31_streaming`

## テスト

invokeが正常に動作することを確認するテストを実行できます：

```bash
cd /root/LearnLangGraph/archives/p31_streaming
python -m pytest tests/test_invoke.py -v
```

または、直接実行：

```bash
python tests/test_invoke.py
```

## ロギング機能

### ログファイル

- **通常ログ**: `p31_streaming.log` (デフォルト)
- **エラーログ**: `p31_streaming_error.log` (ERROR/CRITICALレベルのみ)

### 環境変数

以下の環境変数でロギングをカスタマイズできます：

- `LOG_LEVEL`: ログレベル (DEBUG, INFO, WARNING, ERROR) - デフォルト: INFO
- `LOG_FILE`: ログファイル名 - デフォルト: `p31_streaming.log`
- `LOG_DIR`: ログファイルのディレクトリ - デフォルト: `.` (現在のディレクトリ)
- `LOG_USE_PYTHON_ROTATION`: Pythonローテーションを使用するか (true/false) - デフォルト: true
- `ENVIRONMENT`: 環境 (production, development, staging) - デフォルト: development

### ログの内容

自前実装部分（nodes.py, agent.py）に以下のような日本語ログが出力されます：

- **エージェント初期化**: モデルの初期化、グラフの構築
- **トピック抽出**: メッセージからトピックを抽出する処理
- **トピック精緻化**: LLM呼び出し開始/完了、精緻化されたトピック
- **ジョーク生成**: LLM呼び出し開始/完了、生成されたジョーク
- **エラー**: エラー発生時の詳細情報

### ログの確認方法

1. **コンソール出力**: 実行時にコンソールにログが表示されます
2. **ログファイル**: `p31_streaming.log` ファイルを確認
3. **エラーログ**: `p31_streaming_error.log` ファイルでエラーのみを確認

## 元のコードとの違い

- **構造化**: p23の構造に従った実装
- **ストリーミング対応**: Vercel AI SDKのチャットから呼び出し可能
- **Studio対応**: `langgraph dev`で使用可能
- **ロギング機能**: p30_loggingを参考にした日本語ログを追加
- **テスト**: invokeの動作を確認するテストを含む

