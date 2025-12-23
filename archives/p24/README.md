# p24 - LangGraph テスト実装

このプロジェクトは、P24_test.mdに従ったテストを実装したものです。
計算エージェントに対して、様々なテスト手法を実装しています。

## 構造

```
p24/
├── my_agent/              # プロジェクトコード
│   ├── utils/             # グラフ用のユーティリティ
│   │   ├── __init__.py
│   │   ├── state.py       # グラフの状態定義
│   │   ├── nodes.py       # グラフ用のノード関数
│   │   └── tools.py      # グラフ用のツール
│   ├── __init__.py
│   └── agent.py          # グラフを構築するコード
├── tests/                 # テストコード
│   ├── __init__.py
│   ├── conftest.py       # 共通フィクスチャ
│   ├── test_basic.py     # 基本的なテスト（グラフ実行、個別ノード）
│   ├── test_conditional.py  # 条件付きエッジのテスト
│   ├── test_partial.py   # 部分実行のテスト
│   ├── test_mock_llm.py  # LLMのモックテスト
│   ├── test_mock_tool.py # ツールのモックテスト
│   ├── test_fixtures.py  # pytestフィクスチャの使用
│   └── test_integration.py  # 結合テスト（実際のLLM使用）
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

## テストの実行

```bash
# すべてのテストを実行
pytest

# 特定のテストファイルを実行
pytest tests/test_basic.py

# 詳細な出力で実行
pytest -v

# カバレッジレポートを生成
pytest --cov=my_agent --cov-report=html
```

## 実装されているテスト

- **グラフの実行テスト**: グラフ全体の実行をテスト（LLMモック）
- **個別ノードのテスト**: 各ノードを個別にテスト（LLMモック）
- **条件付きエッジのテスト**: 条件分岐の動作をテスト（LLMモック）
- **部分実行のテスト**: 特定の部分のみをテスト（LLMモック）
- **LLMのモック**: LLM呼び出しをモックしたテスト
- **ツールのモック**: ツール呼び出しをモックしたテスト（LLMモック）
- **pytestフィクスチャの使用**: 再利用可能なテストコンポーネント
- **結合テスト**: 実際のLLMを使用したエンドツーエンドテスト
