# Application Structure

このドキュメントでは、LangGraphアプリケーションの構造化と、プロジェクト構成のベストプラクティスについて解説します。

公式ドキュメント: https://docs.langchain.com/oss/python/langgraph/application-structure

## 概要

LangGraphアプリケーションは、本番環境でデプロイ可能な形で構造化する必要があります。適切な構造を持つことで、以下の利点が得られます：

- **保守性の向上**: コードが整理され、理解しやすくなる
- **スケーラビリティ**: 機能追加や変更が容易になる
- **デプロイの容易さ**: LangSmith Deploymentなどのプラットフォームへの展開が簡単になる
- **チーム開発**: 複数の開発者が協力しやすくなる

LangGraphアプリケーションは、以下の要素で構成されます：

1. **グラフ（Graphs）**: アプリケーションのロジックを実装する1つ以上のグラフ
2. **設定ファイル（langgraph.json）**: 依存関係、グラフ、環境変数を指定
3. **依存関係ファイル**: アプリケーションの実行に必要なパッケージを定義
4. **環境変数ファイル（.env）**: 環境固有の設定を管理（オプション）

## ファイル構造

### 基本的な構造

LangGraphアプリケーションの典型的なディレクトリ構造は以下の通りです：

```
my-app/
├── my_agent/              # プロジェクトコードのルート
│   ├── utils/             # グラフ用のユーティリティ
│   │   ├── __init__.py
│   │   ├── tools.py      # グラフ用のツール
│   │   ├── nodes.py      # グラフ用のノード関数
│   │   └── state.py      # グラフの状態定義
│   ├── __init__.py
│   └── agent.py          # グラフを構築するコード
├── tests/                 # テストコード（推奨）
│   ├── __init__.py
│   ├── conftest.py       # 共通フィクスチャ
│   ├── test_nodes.py     # ノードのユニットテスト
│   ├── test_tools.py     # ツールのユニットテスト
│   ├── test_graph.py     # グラフの統合テスト
│   └── test_integration.py  # エンドツーエンドテスト
├── .env                   # 環境変数（オプション）
├── requirements.txt      # パッケージ依存関係
├── pytest.ini            # pytest設定（オプション）
└── langgraph.json        # LangGraph設定ファイル
```

### ディレクトリ構造の説明

#### `my_agent/` - プロジェクトコード

アプリケーションのすべてのコードは、このディレクトリ内に配置します。

- **`agent.py`**: グラフを構築するメインコード
- **`utils/`**: グラフの実装に必要なユーティリティ
  - **`state.py`**: 状態（State）の定義
  - **`nodes.py`**: ノード関数の実装
  - **`tools.py`**: ツールの定義

#### `tests/` - テストコード（推奨）

テストコードは、実装コードとは別の`tests/`ディレクトリに配置することを推奨します。これにより、以下の利点が得られます：

- **明確な分離**: 実装コードとテストコードが明確に分離される
- **保守性**: テストコードの管理が容易になる
- **デプロイ時の除外**: 本番環境にテストコードを含めないようにできる

**注意**: テストコードを実装ファイルと同じファイルに記述することも可能ですが、以下の理由から推奨されません：
- ファイルサイズが大きくなり、可読性が低下する
- 本番環境にテストコードが含まれる可能性がある
- テストの実行と管理が困難になる

詳細は[Testing](./P24_test.md)のドキュメントを参照してください。

#### `requirements.txt` - 依存関係

アプリケーションの実行に必要なPythonパッケージを定義します。

```txt
langgraph>=0.1.0
langchain>=0.1.0
langchain-openai>=0.1.0
python-dotenv>=1.0.0
```

#### `.env` - 環境変数（オプション）

環境固有の設定（APIキーなど）を管理します。

```env
OPENAI_API_KEY=your-api-key-here
LANGCHAIN_API_KEY=your-langchain-api-key
```

#### `langgraph.json` - 設定ファイル

LangGraphアプリケーションの設定を定義します（後述）。

## 設定ファイル（langgraph.json）

