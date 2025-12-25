# Tasks（タスク）

このドキュメントでは、LangGraphにおける**Tasks（タスク）**について解説します。Tasksは、耐久性のある実行（Durable Execution）において、非決定的な操作や副作用を持つ操作をラップするための重要な機能です。

公式ドキュメント: https://docs.langchain.com/oss/python/langgraph/durable-execution

## 概要

**Tasks（タスク）**は、LangGraphでワークフローを再開可能にするために、非決定的な操作や副作用を持つ操作をラップするための仕組みです。

- **非決定的な操作**: ランダム数生成など、実行ごとに結果が変わる可能性がある操作
- **副作用を持つ操作**: ファイル書き込み、API呼び出しなど、外部に影響を与える操作

これらの操作をタスクとしてラップすることで、ワークフローが中断された後に再開する際、同じ操作が繰り返されず、永続化レイヤーから結果が取得されます。

## なぜタスクが必要か？

### ワークフローの再開の仕組み

ワークフローを再開する際、コードは**停止した行から再開されるわけではありません**。代わりに、適切な**開始ポイント**から再開され、停止したポイントまで全てのステップが再実行されます。

つまり、ワークフローは**開始ポイントから停止ポイントまで再現（replay）**されます。

### タスクなしの場合の問題

タスクを使用しない場合、以下のような問題が発生します：

1. **副作用の重複実行**: API呼び出しが再実行され、同じリクエストが複数回送信される
2. **非決定的な結果**: ランダム数生成が再実行され、以前とは異なる結果になる
3. **一貫性の欠如**: 再開時に以前の実行とは異なる動作になる

### タスクを使用することで解決されること

タスクを使用することで、以下のことが保証されます：

1. **操作の一意性**: 同じタスクは同じ実行内で一度だけ実行される
2. **結果の再利用**: 再開時には、永続化レイヤーから以前の結果が取得される
3. **一貫性の保証**: 再開時も以前の実行と同じ結果が得られる

## 要件

耐久性のある実行を活用するには、以下が必要です：

1. **永続化の有効化**: チェックポインタを指定してワークフローの進捗を保存
2. **スレッド識別子の指定**: ワークフロー実行時にスレッドIDを指定して実行履歴を追跡
3. **タスクの使用**: 非決定的な操作や副作用を持つ操作をタスクでラップ

## タスクの使用ガイドライン

### 1. 作業の重複を避ける

ノードに複数の副作用を持つ操作（ログ出力、ファイル書き込み、ネットワーク呼び出しなど）が含まれている場合、各操作を**個別のタスク**としてラップします。

これにより、ワークフローが再開された際、操作が繰り返されず、永続化レイヤーから結果が取得されます。

### 2. 非決定的な操作をカプセル化

非決定的な結果を生成する可能性のあるコード（例：ランダム数生成）を**タスク**または**ノード**内にラップします。

これにより、再開時に、ワークフローは記録されたステップの正確なシーケンスを同じ結果で再現します。

### 3. べき等性のある操作を使用

可能な限り、副作用（API呼び出し、ファイル書き込みなど）を**べき等性**のある操作にします。べき等性とは、操作を再試行しても最初に実行した場合と同じ効果が得られることを意味します。

これは、データ書き込みを伴う操作において特に重要です。タスクが開始されたが正常に完了しなかった場合、ワークフローの再開時にタスクが再実行されます。記録された結果に依存して一貫性を維持するため、べき等性キーを使用するか、既存の結果を検証して、意図しない重複を避けます。

## ノード内でのタスクの使用

ノードに複数の操作が含まれている場合、各操作を個別のノードにリファクタリングするよりも、各操作を**タスク**に変換する方が簡単な場合があります。

### 例: タスクなしの実装

```python
from typing import NotRequired
from typing_extensions import TypedDict
import uuid
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, START, END
import requests

# 状態の定義
class State(TypedDict):
    url: str
    result: NotRequired[str]

def call_api(state: State):
    """APIリクエストを行うノードの例"""
    result = requests.get(state['url']).text[:100]  # 副作用
    return {
        "result": result
    }

# グラフの構築
builder = StateGraph(State)
builder.add_node("call_api", call_api)
builder.add_edge(START, "call_api")
builder.add_edge("call_api", END)

# チェックポインタの指定
checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)

# スレッドIDを含む設定を定義
thread_id = uuid.uuid4()
config = {"configurable": {"thread_id": thread_id}}

# グラフの実行
graph.invoke({"url": "https://www.example.com"}, config)
```

### 例: タスクを使用した実装

