# p30_logging - LangGraph クイックスタート（ロギング版）

このプロジェクトは、p23と同じ構造で、計算エージェントを実装したものです。
LangSmithの無料プランではトレース件数が限られているため、自前実装部分の検証はログで確認できるように日本語のログを追加しています。

LangGraph Studio（`langgraph dev`）で使用できます。

## 構造

```
p30_logging/
├── my_agent/              # プロジェクトコード
│   ├── utils/             # グラフ用のユーティリティ
│   │   ├── __init__.py
│   │   ├── state.py       # グラフの状態定義
│   │   ├── nodes.py       # グラフ用のノード関数（ログ付き）
│   │   ├── tools.py       # グラフ用のツール（ログ付き）
│   │   └── logging_config.py  # ロギング設定
│   ├── __init__.py
│   └── agent.py          # グラフを構築するコード（ログ付き）
├── tests/                 # テストコード
│   ├── __init__.py
│   ├── conftest.py        # 共通フィクスチャ
│   └── test_invoke.py    # invokeテスト
├── langgraph.json         # LangGraph設定ファイル
└── README.md             # このファイル
```

## セットアップ

### 1. 依存関係のインストール

親フォルダで実行済み。

### 2. 環境変数の設定

親フォルダで実行済み。

### 3. LangGraph Studioで実行

```bash
langgraph dev
```

サーバーが起動すると、以下のURLでアクセスできます：
- **APIエンドポイント**: `http://127.0.0.1:2024`
- **Studio UI**: `https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024`

## 機能

このエージェントは、以下の計算ツールを使用できます：

- **add**: 2つの数値を加算
- **multiply**: 2つの数値を乗算
- **divide**: 2つの数値を除算

## ロギング機能

### ログファイル

- **通常ログ**: `p30_logging.log` (デフォルト)
- **エラーログ**: `p30_logging_error.log` (ERROR/CRITICALレベルのみ)

### 環境変数

以下の環境変数でロギングをカスタマイズできます：

- `LOG_LEVEL`: ログレベル (DEBUG, INFO, WARNING, ERROR) - デフォルト: INFO
- `LOG_FILE`: ログファイル名 - デフォルト: `p30_logging.log`
- `LOG_DIR`: ログファイルのディレクトリ - デフォルト: `.` (現在のディレクトリ)
- `LOG_USE_PYTHON_ROTATION`: Pythonローテーションを使用するか (true/false) - デフォルト: true
- `ENVIRONMENT`: 環境 (production, development, staging) - デフォルト: development

### ログの内容

自前実装部分（nodes.py, tools.py, agent.py）に以下のような日本語ログが出力されます：

- **エージェント初期化**: モデルの初期化、ツールのバインド、グラフの構築
- **LLM呼び出し**: 呼び出し開始/完了、ツール呼び出しの検出
- **ツール実行**: ツール名、引数、結果
- **ルーティング**: 次のノードへのルーティング判定
- **エラー**: エラー発生時の詳細情報

### ログの確認方法

1. **コンソール出力**: 実行時にコンソールにログが表示されます
2. **ログファイル**: `p30_logging.log` ファイルを確認
3. **エラーログ**: `p30_logging_error.log` ファイルでエラーのみを確認

## p23との違い

- **ロギング機能**: Morizo-aiv2のロギング実装を参考にした日本語ログを追加
- **自前実装部分の可視化**: nodes.py, tools.py, agent.pyに詳細なログを追加
- **ログファイル出力**: コンソールとファイルの両方にログを出力

## テストの実行

**注意**: テストを実行する前に、親ディレクトリで仮想環境を有効化してください。

```bash
# 親ディレクトリで仮想環境を有効化
cd /root/LearnLangGraph
source venv/bin/activate  # Linux/macOS

# p30_loggingディレクトリに移動
cd archives/p30_logging

# すべてのテストを実行
pytest

# 特定のテストファイルを実行
pytest tests/test_invoke.py

# 詳細な出力で実行
pytest -v

# ログを表示しながら実行
pytest -v -s
```

### 実装されているテスト

- **test_graph_invoke_add**: 加算計算のinvokeテスト
- **test_graph_invoke_multiply**: 乗算計算のinvokeテスト
- **test_graph_invoke_divide**: 除算計算のinvokeテスト
- **test_graph_invoke_multiple_operations**: 複数の計算を連続で行うテスト
- **test_graph_invoke_state_structure**: 状態の構造を確認するテスト
- **test_graph_invoke_empty_messages**: 空のメッセージでグラフを実行するテスト
- **test_graph_invoke_multiple_requests**: 複数の異なる計算要求でグラフを実行するテスト
- **test_graph_invoke_llm_calls_counter**: LLM呼び出しカウンターが正しく動作することを確認するテスト
- **test_graph_invoke_tool_execution**: ツールが実行されることを確認するテスト

## 参考プロジェクト

このプロジェクトのロギング実装は、`/root/Morizo-aiv2` のロギング実装を参考にしています。