`langgraph.json`は、LangGraphアプリケーションのデプロイに必要な情報を指定するJSONファイルです。

### 基本的な構造

```json
{
  "dependencies": ["langchain_openai", "./my_agent"],
  "graphs": {
    "my_agent": "./my_agent/agent.py:graph"
  },
  "env": "./.env"
}
```

### 設定項目の説明

#### `dependencies`

アプリケーションの実行に必要な依存関係を指定します。

- **外部パッケージ**: `"langchain_openai"`のように、PyPIからインストール可能なパッケージ名を指定
- **ローカルパッケージ**: `"./my_agent"`のように、相対パスでローカルパッケージを指定

```json
{
  "dependencies": [
    "langchain_openai",
    "langgraph",
    "./my_agent"
  ]
}
```

#### `graphs`

デプロイするグラフを指定します。複数のグラフを定義できます。

```json
{
  "graphs": {
    "my_agent": "./my_agent/agent.py:graph",
    "another_agent": "./my_agent/another.py:another_graph"
  }
}
```

各グラフは以下の形式で指定します：
- **形式**: `"<グラフ名>": "<ファイルパス>:<変数名>"`
- **例**: `"./my_agent/agent.py:graph"` → `agent.py`ファイルの`graph`変数

#### `env`

環境変数ファイルのパスを指定します（オプション）。

```json
{
  "env": "./.env"
}
```

本番環境では、通常はデプロイ環境で環境変数を設定します。

### 設定ファイルの例

#### 例1: シンプルな構成

```json
{
  "dependencies": ["langchain_openai", "./my_agent"],
  "graphs": {
    "my_agent": "./my_agent/agent.py:graph"
  },
  "env": "./.env"
}
```

#### 例2: 複数のグラフ

```json
{
  "dependencies": [
    "langchain_openai",
    "langchain-anthropic",
    "./my_agent"
  ],
  "graphs": {
    "chat_agent": "./my_agent/chat.py:chat_graph",
    "research_agent": "./my_agent/research.py:research_graph"
  },
  "env": "./.env"
}
```

#### 例3: 追加のバイナリやシステムライブラリが必要な場合

```json
{
  "dependencies": ["langchain_openai", "./my_agent"],
  "graphs": {
    "my_agent": "./my_agent/agent.py:graph"
  },
  "env": "./.env",
  "dockerfile_lines": [
    "RUN apt-get update && apt-get install -y curl"
  ]
}
```

## 依存関係の管理

### requirements.txt を使用する場合

`requirements.txt`を使用して依存関係を管理する場合：

```txt
langgraph>=0.1.0
langchain>=0.1.0
langchain-openai>=0.1.0
python-dotenv>=1.0.0
```

`langgraph.json`では、依存関係ファイルを指定する必要はありません（自動的に検出されます）。

### pyproject.toml を使用する場合

`pyproject.toml`を使用する場合も同様に、自動的に検出されます。

```toml
[project]
dependencies = [
    "langgraph>=0.1.0",
    "langchain>=0.1.0",
    "langchain-openai>=0.1.0",
    "python-dotenv>=1.0.0",
]
```

## グラフの定義

### グラフの定義方法

グラフは、Pythonファイルのモジュールレベルで変数として定義する必要があります。`langgraph.json`では、この変数を参照することでグラフを読み込みます。

#### 方法1: コンパイル済みグラフを変数として定義

```python
# my_agent/agent.py
from langgraph.graph import StateGraph, START, END
from my_agent.utils.state import MyState
from my_agent.utils.nodes import process_node

# グラフを構築
graph = StateGraph(MyState)
graph.add_node("process", process_node)
graph.add_edge(START, "process")
graph.add_edge("process", END)

# コンパイルしてモジュールレベルの変数に代入
# langgraph.jsonでは "./my_agent/agent.py:graph" として参照可能
graph = graph.compile()
```

**注意**: `graph = graph.compile()` は、コンパイル済みグラフを`graph`変数に代入しているだけです。この変数はモジュールレベルで定義されているため、`langgraph.json`から `"./my_agent/agent.py:graph"` のように参照できます。

