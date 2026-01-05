# ex07_todo_agent - TODO管理エージェント

このプロジェクトは、ユーザーの依頼から「タスク」「期限」を抽出し、State内のリストを更新・削除するTODO管理エージェントです。
p31_streamingと同等のロギング・ストリーミング機能を実装しています。
Vercel AI SDKのチャットから呼び出して使用できます。
LangGraph Studio（`langgraph dev`）で使用できます。

## 構造

```
ex07_todo_agent/
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

1. **操作抽出 (Extract Node)**: ユーザーの発言から「操作の種類（追加/削除/更新など）」と「タスク内容・期限」をJSONで抽出します
2. **TODOリスト管理 (Logic Node)**: 抽出された情報に基づき、Pythonコードで State["todo_list"] を更新します
3. **返答生成 (Response Node)**: 「『資料作成』を期限1月10日で登録しました！」のように、人間フレンドリーな返答を作成します

## 状態 (State)

- `messages`: メッセージ履歴
- `todo_list`: タスクID、内容、期限、ステータス（done/undone）を持つオブジェクトのリスト
- `recent_change`: 今回のターンで「何が追加/削除されたか」の要約（ユーザーへの報告用）

### TODOアイテムの構造

- `task_id`: UUID（自動生成）
- `content`: タスク内容（文字列）
- `deadline`: 期限（yyyy-mm-dd形式の文字列）
- `status`: ステータス（"done" または "undone"）

## 操作の種類

- `add`: 新しいタスクを追加
- `delete`: タスクを削除（内容の部分一致で検索）
- `update_status`: タスクのステータスを更新（done/undoneの切り替え）
- `none`: 操作なし

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
cd /root/LearnLangGraph/archives/ex07_todo_agent
langgraph dev
```

サーバーが起動すると、以下のURLでアクセスできます：
- **APIエンドポイント**: `http://127.0.0.1:2024`
- **Studio UI**: `https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024`

## Vercel AI SDKからの呼び出し

Vercel AI SDKのチャットから呼び出すには、以下の設定を使用します：

- **API URL**: `http://localhost:2024` (またはデプロイ先のURL)
- **Assistant ID**: `ex07_todo_agent`

## テスト

invokeが正常に動作することを確認するテストを実行できます：

```bash
cd /root/LearnLangGraph/archives/ex07_todo_agent
python -m pytest tests/test_invoke.py -v
```

または、直接実行：

```bash
python tests/test_invoke.py
```

## ロギング機能

### ログファイル

- **通常ログ**: `ex07_todo_agent.log` (デフォルト)
- **エラーログ**: `ex07_todo_agent_error.log` (ERROR/CRITICALレベルのみ)

### 環境変数

以下の環境変数でロギングをカスタマイズできます：

- `LOG_LEVEL`: ログレベル (DEBUG, INFO, WARNING, ERROR) - デフォルト: INFO
- `LOG_FILE`: ログファイル名 - デフォルト: `ex07_todo_agent.log`
- `LOG_DIR`: ログファイルのディレクトリ - デフォルト: `.` (現在のディレクトリ)
- `LOG_USE_PYTHON_ROTATION`: Pythonローテーションを使用するか (true/false) - デフォルト: true
- `ENVIRONMENT`: 環境 (production, development, staging) - デフォルト: development

### ログの内容

自前実装部分（nodes.py, agent.py）に以下のような日本語ログが出力されます：

- **エージェント初期化**: モデルの初期化、グラフの構築
- **操作抽出**: ユーザーの発言から操作を抽出する処理
- **TODOリスト管理**: タスクの追加・削除・更新処理
- **返答生成**: LLM呼び出し開始/完了、生成された返答
- **エラー**: エラー発生時の詳細情報

### ログの確認方法

1. **コンソール出力**: 実行時にコンソールにログが表示されます
2. **ログファイル**: `ex07_todo_agent.log` ファイルを確認
3. **エラーログ**: `ex07_todo_agent_error.log` ファイルでエラーのみを確認

## 使用例

### タスクの追加

```
ユーザー: 「資料作成を1月10日までに登録して」
エージェント: 「『資料作成』を期限2024-01-10で追加しました。現在のTODOリストには1件の未完了タスクがあります。」
```

### タスクの削除

```
ユーザー: 「資料作成を削除して」
エージェント: 「『資料作成』を含むタスクを1件削除しました。現在のTODOリストは空です。」
```

### ステータスの更新

```
ユーザー: 「資料作成を完了にして」
エージェント: 「『資料作成』を含むタスクを1件、完了に更新しました。現在のTODOリストには0件の未完了タスクと1件の完了タスクがあります。」
```

## 元のコードとの違い

- **構造化**: p23の構造に従った実装
- **ストリーミング対応**: Vercel AI SDKのチャットから呼び出し可能
- **Studio対応**: `langgraph dev`で使用可能
- **ロギング機能**: p31_streamingと同等の日本語ログを追加
- **テスト**: invokeの動作を確認するテストを含む