```python
from typing import NotRequired
from typing_extensions import TypedDict
import uuid
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.func import task
from langgraph.graph import StateGraph, START, END
import requests

# 状態の定義
class State(TypedDict):
    urls: list[str]
    result: NotRequired[list[str]]

@task
def _make_request(url: str):
    """リクエストを行うタスク"""
    return requests.get(url).text[:100]

def call_api(state: State):
    """APIリクエストを行うノードの例"""
    requests = [_make_request(url) for url in state['urls']]
    results = [request.result() for request in requests]
    return {
        "results": results
    }

# グラフの構築
builder = StateGraph(State)
builder.add_node("call_api", call_api)
builder.add_edge(START, "call_api")
builder.add_edge("call_api", END)

# チェックポインタの指定
checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)

# スレッドIDを含む設定を定義
thread_id = uuid.uuid4()
config = {"configurable": {"thread_id": thread_id}}

# グラフの実行
graph.invoke({"urls": ["https://www.example.com"]}, config)
```

### タスクを使用する利点

1. **再実行の防止**: ワークフローが再開されても、タスクは再実行されず、永続化レイヤーから結果が取得される
2. **一貫性の保証**: 同じ実行内で同じタスクは同じ結果を返す
3. **柔軟性**: ノード内の複数の操作を個別のタスクとして管理できる

## タスクの使用例

### 複数のAPI呼び出しをタスクで管理

```python
from langgraph.func import task
from typing import TypedDict, NotRequired

class State(TypedDict):
    urls: list[str]
    results: NotRequired[list[str]]

@task
def fetch_url(url: str) -> str:
    """URLを取得するタスク"""
    import requests
    response = requests.get(url)
    return response.text[:100]

def process_urls(state: State) -> dict:
    """複数のURLを処理するノード"""
    # 各URLに対してタスクを作成
    tasks = [fetch_url(url) for url in state['urls']]
    # タスクの結果を取得
    results = [task.result() for task in tasks]
    return {"results": results}
```

### ファイル操作をタスクで管理

```python
from langgraph.func import task
from typing import TypedDict, NotRequired

class State(TypedDict):
    file_path: str
    content: NotRequired[str]

@task
def read_file(file_path: str) -> str:
    """ファイルを読み込むタスク"""
    with open(file_path, 'r') as f:
        return f.read()

def process_file(state: State) -> dict:
    """ファイルを処理するノード"""
    content = read_file(state['file_path']).result()
    return {"content": content}
```

## ベストプラクティス

### 1. タスクの粒度

- **細かすぎる**: 単純な計算など、副作用のない操作をタスクにする必要はない
- **粗すぎる**: 複数の副作用を持つ操作を1つのタスクにまとめない
- **適切**: 各副作用を持つ操作を個別のタスクとして定義

### 2. べき等性の確保

タスク内で行う操作は、可能な限りべき等性を確保します：

```python
@task
def create_resource(name: str, idempotency_key: str):
    """べき等性のあるリソース作成"""
    # 既存のリソースをチェック
    existing = check_existing_resource(idempotency_key)
    if existing:
        return existing
    
    # 新規作成
    return create_new_resource(name, idempotency_key)
```

### 3. エラーハンドリング

タスク内で適切にエラーを処理します：

```python
@task
def safe_api_call(url: str):
    """安全なAPI呼び出し"""
    try:
        response = requests.get(url, timeout=10)
        return response.text
    except requests.RequestException as e:
        # エラーを記録して再試行可能にする
        raise TaskError(f"API呼び出しに失敗: {e}")
```

## まとめ

Tasks（タスク）は、LangGraphで耐久性のある実行を実現するための重要な機能です：

1. **非決定的な操作のカプセル化**: ランダム数生成などの非決定的な操作をタスクでラップ
2. **副作用の管理**: ファイル書き込み、API呼び出しなどの副作用を持つ操作をタスクで管理
3. **再実行の防止**: ワークフロー再開時に、タスクは再実行されず、永続化レイヤーから結果が取得される
4. **一貫性の保証**: 同じ実行内で同じタスクは同じ結果を返す

適切にタスクを使用することで、堅牢で信頼性の高いワークフローを構築できます。

## 関連ドキュメント

- [P21: Durable Execution](./P21_durable_execution.md): 耐久性のある実行の詳細
- [P16: Persistence](./P16_persistence.md): 状態の永続化の詳細
- [Functional API - Tasks](https://docs.langchain.com/oss/python/langgraph/functional-api#task): Functional APIでのタスクの使用
- [Common Pitfalls](https://docs.langchain.com/oss/python/langgraph/functional-api#common-pitfalls): よくある落とし穴と回避方法
- [P00: Roadmap](./P00_roadmap.md): 学習ロードマップに戻る