#### 方法2: グラフ構築関数を使用

```python
# my_agent/agent.py
from langgraph.graph import StateGraph, START, END
from my_agent.utils.state import MyState
from my_agent.utils.nodes import process_node

def build_graph():
    """グラフを構築する関数"""
    graph = StateGraph(MyState)
    graph.add_node("process", process_node)
    graph.add_edge(START, "process")
    graph.add_edge("process", END)
    return graph.compile()

# 関数を呼び出してモジュールレベルの変数に代入
# langgraph.jsonでは "./my_agent/agent.py:graph" として参照可能
graph = build_graph()
```

### 複数のグラフを定義する場合

複数のグラフを定義する場合、それぞれを別のファイルに分けるか、同じファイル内で複数の変数として定義します。

```python
# my_agent/chat.py
from langgraph.graph import StateGraph, START, END
# ... グラフ構築コード ...
chat_graph = graph.compile()

# my_agent/research.py
from langgraph.graph import StateGraph, START, END
# ... グラフ構築コード ...
research_graph = graph.compile()
```

`langgraph.json`では：

```json
{
  "graphs": {
    "chat_agent": "./my_agent/chat.py:chat_graph",
    "research_agent": "./my_agent/research.py:research_graph"
  }
}
```

## 環境変数の管理

### ローカル開発環境

ローカル開発では、`.env`ファイルを使用して環境変数を管理します。

```env
# .env
OPENAI_API_KEY=sk-...
LANGCHAIN_API_KEY=ls-...
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=my-project
```

`langgraph.json`で指定：

```json
{
  "env": "./.env"
}
```

### 本番環境

本番環境では、通常はデプロイプラットフォーム（LangSmith Deploymentなど）で環境変数を設定します。

- **LangSmith Deployment**: ダッシュボードで環境変数を設定
- **その他のプラットフォーム**: 各プラットフォームの環境変数設定機能を使用

## ベストプラクティス

### 1. モジュール化された設計

グラフを小さな再利用可能なコンポーネントに分割します。

```
my_agent/
├── utils/
│   ├── state.py          # 状態定義
│   ├── nodes.py          # ノード関数
│   ├── tools.py          # ツール定義
│   └── edges.py          # エッジ定義（条件付きエッジなど）
├── graphs/
│   ├── chat.py           # チャットエージェント
│   └── research.py       # リサーチエージェント
└── agent.py              # メインエージェント（必要に応じて）
```

### 2. 一貫した命名規則

ファイル名とディレクトリ名は、その目的を明確に示すようにします。

- **ノード関数**: `process_node`, `analyze_node`など
- **ツール**: `search_tool`, `calculate_tool`など
- **状態**: `ChatState`, `ResearchState`など

### 3. 設定の分離

環境固有の設定は、環境変数や設定ファイルで管理します。

```python
# my_agent/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4")
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
```

### 4. エラーハンドリング

各ノードで適切なエラーハンドリングを実装します。

```python
# my_agent/utils/nodes.py
import logging

logger = logging.getLogger(__name__)

def process_node(state: MyState) -> dict:
    try:
        # 処理を実行
        result = perform_processing(state)
        return {"result": result}
    except Exception as e:
        logger.error(f"Error in process_node: {e}")
        return {"error": str(e)}
```

### 5. ログの実装

デバッグとモニタリングのために、適切なログを実装します。

```python
# my_agent/utils/nodes.py
import logging

logger = logging.getLogger(__name__)

def process_node(state: MyState) -> dict:
    logger.info(f"Processing state: {state}")
    result = perform_processing(state)
    logger.info(f"Processing complete: {result}")
    return {"result": result}
```

### 6. 型安全性

状態とノードの入出力に型ヒントを使用します。

```python
from typing import TypedDict, Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages

class MyState(TypedDict):
    messages: Annotated[list, add_messages]
    counter: int
    data: dict

def process_node(state: MyState) -> dict:
    # 型安全な処理
    ...
```

### 7. テストコードの分離

テストコードは実装コードとは別の`tests/`ディレクトリに配置します。

