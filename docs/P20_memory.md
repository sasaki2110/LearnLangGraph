# Memory

このドキュメントでは、LangGraphにおけるメモリ管理について解説します。

公式ドキュメント: https://docs.langchain.com/oss/python/langgraph/add-memory

## 概要

メモリ（Memory）は、エージェントが**過去の情報を保持し、活用する**ための機能です。LangGraphでは、以下の2種類のメモリを管理できます：

1. **短期メモリ**: 現在の実行セッション内での情報
2. **長期メモリ**: 複数のセッションにわたって保持される情報

## メモリの種類

### 短期メモリ（Short-term Memory）

短期メモリは、**現在の実行セッション内**でのみ有効な情報です。

- グラフの状態として管理される
- 実行が終了すると消える
- 会話履歴、中間結果など

### 長期メモリ（Long-term Memory）

長期メモリは、**複数のセッションにわたって保持**される情報です。

- データベースやストレージに保存される
- 永続化と組み合わせて使用
- ユーザー設定、学習した知識など

## 短期メモリの追加

短期メモリ（スレッドレベルの永続化）により、エージェントはマルチターン会話を追跡できます。短期メモリを追加するには、チェックポインタ（checkpointer）を使用します。

### 基本的な使用方法

`InMemorySaver`を使用して、メモリ内に短期メモリを保存します：

```python
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph

# メモリ内チェックポインタの初期化
checkpointer = InMemorySaver()

# グラフの構築
builder = StateGraph(...)
graph = builder.compile(checkpointer=checkpointer)

# グラフの実行（thread_idで会話スレッドを識別）
graph.invoke(
    {"messages": [{"role": "user", "content": "hi! I am Bob"}]},
    {"configurable": {"thread_id": "1"}},  # 会話スレッドの一意識別子
)
```

この設定により、`InMemorySaver`が会話状態をメモリに保存し、エージェントが会話全体を通じてコンテキストを維持できます。

### 本番環境での使用

本番環境では、データベースにバックアップされたチェックポインタを使用します：

```python
from langgraph.checkpoint.postgres import PostgresSaver

DB_URI = "postgresql://postgres:postgres@localhost:5442/postgres?sslmode=disable"

with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
    builder = StateGraph(...)
    graph = builder.compile(checkpointer=checkpointer)
```