```
my-app/
├── my_agent/              # 実装コード
│   ├── agent.py
│   └── utils/
│       ├── nodes.py
│       └── tools.py
├── tests/                 # テストコード
│   ├── __init__.py
│   ├── conftest.py       # 共通フィクスチャ
│   ├── test_nodes.py    # ノードのユニットテスト
│   ├── test_tools.py     # ツールのユニットテスト
│   ├── test_graph.py     # グラフの統合テスト
│   └── test_integration.py  # エンドツーエンドテスト
└── pytest.ini            # pytest設定
```

**テストを別ファイルにしない場合の問題点**:

- **ファイルサイズ**: 実装ファイルが大きくなり、可読性が低下
- **本番環境への混入**: テストコードが本番環境に含まれる可能性
- **実行と管理**: テストの実行と管理が困難

**推奨される構造**:

- 実装コード: `my_agent/`ディレクトリ
- テストコード: `tests/`ディレクトリ
- テストは実装コードをインポートして使用

詳細は[Testing](./P24_test.md)のドキュメントを参照してください。

## 実装例

### 完全な例

以下は、完全なLangGraphアプリケーションの構造例です。

#### ディレクトリ構造

```
my-app/
├── my_agent/
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── state.py
│   │   ├── nodes.py
│   │   └── tools.py
│   ├── __init__.py
│   └── agent.py
├── .env
├── requirements.txt
└── langgraph.json
```

#### state.py

```python
# my_agent/utils/state.py
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    counter: int
```

#### nodes.py

```python
# my_agent/utils/nodes.py
from my_agent.utils.state import AgentState

def process_node(state: AgentState) -> dict:
    """処理ノード"""
    # 処理を実行
    return {"counter": state.get("counter", 0) + 1}
```

#### tools.py

```python
# my_agent/utils/tools.py
from langchain.tools import tool

@tool
def calculate(expression: str) -> str:
    """数式を計算するツール"""
    try:
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Error: {e}"
```

#### agent.py

```python
# my_agent/agent.py
from langgraph.graph import StateGraph, START, END
from my_agent.utils.state import AgentState
from my_agent.utils.nodes import process_node
from my_agent.utils.tools import calculate

# グラフを構築
graph = StateGraph(AgentState)
graph.add_node("process", process_node)
graph.add_edge(START, "process")
graph.add_edge("process", END)

# コンパイルしてエクスポート
graph = graph.compile()
```

#### langgraph.json

```json
{
  "dependencies": ["langchain_openai", "./my_agent"],
  "graphs": {
    "my_agent": "./my_agent/agent.py:graph"
  },
  "env": "./.env"
}
```

#### requirements.txt

```txt
langgraph>=0.1.0
langchain>=0.1.0
langchain-openai>=0.1.0
python-dotenv>=1.0.0
```

## LangSmith Deployment へのデプロイ

LangSmith Deploymentを使用してアプリケーションをデプロイする場合：

1. **リポジトリの準備**: 上記の構造でコードを準備
2. **設定ファイルの確認**: `langgraph.json`が正しく設定されているか確認
3. **デプロイ**: LangSmith CLIまたはダッシュボードからデプロイ

詳細は[Deploy](./P27_deploy.md)のドキュメントを参照してください。

## まとめ

適切なアプリケーション構造を持つことで：

- ✅ **保守性**: コードが整理され、理解しやすくなる
- ✅ **スケーラビリティ**: 機能追加や変更が容易になる
- ✅ **デプロイの容易さ**: LangSmith Deploymentへの展開が簡単になる
- ✅ **チーム開発**: 複数の開発者が協力しやすくなる

この構造に従うことで、実用的で保守性の高いLangGraphアプリケーションを構築できます。

## 参考資料

- [公式ドキュメント: Application Structure](https://docs.langchain.com/oss/python/langgraph/application-structure)
- [LangGraph Configuration File Reference](https://docs.langchain.com/langsmith/cli#configuration-file)
- [LangSmith Deployment](https://docs.langchain.com/langsmith/deployments)