**利用可能なチェックポインタ：**
- `PostgresSaver`: PostgreSQLデータベース
- `MongoDBSaver`: MongoDB（[langgraph-checkpoint-mongodb](https://pypi.org/project/langgraph-checkpoint-mongodb/)）
- `RedisSaver`: Redis

### サブグラフでの使用

グラフに[サブグラフ](./P19_subgraphs.md)が含まれている場合、親グラフをコンパイルする際にチェックポインタを提供するだけで十分です。LangGraphは自動的にチェックポインタを子サブグラフに伝播します。

```python
from langgraph.graph import START, StateGraph
from langgraph.checkpoint.memory import InMemorySaver
from typing import TypedDict

class State(TypedDict):
    foo: str

# サブグラフ
def subgraph_node_1(state: State):
    return {"foo": state["foo"] + "bar"}

subgraph_builder = StateGraph(State)
subgraph_builder.add_node(subgraph_node_1)
subgraph_builder.add_edge(START, "subgraph_node_1")
subgraph = subgraph_builder.compile()

# 親グラフ
builder = StateGraph(State)
builder.add_node("node_1", subgraph)
builder.add_edge(START, "node_1")

checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)
```

サブグラフに独自のメモリを持たせたい場合は、サブグラフを適切なチェックポインタオプションでコンパイルします。これは、[マルチエージェント](./P14_workflows_agents.md)システムで、エージェントが内部メッセージ履歴を追跡したい場合に有用です。

```python
subgraph_builder = StateGraph(...)
subgraph = subgraph_builder.compile(checkpointer=True)
```

## 長期メモリの追加

長期メモリを使用して、会話をまたいでユーザー固有またはアプリケーションレベルのデータを保存します。

### 基本的な使用方法

```python
from langgraph.store.memory import InMemoryStore
from langgraph.graph import StateGraph

store = InMemoryStore()
builder = StateGraph(...)
graph = builder.compile(store=store)
```

### 本番環境での使用

本番環境では、データベースにバックアップされたストアを使用します：

```python
from langgraph.store.postgres import PostgresStore

DB_URI = "postgresql://postgres:postgres@localhost:5442/postgres?sslmode=disable"

with PostgresStore.from_conn_string(DB_URI) as store:
    builder = StateGraph(...)
    graph = builder.compile(store=store)
```

**利用可能なストア：**
- `PostgresStore`: PostgreSQLデータベース
- `RedisStore`: Redis

### セマンティック検索の使用

グラフのメモリストアでセマンティック検索を有効にすると、グラフエージェントがストア内のアイテムを意味的類似性で検索できるようになります。

```python
from langchain.embeddings import init_embeddings
from langgraph.store.memory import InMemoryStore

# 埋め込みモデルの初期化
embeddings = init_embeddings("openai:text-embedding-3-small")

# セマンティック検索を有効にしたメモリストアの作成
store = InMemoryStore(
    index={
        "embed": embeddings,
        "dims": 1536,
    }
)

# ユーザーメモリの保存
store.put(("user_123", "memories"), "1", {"text": "I love pizza"})
store.put(("user_123", "memories"), "2", {"text": "I am a plumber"})

# クエリに意味的に関連するメモリを検索
items = store.search(
    ("user_123", "memories"), query="I'm hungry", limit=1
)
```

この例では、エージェントは「I'm hungry」というクエリに対して、正確なフレーズが一致しなくても、意味的に関連するユーザーメモリ（「I love pizza」）を取得できます。

## 短期メモリの管理

[短期メモリ](#短期メモリの追加)を有効にすると、長い会話がLLMのコンテキストウィンドウを超える可能性があります。一般的な解決策は以下の通りです：

1. **メッセージのトリミング**: LLM呼び出し前に最初または最後のN件のメッセージを削除
2. **メッセージの削除**: LangGraphの状態からメッセージを永続的に削除
3. **メッセージの要約**: 履歴の以前のメッセージを要約し、要約で置き換える
4. **チェックポイントの管理**: メッセージ履歴の保存と取得
5. カスタム戦略（メッセージフィルタリングなど）

これにより、エージェントはLLMのコンテキストウィンドウを超えることなく、会話を追跡できます。

### メッセージのトリミング

ほとんどのLLMには、サポートされる最大コンテキストウィンドウ（トークン単位）があります。メッセージ履歴を切り詰める方法の1つは、メッセージ履歴のトークンをカウントし、その制限に近づいたら切り詰めることです。LangChainを使用している場合、`trim_messages`ユーティリティを使用して、リストから保持するトークン数と、境界を処理するための`strategy`（例：最後の`max_tokens`を保持）を指定できます。

メッセージ履歴をトリミングするには、`trim_messages`関数を使用します：

```python
from langchain_core.messages.utils import (
    trim_messages,
    count_tokens_approximately
)

def call_model(state: MessagesState):
    messages = trim_messages(
        state["messages"],
        strategy="last",
        token_counter=count_tokens_approximately,
        max_tokens=128,
        start_on="human",
        end_on=("human", "tool"),
    )
    response = model.invoke(messages)
    return {"messages": [response]}

builder = StateGraph(MessagesState)
builder.add_node(call_model)
...
```

### メッセージの削除

グラフの状態からメッセージを削除して、メッセージ履歴を管理できます。これは、特定のメッセージを削除するか、メッセージ履歴全体をクリアしたい場合に有用です。

特定のメッセージを削除するには、`RemoveMessage`を使用します。`RemoveMessage`を機能させるには、`add_messages`[リデューサー](./P13_thinking_in_langgraph.md#reducers)を持つ状態キー（例：[MessagesState](./P13_thinking_in_langgraph.md#messagesstate)）を使用する必要があります。

```python
from langchain.messages import RemoveMessage

def delete_messages(state):
    messages = state["messages"]
    if len(messages) > 2:
        # 最初の2つのメッセージを削除
        return {"messages": [RemoveMessage(id=m.id) for m in messages[:2]]}
```

すべてのメッセージを削除するには：

```python
from langgraph.graph.message import REMOVE_ALL_MESSAGES

def delete_messages(state):
    return {"messages": [RemoveMessage(id=REMOVE_ALL_MESSAGES)]}
```

**警告**: メッセージを削除する際は、結果のメッセージ履歴が有効であることを確認してください。使用しているLLMプロバイダーの制限を確認してください。例えば：
- 一部のプロバイダーは、メッセージ履歴が`user`メッセージで始まることを期待します
- ほとんどのプロバイダーは、ツール呼び出しを含む`assistant`メッセージの後に、対応する`tool`結果メッセージが続くことを要求します

### メッセージの要約

上記のようにメッセージをトリミングまたは削除すると、メッセージキューから情報が失われる可能性があります。このため、一部のアプリケーションでは、チャットモデルを使用してメッセージ履歴を要約する、より洗練されたアプローチが有益です。

プロンプトとオーケストレーションロジックを使用してメッセージ履歴を要約できます。例えば、LangGraphでは、[MessagesState](./P13_thinking_in_langgraph.md#messagesstate)を拡張して`summary`キーを含めることができます：

```python
from langgraph.graph import MessagesState

class State(MessagesState):
    summary: str
```

次に、チャット履歴の要約を生成し、既存の要約を次の要約のコンテキストとして使用できます。この`summarize_conversation`ノードは、`messages`状態キーにメッセージが蓄積された後に呼び出すことができます。

```python
def summarize_conversation(state: State):
    # 既存の要約を取得
    summary = state.get("summary", "")
    
    # 要約プロンプトの作成
    if summary:
        # 既に要約が存在する
        summary_message = (
            f"This is a summary of the conversation to date: {summary}\n\n"
            "Extend the summary by taking into account the new messages above:"
        )
    else:
        summary_message = "Create a summary of the conversation above:"
    
    # プロンプトを履歴に追加
    messages = state["messages"] + [HumanMessage(content=summary_message)]
    response = model.invoke(messages)
    
    # 最新の2件以外のすべてのメッセージを削除
    delete_messages = [RemoveMessage(id=m.id) for m in state["messages"][:-2]]
    
    return {"summary": response.content, "messages": delete_messages}
```

### チェックポイントの管理

チェックポインタによって保存された情報を表示および削除できます。

#### スレッド状態の表示

```python
config = {
    "configurable": {
        "thread_id": "1",
        # オプションで特定のチェックポイントのIDを提供
        # それ以外の場合は最新のチェックポイントが表示される
        # "checkpoint_id": "1f029ca3-1f5b-6704-8004-820c16b69a5a"
    }
}
graph.get_state(config)
```

#### スレッドの履歴を表示

```python
config = {
    "configurable": {
        "thread_id": "1"
    }
}
list(graph.get_state_history(config))
```

#### スレッドのすべてのチェックポイントを削除

```python
thread_id = "1"
checkpointer.delete_thread(thread_id)
```

## Prebuilt memory tools

**LangMem**は、エージェントで長期メモリを管理するためのツールを提供する、LangChainがメンテナンスしているライブラリです。使用例については、[LangMemドキュメント](https://langchain-ai.github.io/langmem/)を参照してください。

## Database management

データベースにバックアップされた永続化実装（PostgresやRedisなど）を使用して短期メモリや長期メモリを保存する場合、データベースで使用する前に、必要なスキーマを設定するためにマイグレーションを実行する必要があります。

慣例として、ほとんどのデータベース固有のライブラリは、チェックポインタまたはストアインスタンスに`setup()`メソッドを定義して、必要なマイグレーションを実行します。ただし、[BaseCheckpointSaver](https://reference.langchain.com/python/langgraph/checkpoints/#langgraph.checkpoint.base.BaseCheckpointSaver)または[BaseStore](https://reference.langchain.com/python/langgraph/store/#langgraph.store.base.BaseStore)の特定の実装を確認して、正確なメソッド名と使用方法を確認してください。

マイグレーションは専用のデプロイステップとして実行することを推奨します。または、サーバー起動の一部として実行されることを確認してください。

## 実装例

### 例1: 基本的な会話履歴の管理（短期メモリ）

```python
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langchain.messages import HumanMessage, AIMessage
from typing import Annotated
from typing_extensions import TypedDict
from operator import add

class ConversationState(TypedDict):
    messages: Annotated[list, add]

def llm_call(state: ConversationState) -> dict:
    """LLM呼び出し（会話履歴を使用）"""
    response = model.invoke(state["messages"])
    return {"messages": [response]}

# グラフの構築
graph = StateGraph(ConversationState)
graph.add_node("llm_call", llm_call)
graph.add_edge(START, "llm_call")
graph.add_edge("llm_call", END)

# チェックポインタを設定
checkpointer = InMemorySaver()
agent = graph.compile(checkpointer=checkpointer)

# 実行（会話履歴が保持される）
config = {"configurable": {"thread_id": "1"}}

result1 = agent.invoke(
    {"messages": [HumanMessage(content="hi! I am Bob")]},
    config=config
)

result2 = agent.invoke(
    {"messages": [HumanMessage(content="what's my name?")]},
    config=config
)
# 前の会話履歴が含まれているため、「Bob」と答えることができる
```

### 例2: 長期メモリとセマンティック検索

```python
from langgraph.store.memory import InMemoryStore
from langchain.embeddings import init_embeddings
from langgraph.graph import StateGraph

# セマンティック検索を有効にしたストアの作成
embeddings = init_embeddings("openai:text-embedding-3-small")
store = InMemoryStore(
    index={
        "embed": embeddings,
        "dims": 1536,
    }
)

# ユーザーメモリの保存
store.put(("user_123", "memories"), "1", {"text": "I love pizza"})
store.put(("user_123", "memories"), "2", {"text": "I am a plumber"})

# グラフの構築
builder = StateGraph(...)
graph = builder.compile(store=store)

# セマンティック検索の実行
items = store.search(
    ("user_123", "memories"), query="I'm hungry", limit=1
)
# 「I'm hungry」に関連して「I love pizza」が返される
```

### 例3: メッセージのトリミングと要約

```python
from langchain_core.messages.utils import (
    trim_messages,
    count_tokens_approximately
)
from langchain.messages import RemoveMessage, HumanMessage
from langgraph.graph import MessagesState

class State(MessagesState):
    summary: str

def call_model(state: State):
    # メッセージをトリミング
    messages = trim_messages(
        state["messages"],
        strategy="last",
        token_counter=count_tokens_approximately,
        max_tokens=128,
        start_on="human",
        end_on=("human", "tool"),
    )
    response = model.invoke(messages)
    return {"messages": [response]}

def summarize_conversation(state: State):
    summary = state.get("summary", "")
    
    if summary:
        summary_message = (
            f"This is a summary of the conversation to date: {summary}\n\n"
            "Extend the summary by taking into account the new messages above:"
        )
    else:
        summary_message = "Create a summary of the conversation above:"
    
    messages = state["messages"] + [HumanMessage(content=summary_message)]
    response = model.invoke(messages)
    
    # 最新の2件以外のすべてのメッセージを削除
    delete_messages = [RemoveMessage(id=m.id) for m in state["messages"][:-2]]
    
    return {"summary": response.content, "messages": delete_messages}
```

## ベストプラクティス

### 1. メモリの適切なサイズ管理

メモリが大きくなりすぎないように、適切に管理します。`trim_messages`を使用して、トークン数に基づいてメッセージを管理することを推奨します。

```python
from langchain_core.messages.utils import (
    trim_messages,
    count_tokens_approximately
)

# 会話履歴の最大トークン数を設定
MAX_TOKENS = 4000

def call_model_with_trimming(state: MessagesState) -> dict:
    """メッセージをトリミングしてからLLMを呼び出す"""
    messages = trim_messages(
        state["messages"],
        strategy="last",
        token_counter=count_tokens_approximately,
        max_tokens=MAX_TOKENS,
        start_on="human",
        end_on=("human", "tool"),
    )
    response = model.invoke(messages)
    return {"messages": [response]}
```

### 2. 関連情報のグループ化

関連する情報をグループ化して管理します。

```python
from typing import Annotated
from typing_extensions import TypedDict
from operator import add

class OrganizedMemoryState(TypedDict):
    messages: Annotated[list, add]
    user_profile: dict  # ユーザープロフィール
    conversation_context: dict  # 会話コンテキスト
    task_history: list  # タスク履歴
```

### 3. メッセージ履歴の検証

メッセージを削除する際は、結果のメッセージ履歴が有効であることを確認してください。LLMプロバイダーの制限を考慮してください：

- 一部のプロバイダーは、メッセージ履歴が`user`メッセージで始まることを期待します
- ほとんどのプロバイダーは、ツール呼び出しを含む`assistant`メッセージの後に、対応する`tool`結果メッセージが続くことを要求します

```python
def validate_message_history(messages):
    """メッセージ履歴の検証"""
    if not messages:
        return False
    
    # 最初のメッセージがuserメッセージであることを確認
    if messages[0].type != "human":
        return False
    
    # ツール呼び出しの整合性を確認
    for i, msg in enumerate(messages):
        if msg.type == "ai" and hasattr(msg, "tool_calls"):
            # 次のメッセージがtool結果であることを確認
            if i + 1 >= len(messages) or messages[i + 1].type != "tool":
                return False
    
    return True
```

### 4. 本番環境でのチェックポインタとストアの選択

- **開発・テスト**: `InMemorySaver`と`InMemoryStore`を使用
- **小規模アプリケーション**: `SqliteSaver`を使用
- **本番環境**: `PostgresSaver`と`PostgresStore`を使用
- **高パフォーマンスが必要な場合**: `RedisSaver`と`RedisStore`を検討

### 5. セマンティック検索の活用

長期メモリでセマンティック検索を有効にすると、正確なキーワードマッチングではなく、意味的に関連する情報を検索できます。これは、ユーザーの好みや過去の会話を検索する際に特に有用です。

## まとめ

メモリ管理により、以下のことが可能になります：

1. **短期メモリ（スレッドレベルの永続化）**: チェックポインタを使用して、マルチターン会話を追跡できる
2. **長期メモリ（クロススレッド永続化）**: ストアを使用して、会話をまたいでユーザー固有またはアプリケーションレベルのデータを保存できる
3. **セマンティック検索**: 意味的に関連する情報を検索できる
4. **メッセージ管理**: トリミング、削除、要約により、LLMのコンテキストウィンドウを効率的に使用できる
5. **チェックポイント管理**: スレッド状態の表示、履歴の確認、削除が可能

適切にメモリを管理することで、より賢く、パーソナライズされたエージェントを構築できます。本番環境では、データベースにバックアップされたチェックポインタとストアを使用し、必要に応じてセマンティック検索を有効にしてください。

## 次のステップ

- [P21: Durable Execution](./P21_durable_execution.md): 長時間実行の管理
- [P16: Persistence](./P16_persistence.md): 状態の永続化
- [P00: Roadmap](./P00_roadmap.md): 学習ロードマップに戻る

---

公式ドキュメントとプロジェクト内のドキュメントを比較し、違いを整理します。


[3 tools called]


公式ドキュメントの詳細を確認中です。


[2 tools called]


両ドキュメントの違いを整理します。


[2 tools called]


## Persistence（P16_persistence.md）と Memory（P20_memory.md）の違い

### 1. 焦点の違い

**Persistence（永続化）**
- 技術的な仕組みに焦点
- チェックポインタの動作原理
- 状態の保存・取得・更新の仕組み
- スレッドとチェックポイントの概念

**Memory（メモリ）**
- 実用的な使い方に焦点
- メモリの追加方法
- メッセージ管理（トリミング、削除、要約）
- セマンティック検索の活用

### 2. 内容の違い

| 項目 | Persistence | Memory |
|------|------------|--------|
| **チェックポインタの説明** | ✅ 詳細（仕組み、実装、API） | ✅ 簡潔（使用方法のみ） |
| **ストア（Store）の説明** | ✅ 簡潔（基本的な説明のみ） | ✅ 詳細（セマンティック検索含む） |
| **状態の取得・更新** | ✅ 詳細（`get_state`, `update_state`, `delete_state`） | ❌ なし |
| **チェックポイントの管理** | ✅ 詳細（履歴、フォークなど） | ✅ 簡潔（表示・削除のみ） |
| **メッセージ管理** | ❌ なし | ✅ 詳細（トリミング、削除、要約） |
| **セマンティック検索** | ✅ 簡潔 | ✅ 詳細（実装例含む） |
| **実装例** | ✅ 技術的な例 | ✅ 実用的な例 |

### 3. 対象読者

**Persistence**
- 永続化の仕組みを理解したい
- カスタムチェックポインタを作成したい
- 状態管理の詳細を知りたい

**Memory**
- メモリ機能を実装したい
- 会話履歴を管理したい
- セマンティック検索を使いたい

### 4. 重複している部分

両方のドキュメントで説明されている内容：
- チェックポインタの基本的な使用方法（`InMemorySaver`, `PostgresSaver`など）
- ストアの基本的な使用方法（`InMemoryStore`, `PostgresStore`など）
- セマンティック検索の基本的な説明

### 5. 補完関係

- Persistence: 「どのように動作するか」を説明
- Memory: 「どのように使うか」を説明

### まとめ

- Persistence: 永続化の技術的な仕組みとAPI
- Memory: メモリ機能の実用的な使い方とベストプラクティス

両方を読むことで、仕組みと使い方の両方を理解できます。

---

## メモリ機能と永続化の違い

### 概念的な違い

**永続化（Persistence）**
- **技術的な仕組み**：グラフの状態を保存するためのインフラストラクチャ
- **目的**：状態の保存・復元、タイムトラベル、中断後の再開など
- **実装**：チェックポインタ（checkpointer）を使用
- **保存対象**：グラフの状態（State）のスナップショット（チェックポイント）

**メモリ機能（Memory）**
- **機能・目的**：エージェントが過去の情報を保持し、活用するための機能
- **実装方法**：
  - **短期メモリ**：永続化（チェックポインタ）を使用
  - **長期メモリ**：ストア（store）を使用
- **保存対象**：会話履歴、ユーザー設定、学習した知識など

### 関係性

```
永続化（Persistence）
├─ チェックポインタ（Checkpointer）
│  └─ 短期メモリの実装に使用
│     └─ グラフの状態をスレッド単位で保存
│
└─ ストア（Store）
   └─ 長期メモリの実装に使用
      └─ ユーザー固有データをスレッド間で共有
```

### 具体的な違い

| 観点 | 永続化（Persistence） | メモリ機能（Memory） |
|------|---------------------|---------------------|
| **レベル** | 技術的な基盤 | 機能・目的 |
| **主な実装** | チェックポインタ | チェックポインタ + ストア |
| **保存内容** | グラフの状態全体 | 会話履歴、ユーザーデータなど |
| **スコープ** | スレッド単位 | スレッド単位（短期） + クロススレッド（長期） |
| **主な用途** | 状態の復元、タイムトラベル、中断再開 | 会話の継続、パーソナライゼーション |
| **管理方法** | `get_state()`, `update_state()`, `delete_state()` | メッセージのトリミング、要約、削除 |

### 例：会話ボットでの使用

**永続化の役割**
```python
# グラフの状態を保存・復元
checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)

# 状態の取得
state = graph.get_state({"configurable": {"thread_id": "1"}})

# 状態の更新
graph.update_state(config, {"messages": [new_message]})
```

**メモリ機能の役割**
```python
# 短期メモリ：会話履歴の保持（永続化を使用）
checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)
# → 同じthread_idで複数回呼び出すと、会話履歴が保持される

# 長期メモリ：ユーザー設定の保存（ストアを使用）
store = InMemoryStore()
graph = builder.compile(store=store)
# → スレッドをまたいでユーザーの好みを保存・検索できる
```

### まとめ

- **永続化**は「状態を保存する技術的な仕組み」
- **メモリ機能**は「過去の情報を活用するための機能」
- **短期メモリ**は永続化（チェックポインタ）を利用して実現
- **長期メモリ**はストア（store）を使用して実現

永続化はメモリ機能を実現するための技術の一つであり、メモリ機能は永続化を活用した具体的な機能です。

---

ここから gemini の解説

---

LangGraphにおける「短期メモリ」と「長期メモリ」の違いは、一言で言うと**「その情報は『この会話（スレッド）』の中だけのものか、それとも『他の会話』でも使い回すものか」**というスコープ（範囲）の違いです。

Cursorの説明にあった内容を、さらに噛み砕いて図解と対比表で解説します。

---

### メモリの構造イメージ

### 1. 短期メモリ（Short-term Memory）

**キーワード：チェックポインタ、スレッド内、自動保存**

* **役割:** 「さっき言ったことを覚えている」状態を作ることです。
* **仕組み:** `checkpointer`（チェックポインタ）を使います。
* **単位:** `thread_id`（スレッドID）ごとに保存されます。
* **具体例:** * ユーザー「私の名前はボブです」
* エージェント「こんにちはボブさん！」
* ユーザー「私の名前は何？」
* エージェント「ボブさんですよ」
* ※この「ボブ」という記憶は、このチャット画面（スレッド）を閉じたり、別のスレッド（ID:2）に切り替えたりすると、基本的には参照されません。



### 2. 長期メモリ（Long-term Memory）

**キーワード：ストア(Store)、クロススレッド、手動保存**

* **役割:** 「別の会話や、数日前の会話で得た知識」を全スレッド共通で使い回すことです。
* **仕組み:** `store`（ストア）を使います。
* **単位:** ユーザーIDなど、スレッドを超えた識別子で管理します。
* **具体例:**
* **会話1（スレッドA）:** ユーザー「私はピザが好きです」→ **Storeに保存**
* **会話2（スレッドB）:** （翌日、別のスレッドで）ユーザー「何かおすすめの料理ある？」
* エージェント「（Storeを検索して）ピザがお好きでしたよね、イタリアンはどうですか？」
* ※スレッドが変わっても、そのユーザーに関する「知識」として引き継がれます。



---

### 違いの比較表

| 項目 | 短期メモリ（永続化） | 長期メモリ（ストア） |
| --- | --- | --- |
| **主な実装クラス** | `InMemorySaver`, `PostgresSaver` | `InMemoryStore`, `PostgresStore` |
| **保存の単位** | **スレッド単位** (`thread_id`) | **グローバル / ユーザー単位** |
| **保存されるもの** | グラフの「状態（State）」そのもの | 抽出された「知識・事実・設定」 |
| **いつ使う？** | 会話の文脈（コンテキスト）維持 | ユーザーの好み、学習した知識の蓄積 |
| **検索方法** | IDによる状態の復元のみ | **セマンティック検索**（意味で探す）が可能 |

---

### なぜ「永続化」と「メモリ」が混同しやすいのか？

Cursorの説明で混乱された原因は、**「短期メモリも長期メモリも、どちらもディスク（DB）に保存（永続化）できるから」**だと思われます。

* **短期メモリの永続化:** 「会話が途切れても、同じスレッドIDなら続きから再開できる」ようにDBへ保存すること。
* **長期メモリの永続化:**
「ユーザーの好みを忘れない」ようにDBへ保存すること。

> **使い分けのヒント**
> * `checkpointer` を使うときは、**「今の会話のキャッチボール」**を維持したいとき。
> * `store` を使うときは、**「そのユーザーに関するデータベース」**を作りたいとき。
> 
> 

次は、具体的に「短期メモリが溢れないようにする（トリミングや要約）」の実装コードについて詳しく解説しましょうか？

---
短期メモリの永続化: 「会話が途切れても、同じスレッドIDなら続きから再開できる」ようにDBへ保存すること。

も、今一つピンときません。

このスレッド内だけなら、メモリへの記憶で良いのでは？
DBに記憶するというから、長期メモリと混同して混乱します。


もう、保存先がメモリかDBかをきにせず、

短期メモリ：本スレッド内（メモリかDBかは問わない）
長期メモリ：どのスレッドからでも参照可能に保存（永続化）

と割り切った方が良いですか？


---

結論から申し上げますと、**その割り切り方は大正解です！** むしろ、開発の実務においてはその理解が最も本質を突いています。

混乱を解くために、「なぜ短期メモリなのにDB（永続化）が出てくるのか」という点に絞って整理しましょう。

---

### 1. なぜ短期メモリをDBに保存するのか？（永続化の理由）

「短期＝メモリ（RAM）で十分では？」という疑問は非常に鋭いです。しかし、LangGraph（というかWebアプリ全般）では、以下の事態に備えるために「短期メモリのDB保存」が必要になります。

* **サーバーの再起動:** メモリ（RAM）だけに置いていると、サーバーが再起動した瞬間に、全ユーザーの「会話の途中経過」が消えてしまいます。
* **数時間後の返信:** ユーザーが3時間後に返信してきたとき、サーバーのメモリが他の処理でいっぱいになっていて、古い会話データを捨ててしまっているかもしれません。
* **サーバーが複数台ある場合:** Webサービスが大きくなると、サーバーAとサーバーBが動きます。最初の質問をAが受け、次の質問をBが受けたとき、DBに保存していないとBは「さっきの話」を知ることができません。

つまり、**「短期メモリ」を「（物理的に）永続化」するのは、情報の期間を長くしたいからではなく、情報の「生存率」を高めるため**なのです。

---

### 2. 「短期」と「長期」の決定的な違い

保存先がどこであれ（メモリでもPostgresでも）、LangGraphにおけるこの2つの違いは**「キー（鍵）」の構造**にあります。

| 種類 | 鍵（Key）のイメージ | データの性質 |
| --- | --- | --- |
| **短期メモリ** | `thread_id`（スレッドID） | **「進行中のパズル」**。そのスレッド専用の作業台。その会話が終われば、二度と触らないデータ。 |
| **長期メモリ** | `user_id`（ユーザーID） | **「ユーザーのプロフィール帳」**。どのスレッド（会話）からでも取り出せる共通の引き出し。 |

---

### まとめ：こう考えるとスッキリします

ユーザーさんの今の解釈を、少しだけ専門用語を添えて整理するとこうなります。

* **短期メモリ（チェックポインタ）**
* 目的：**「会話の続き」**を成立させるため。
* 範囲：特定の`thread_id`の中だけ。
* 保存先：消えてもいいならメモリ、消したくないならDB（でも中身は短期用）。


* **長期メモリ（ストア）**
* 目的：**「ユーザーのパーソナライズ」**のため。
* 範囲：すべてのスレッド、すべての時間で共有。
* 保存先：基本はDB（あとで検索して再利用するため）。



**「短期・長期というのは、情報の寿命や保存場所のことではなく、情報の『有効範囲（スコープ）』のことである」**

と割り切ってしまうのが、LangGraphを使いこなす一番の近道です。

次は、実際に「長期メモリ（Store）」に、ユーザーの好みをどうやって保存し、どうやって検索して取り出すのか、具体的なコード例を見てみますか？
