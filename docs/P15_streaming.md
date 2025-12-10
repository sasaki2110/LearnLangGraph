# Streaming

このドキュメントでは、LangGraphにおけるストリーミング出力の実装方法について詳細に解説します。

公式ドキュメント: https://docs.langchain.com/oss/python/langgraph/streaming

## 1. 概要

LangGraphは、リアルタイムの更新を提供するストリーミングシステムを実装しています。ストリーミングは、LLM（大規模言語モデル）を活用したアプリケーションの応答性を向上させるために不可欠です。完全な応答が準備される前に出力を段階的に表示することで、特にLLMの遅延に対処する際に、ユーザーエクスペリエンス（UX）を大幅に改善します。

### 1.1 LangGraphのストリーミングで可能なこと

- **グラフ状態のストリーミング**: `updates`および`values`モードを使用して、各ステップ後の状態の更新や全体の値を取得します。
- **サブグラフ出力のストリーミング**: 親グラフとネストされたサブグラフの両方からの出力を含めます。
- **LLMトークンのストリーミング**: ノード、サブグラフ、ツール内のどこからでもトークンストリームをキャプチャします。
- **カスタムデータのストリーミング**: ツール関数から直接カスタムの更新や進行状況のシグナルを送信します。
- **複数のストリーミングモードの使用**: `values`（全状態）、`updates`（状態の差分）、`messages`（LLMトークンとメタデータ）、`custom`（任意のユーザーデータ）、`debug`（詳細なトレース）から選択します。

### 1.2 ストリーミングの利点

1. **ユーザー体験の向上**: 結果を待たずに確認できる
2. **応答性の向上**: 処理が完了する前に結果を表示できる
3. **進行状況の可視化**: 処理の進行状況を把握できる
4. **デバッグの容易さ**: リアルタイムで状態の変化を確認できる

## 2. サポートされているストリームモード

`stream`または`astream`メソッドに、以下のストリームモードのいずれか、または複数をリストとして渡すことができます：

### 2.1 `values`

各グラフステップ後の**完全な状態の値**をストリームします。

```python
for chunk in graph.stream(inputs, stream_mode="values"):
    print(chunk)  # 完全な状態が返される
```

**特徴**:
- 各ステップ後の状態全体を取得
- 状態の完全なスナップショットが必要な場合に使用
- メモリ使用量が比較的多い

### 2.2 `updates`

各グラフステップ後の**状態の更新**をストリームします。同じステップで複数の更新が行われた場合（例：複数のノードが実行された場合）、それらの更新は個別にストリームされます。

```python
for chunk in graph.stream(inputs, stream_mode="updates"):
    print(chunk)  # 更新された部分のみが返される
```

**特徴**:
- 状態の差分のみを取得
- メモリ効率が良い
- 変更された部分のみを追跡したい場合に使用

#### `values`と`updates`の使い分け

| 項目 | `values` | `updates` |
|------|----------|-----------|
| **返されるデータ** | 完全な状態全体 | 更新された部分のみ |
| **ノード名の情報** | 含まれない | 含まれる（どのノードが更新したか分かる） |
| **メモリ効率** | やや悪い | 良い |
| **使用例** | 状態の完全なスナップショットが必要、状態の履歴を保存したい | 通常のストリーミング表示、デバッグ |
| **推奨** | 特別な理由がある場合のみ | **通常はこちらを推奨** |

**結論**: 特別な理由がない限り、`updates`を使用することを推奨します。`values`は状態の完全なスナップショットや履歴保存が必要な場合に使用します。

### 2.3 `custom`

グラフノード内から**カスタムデータ**をストリームします。`get_stream_writer()`を使用してノード内からカスタムデータを送信できます。

```python
for chunk in graph.stream(inputs, stream_mode="custom"):
    print(chunk)  # カスタムデータが返される
```

**特徴**:
- ノード内から任意のデータをストリーム可能
- 進行状況の報告などに使用
- `get_stream_writer()`を使用して実装

### 2.4 `messages`

LLMが呼び出される任意のグラフノードから、**2タプル（LLMトークン、メタデータ）**をストリームします。これにより、LLMの出力をトークン単位でリアルタイムに取得できます。

```python
for token, metadata in graph.stream(inputs, stream_mode="messages"):
    print(f"Token: {token}, Metadata: {metadata}")
```

**特徴**:
- LLMトークンをリアルタイムで取得
- メタデータ（ノード名、LLM呼び出し情報など）も同時に取得
- チャットUIなどでトークン単位の表示が必要な場合に使用

### 2.5 `debug`

グラフの実行全体で**可能な限り多くの情報**をストリームします。デバッグや詳細なトレースが必要な場合に使用します。

```python
for chunk in graph.stream(inputs, stream_mode="debug"):
    print(chunk)  # 詳細なデバッグ情報が返される
```

**特徴**:
- ノード名、完全な状態、実行フローなどの詳細情報
- デバッグ専用
- パフォーマンスへの影響がある可能性

**出力構造**:

`debug`モードは、実行フローの詳細なトレース情報を提供します。各チャンクは以下の構造を持ちます：

```python
{
    "step": 1,                    # ステップ番号
    "timestamp": "2025-12-10T08:14:33.072672+00:00",  # イベントの実行時刻
    "type": "task",              # イベントタイプ（"task" または "task_result"）
    "payload": {                  # 詳細情報
        "id": "...",             # イベントID
        "name": "refine_topic",  # ノード名
        "input": {...},          # 入力データ（type="task"の場合）
        "result": {...},         # 結果データ（type="task_result"の場合）
        "error": None            # エラー情報（エラーが発生した場合）
    }
}
```

**イベントタイプ**:

1. **`type: "task"`** - ノードの実行開始
   - `payload.input`: ノードへの入力データ
   - `payload.name`: 実行されるノード名
   - `payload.triggers`: トリガー情報

2. **`type: "task_result"`** - ノードの実行完了
   - `payload.result`: ノードの実行結果
   - `payload.name`: 実行されたノード名
   - `payload.error`: エラー情報（エラーが発生した場合）
   - `payload.interrupts`: 割り込み情報

**使用例**:

```python
for chunk in graph.stream(inputs, stream_mode="debug"):
    event_type = chunk.get("type")
    step = chunk.get("step")
    payload = chunk.get("payload", {})
    node_name = payload.get("name")
    
    if event_type == "task":
        print(f"ステップ {step}: ノード '{node_name}' の実行開始")
        print(f"入力: {payload.get('input')}")
    elif event_type == "task_result":
        print(f"ステップ {step}: ノード '{node_name}' の実行完了")
        if payload.get("error"):
            print(f"エラー: {payload.get('error')}")
        else:
            print(f"結果: {payload.get('result')}")
```

**注意点**:
- `debug`モードは`messages`モードを網羅しません。LLMトークンも取得したい場合は、`stream_mode=["debug", "messages"]`を使用してください。
- `debug`モードは`updates`や`values`と重複する情報を含む可能性があるため、同時に指定するのは非推奨です。

## 3. 基本的な使用例

LangGraphのグラフは、ストリーム出力をイテレータとして生成する`stream`（同期）および`astream`（非同期）メソッドを提供しています。

### 3.1 基本的なストリーミング

```python
from langgraph.graph import StateGraph, START, END
from typing import TypedDict

class State(TypedDict):
    topic: str
    joke: str

def refine_topic(state: State):
    return {"topic": state["topic"] + " and cats"}

def generate_joke(state: State):
    return {"joke": f"This is a joke about {state['topic']}"}

# グラフの構築
graph = (
    StateGraph(State)
    .add_node("refine_topic", refine_topic)
    .add_node("generate_joke", generate_joke)
    .add_edge(START, "refine_topic")
    .add_edge("refine_topic", "generate_joke")
    .add_edge("generate_joke", END)
    .compile()
)

# stream()メソッドは、ストリーム出力を生成するイテレータを返します
for chunk in graph.stream(
    {"topic": "ice cream"},
    stream_mode="updates",  # 各ノード後のグラフ状態の更新のみをストリーム
):
    print(chunk)
```

**出力例**:

```
{'refine_topic': {'topic': 'ice cream and cats'}}
{'generate_joke': {'joke': 'This is a joke about ice cream and cats'}}
```

### 3.2 非同期ストリーミング

```python
import asyncio

async def main():
    async for chunk in graph.astream(
        {"topic": "ice cream"},
        stream_mode="updates",
    ):
        print(chunk)

asyncio.run(main())
```

#### 同期と非同期の使い分け

| 項目 | 同期 (`stream()`) | 非同期 (`astream()`) |
|------|-------------------|----------------------|
| **単一タスク** | 適している | 使用可能（同期とほぼ同じ） |
| **複数タスクの並列実行** | 順次実行（時間が合計される） | 並列実行可能（大幅に短縮） |
| **Webアプリケーション** | 統合が難しい | **必須**（FastAPI等と統合） |
| **I/O待機中の処理** | ブロックされる | 他の処理を実行可能 |
| **推奨用途** | スクリプト、CLIツール | Webアプリケーション、複数タスクの並列処理 |

**使い分けの指針**:
- **一般的なスクリプト/CLIツール**: 同期 (`stream`) で十分
- **Webアプリケーション（FastAPI等）**: 非同期 (`astream`) を推奨
- **複数タスクを並列処理したい場合**: 非同期 (`astream`) を推奨
- **既存の同期コードベース**: 同期 (`stream`) で統合が容易

## 4. 複数のモードを同時にストリームする

`stream_mode`パラメータにリストを渡すことで、複数のモードを同時にストリームできます。ストリームされた出力は、`(mode, chunk)`のタプルで提供され、`mode`はストリームモードの名前、`chunk`はそのモードによってストリームされたデータです。

```python
for mode, chunk in graph.stream(
    {"topic": "ice cream"},
    stream_mode=["updates", "messages"],  # 複数のモードを同時にストリーム
):
    print(f"Mode: {mode}, Chunk: {chunk}")
```

**使用例**:

```python
# ノードの更新とLLMトークンを同時にストリーム
for mode, chunk in graph.stream(
    initial_state,
    stream_mode=["updates", "messages"],
):
    if mode == "updates":
        print(f"Node update: {chunk}")
    elif mode == "messages":
        token, metadata = chunk
        print(f"LLM token: {token}")
```

**利点**:
- 異なる種類の情報を同時に取得可能
- ノードの進行状況とLLMトークンを同時に監視
- 柔軟なデータ処理が可能

## 5. グラフ状態のストリーミング

`values`および`updates`のストリームモードを使用して、グラフの実行中の状態をストリームできます。

### 5.1 `updates`モードの使用

各ステップ後の状態の更新のみをストリームします。

```python
for chunk in graph.stream(
    {"topic": "ice cream"},
    stream_mode="updates",
):
    print(chunk)
```

**出力形式**:
```python
{'refine_topic': {'topic': 'ice cream and cats'}}
{'generate_joke': {'joke': 'This is a joke about ice cream and cats'}}
```

### 5.2 `values`モードの使用

各ステップ後の完全な状態をストリームします。

```python
for chunk in graph.stream(
    {"topic": "ice cream"},
    stream_mode="values",
):
    print(chunk)
```

**出力形式**:
```python
{'topic': 'ice cream and cats', 'joke': ''}
{'topic': 'ice cream and cats', 'joke': 'This is a joke about ice cream and cats'}
```

### 5.3 状態ストリーミングの実践例

```python
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain.messages import HumanMessage, AIMessage
import operator

class MessagesState(TypedDict):
    messages: Annotated[list, operator.add]

def llm_node(state: MessagesState):
    # LLM呼び出しのシミュレーション
    return {
        "messages": [AIMessage(content="Hello! How can I help you?")]
    }

graph = (
    StateGraph(MessagesState)
    .add_node("llm", llm_node)
    .add_edge(START, "llm")
    .add_edge("llm", END)
    .compile()
)

# 状態の更新をストリーム
for chunk in graph.stream(
    {"messages": [HumanMessage(content="Hi!")]},
    stream_mode="updates",
):
    node_name = list(chunk.keys())[0]
    state_update = chunk[node_name]
    print(f"Node: {node_name}")
    print(f"Update: {state_update}")
    print()
```

## 6. サブグラフ出力のストリーミング

親グラフの`.stream()`メソッドで`subgraphs=True`を設定することで、サブグラフからの出力もストリームに含めることができます。出力は`(namespace, data)`のタプルとしてストリームされ、`namespace`はサブグラフが呼び出されたノードへのパスを示すタプルです。

### 6.1 サブグラフの定義とストリーミング

```python
from langgraph.graph import StateGraph, START, END
from typing import TypedDict

# サブグラフの状態定義
class SubgraphState(TypedDict):
    foo: str
    bar: str

def subgraph_node_1(state: SubgraphState):
    return {"bar": "bar"}

def subgraph_node_2(state: SubgraphState):
    return {"foo": state["foo"] + state["bar"]}

# サブグラフの構築
subgraph_builder = StateGraph(SubgraphState)
subgraph_builder.add_node("subgraph_node_1", subgraph_node_1)
subgraph_builder.add_node("subgraph_node_2", subgraph_node_2)
subgraph_builder.add_edge(START, "subgraph_node_1")
subgraph_builder.add_edge("subgraph_node_1", "subgraph_node_2")
subgraph = subgraph_builder.compile()

# 親グラフの状態定義
class ParentState(TypedDict):
    foo: str

def node_1(state: ParentState):
    return {"foo": "hi! " + state["foo"]}

# 親グラフの構築
builder = StateGraph(ParentState)
builder.add_node("node_1", node_1)
builder.add_node("node_2", subgraph)  # サブグラフをノードとして追加
builder.add_edge(START, "node_1")
builder.add_edge("node_1", "node_2")
graph = builder.compile()

# サブグラフの出力も含めてストリーム
for chunk in graph.stream(
    {"foo": "foo"},
    stream_mode="updates",
    subgraphs=True,  # サブグラフの出力も含める
):
    print(chunk)
```

**出力例**:

```
((), {'node_1': {'foo': 'hi! foo'}})
(('node_2',), {'subgraph_node_1': {'bar': 'bar'}})
(('node_2',), {'subgraph_node_2': {'foo': 'hi! foobar'}})
((), {'node_2': {'foo': 'hi! foobar'}})
```

**説明**:
- `()`は親グラフからの出力を示す
- `('node_2',)`は`node_2`サブグラフからの出力を示す
- ネストされたサブグラフの場合、パスはより長くなる（例: `('node_2', 'nested_node', ...)`）

## 7. LLMトークンのストリーミング

`messages`ストリームモードを使用して、LLMが呼び出されるグラフノードからのトークンとメタデータをストリームできます。これにより、LLMの出力をトークン単位でリアルタイムに取得し、ユーザーに即座にフィードバックを提供できます。

### 7.1 基本的なLLMトークンストリーミング

```python
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, START, END
from langchain.messages import HumanMessage, AIMessage
from typing import TypedDict, Annotated
import operator

class State(TypedDict):
    messages: Annotated[list, operator.add]

# LLMの初期化
llm = init_chat_model("gpt-4o-mini")

def llm_node(state: State):
    response = llm.invoke(state["messages"])
    return {"messages": [response]}

graph = (
    StateGraph(State)
    .add_node("llm", llm_node)
    .add_edge(START, "llm")
    .add_edge("llm", END)
    .compile()
)

# LLMトークンをストリーム
for token, metadata in graph.stream(
    {"messages": [HumanMessage(content="Tell me a joke about programming.")]},
    stream_mode="messages",  # messagesモードでトークン単位のストリーミング
):
    # tokenはAIMessageオブジェクトなので、content属性からテキストを取得
    token_text = token.content if hasattr(token, 'content') else str(token)
    print(token_text, end="", flush=True)  # トークンを逐次表示
    # metadataにはノード名、LLM呼び出し情報などが含まれる
```

**重要な注意点**:
- `token`は`AIMessage`オブジェクトです。テキストを取得するには`token.content`を使用します。
- `token`を直接`print()`すると、オブジェクト全体が文字列として表示されてしまいます。
- `hasattr(token, 'content')`でチェックすることで、異なる型にも対応できます。

### 7.2 メタデータの活用

メタデータには、ノード名、LLM呼び出し情報、実行ステップ情報などが含まれます。メタデータを活用することで、より高度なストリーミング処理が可能になります。

#### 基本的なメタデータの取得

```python
for token, metadata in graph.stream(
    {"messages": [HumanMessage(content="Hello!")]},
    stream_mode="messages",
):
    # メタデータから情報を取得
    # 注意: メタデータのキーは "langgraph_node" です（"node" ではありません）
    node_name = metadata.get("langgraph_node", "unknown")
    
    # tokenはAIMessageオブジェクトなので、content属性からテキストを取得
    token_text = token.content if hasattr(token, 'content') else str(token)
    
    print(f"[{node_name}] {token_text}")
```

#### メタデータの主なキー

メタデータには以下のようなキーが含まれます：

- `langgraph_node`: ノード名（例: "llm", "refine_topic"）
- `langgraph_step`: 実行ステップ番号
- `langgraph_path`: 実行パス
- `ls_provider`: LLMプロバイダー名（例: "openai"）
- `ls_model_name`: モデル名（例: "gpt-4o-mini"）
- `ls_model_type`: モデルタイプ（例: "chat"）
- `ls_temperature`: 温度パラメータ

#### ノード名でフィルタリング

複数のノードがある場合、特定のノードからのトークンのみを処理できます：

```python
target_node = "generate_summary"

for token, metadata in graph.stream(
    initial_state,
    stream_mode="messages",
):
    node_name = metadata.get("langgraph_node", "unknown")
    
    # 特定のノードからのトークンのみを処理
    if node_name == target_node:
        token_text = token.content if hasattr(token, 'content') else str(token)
        print(token_text, end="", flush=True)
```

#### ノードごとにトークンを集計

各ノードから生成されたトークン数を集計できます：

```python
from collections import defaultdict

node_token_counts = defaultdict(int)
node_texts = defaultdict(str)

for token, metadata in graph.stream(
    initial_state,
    stream_mode="messages",
):
    token_text = token.content if hasattr(token, 'content') else str(token)
    node_name = metadata.get("langgraph_node", "unknown")
    
    node_token_counts[node_name] += 1
    node_texts[node_name] += token_text

# 集計結果を表示
for node_name, count in node_token_counts.items():
    print(f"ノード {node_name}: {count} トークン")
```

#### メタデータが全トークンで同じかどうか

メタデータは、同じLLM呼び出し内の全トークンで同じ内容が設定されます。これは、ノード名やLLM呼び出し情報が同じであることを意味します。

```python
metadata_samples = []

for i, (token, metadata) in enumerate(graph.stream(
    initial_state,
    stream_mode="messages",
)):
    # 最初、中間、最後のトークンでメタデータを記録
    if i == 0:
        metadata_samples.append(("最初のトークン", metadata.copy()))
    elif i == 10:
        metadata_samples.append(("10番目のトークン", metadata.copy()))
    elif i % 20 == 0:
        metadata_samples.append((f"{i}番目のトークン", metadata.copy()))

# メタデータを比較（全トークンで同じ内容が設定されていることを確認）
for label, meta in metadata_samples:
    print(f"{label}: ノード名 = {meta.get('langgraph_node', 'N/A')}")
```

### 7.3 複数のモードとLLMトークンの組み合わせ

```python
# ノードの更新とLLMトークンを同時にストリーム
for mode, chunk in graph.stream(
    {"messages": [HumanMessage(content="Hello!")]},
    stream_mode=["updates", "messages"],
):
    if mode == "updates":
        print(f"\n[Node Update] {chunk}")
    elif mode == "messages":
        token, metadata = chunk
        print(token, end="", flush=True)
```

### 7.4 LLMトークンストリーミングの実践例

```python
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, START, END
from langchain.messages import SystemMessage, HumanMessage
from typing import TypedDict, Annotated
import operator

class ChatState(TypedDict):
    messages: Annotated[list, operator.add]

llm = init_chat_model("gpt-4o-mini")

def chat_node(state: ChatState):
    messages = [
        SystemMessage(content="You are a helpful assistant."),
    ] + state["messages"]
    response = llm.invoke(messages)
    return {"messages": [response]}

graph = (
    StateGraph(ChatState)
    .add_node("chat", chat_node)
    .add_edge(START, "chat")
    .add_edge("chat", END)
    .compile()
)

print("AI: ", end="", flush=True)
for token, metadata in graph.stream(
    {"messages": [HumanMessage(content="Write a short poem about AI.")]},
    stream_mode="messages",
):
    print(token, end="", flush=True)
print()  # 改行
```

## 8. LLM呼び出しによるフィルタリング

特定のLLM呼び出しに基づいてストリームをフィルタリングできます。メタデータ内のLLM呼び出し情報を使用して、関心のあるLLM呼び出しからのトークンのみを取得できます。

### 8.1 LLM呼び出しのフィルタリング例

```python
# 特定のLLM呼び出しからのトークンのみを取得
for token, metadata in graph.stream(
    initial_state,
    stream_mode="messages",
):
    # メタデータからLLM呼び出し情報を取得
    llm_invocation = metadata.get("llm_invocation", {})
    llm_name = llm_invocation.get("name", "")
    
    # 特定のLLMからのトークンのみを処理
    if llm_name == "gpt-4o-mini":
        print(token, end="", flush=True)
```

### 8.2 複数のLLM呼び出しの区別

```python
from collections import defaultdict

llm_tokens = defaultdict(str)

for token, metadata in graph.stream(
    initial_state,
    stream_mode="messages",
):
    llm_invocation = metadata.get("llm_invocation", {})
    llm_id = llm_invocation.get("id", "unknown")
    
    # LLM呼び出しごとにトークンを集約
    llm_tokens[llm_id] += token

# 各LLM呼び出しの結果を表示
for llm_id, tokens in llm_tokens.items():
    print(f"LLM {llm_id}: {tokens}")
```

## 9. ノードによるフィルタリング

特定のノードに基づいてストリームをフィルタリングできます。メタデータ内のノード情報を使用して、特定のノードからの出力のみを取得できます。

### 9.1 ノードによるフィルタリング例

```python
# 特定のノードからの出力のみを取得
for chunk in graph.stream(
    initial_state,
    stream_mode="updates",
):
    node_name = list(chunk.keys())[0]
    
    # 特定のノードからの更新のみを処理
    if node_name == "llm_node":
        print(f"LLM Node Update: {chunk[node_name]}")
```

### 9.2 メッセージモードでのノードフィルタリング

```python
# messagesモードでもノードでフィルタリング可能
for token, metadata in graph.stream(
    initial_state,
    stream_mode="messages",
):
    node_name = metadata.get("node", "unknown")
    
    # 特定のノードからのトークンのみを処理
    if node_name == "chat_node":
        print(token, end="", flush=True)
```

### 9.3 複数ノードの監視

```python
target_nodes = {"llm_node", "tool_node"}

for chunk in graph.stream(
    initial_state,
    stream_mode="updates",
):
    node_name = list(chunk.keys())[0]
    
    if node_name in target_nodes:
        print(f"[{node_name}] {chunk[node_name]}")
```

## 10. カスタムデータのストリーミング

`custom`モードを使用して、グラフノード内からカスタムデータや進行状況のシグナルをストリームできます。`get_stream_writer()`を使用してノード内からカスタムデータを送信します。

### 10.1 `get_stream_writer()`の使用

```python
from langgraph.config import get_stream_writer
from langgraph.graph import StateGraph, START, END
from typing import TypedDict

class State(TypedDict):
    progress: int
    result: str

def process_node(state: State):
    writer = get_stream_writer()
    
    # 進行状況をストリーム
    if writer:
        writer({"progress": 25, "status": "Starting processing"})
    
    # 処理のシミュレーション
    result = "Processing..."
    
    if writer:
        writer({"progress": 50, "status": "Halfway done"})
    
    result = "Complete"
    
    if writer:
        writer({"progress": 100, "status": "Finished"})
    
    return {"result": result}

graph = (
    StateGraph(State)
    .add_node("process", process_node)
    .add_edge(START, "process")
    .add_edge("process", END)
    .compile()
)

# カスタムデータをストリーム
for chunk in graph.stream(
    {"progress": 0, "result": ""},
    stream_mode="custom",
):
    print(f"Custom data: {chunk}")
```

**出力例**:

```
Custom data: {'progress': 25, 'status': 'Starting processing'}
Custom data: {'progress': 50, 'status': 'Halfway done'}
Custom data: {'progress': 100, 'status': 'Finished'}
```

### 10.2 カスタムデータと他のモードの組み合わせ

```python
# カスタムデータと更新を同時にストリーム
for mode, chunk in graph.stream(
    initial_state,
    stream_mode=["updates", "custom"],
):
    if mode == "custom":
        print(f"[Progress] {chunk}")
    elif mode == "updates":
        print(f"[State Update] {chunk}")
```

### 10.3 実践的な使用例: 進行状況の報告

```python
from langgraph.config import get_stream_writer
from langgraph.graph import StateGraph, START, END
from typing import TypedDict
import time

class TaskState(TypedDict):
    task_id: str
    status: str
    items_processed: int
    total_items: int

def process_items(state: TaskState):
    writer = get_stream_writer()
    total = state["total_items"]
    
    for i in range(total):
        # アイテムの処理
        time.sleep(0.1)  # 処理のシミュレーション
        
        # 進行状況をストリーム
        if writer:
            progress = int((i + 1) / total * 100)
            writer({
                "progress": progress,
                "items_processed": i + 1,
                "status": f"Processing item {i + 1}/{total}"
            })
    
    return {
        "status": "completed",
        "items_processed": total
    }

graph = (
    StateGraph(TaskState)
    .add_node("process", process_items)
    .add_edge(START, "process")
    .add_edge("process", END)
    .compile()
)

# 進行状況を監視
for chunk in graph.stream(
    {"task_id": "task_1", "status": "pending", "items_processed": 0, "total_items": 10},
    stream_mode="custom",
):
    progress = chunk.get("progress", 0)
    status = chunk.get("status", "")
    print(f"[{progress}%] {status}")
```

## 11. 任意のLLMでの使用

LangGraphのストリーミング機能は、任意のLLMと組み合わせて使用できます。LangChainがサポートするすべてのLLMプロバイダーで動作します。

### 11.1 異なるLLMプロバイダーの使用

```python
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, START, END
from langchain.messages import HumanMessage
from typing import TypedDict, Annotated
import operator

class State(TypedDict):
    messages: Annotated[list, operator.add]

# OpenAI
llm_openai = init_chat_model("gpt-4o-mini")

# Anthropic (Claude)
llm_anthropic = init_chat_model("claude-3-5-sonnet-20241022")

# Google (Gemini)
llm_google = init_chat_model("gemini-1.5-pro")

def llm_node(state: State):
    # 任意のLLMを使用
    response = llm_openai.invoke(state["messages"])
    return {"messages": [response]}

graph = (
    StateGraph(State)
    .add_node("llm", llm_node)
    .add_edge(START, "llm")
    .add_edge("llm", END)
    .compile()
)

# どのLLMでもストリーミングが動作
for token, metadata in graph.stream(
    {"messages": [HumanMessage(content="Hello!")]},
    stream_mode="messages",
):
    print(token, end="", flush=True)
```

### 11.2 ローカルLLMでの使用

```python
# OllamaなどのローカルLLMでも使用可能
llm_local = init_chat_model("ollama/llama2")

def local_llm_node(state: State):
    response = llm_local.invoke(state["messages"])
    return {"messages": [response]}

graph_local = (
    StateGraph(State)
    .add_node("llm", local_llm_node)
    .add_edge(START, "llm")
    .add_edge("llm", END)
    .compile()
)

# ローカルLLMでもストリーミングが動作
for token, metadata in graph_local.stream(
    {"messages": [HumanMessage(content="Hello!")]},
    stream_mode="messages",
):
    print(token, end="", flush=True)
```

## 12. 特定のチャットモデルでのストリーミングの無効化

特定のチャットモデルでストリーミングを無効にすることができます。これは、ストリーミングをサポートしていないモデルや、パフォーマンス上の理由でストリーミングを無効にしたい場合に有用です。

### 12.1 ストリーミングの無効化方法

```python
from langchain.chat_models import init_chat_model
from langchain_core.runnables import RunnableConfig

# ストリーミングを無効にする設定
config = RunnableConfig(
    configurable={
        "disable_streaming": True  # ストリーミングを無効化
    }
)

llm = init_chat_model("gpt-4o-mini")

# ストリーミングが無効化された状態で使用
response = llm.invoke([HumanMessage(content="Hello!")], config=config)
```

### 12.2 条件付きストリーミング無効化

```python
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, START, END
from langchain.messages import HumanMessage
from typing import TypedDict, Annotated
import operator

class State(TypedDict):
    messages: Annotated[list, operator.add]

def llm_node(state: State):
    llm = init_chat_model("gpt-4o-mini")
    
    # 条件に応じてストリーミングを無効化
    use_streaming = len(state["messages"]) < 5  # 例: メッセージ数が少ない場合のみストリーミング
    
    if use_streaming:
        response = llm.invoke(state["messages"])
    else:
        # ストリーミングを無効化
        config = RunnableConfig(
            configurable={"disable_streaming": True}
        )
        response = llm.invoke(state["messages"], config=config)
    
    return {"messages": [response]}

graph = (
    StateGraph(State)
    .add_node("llm", llm_node)
    .add_edge(START, "llm")
    .add_edge("llm", END)
    .compile()
)
```

### 12.3 モデルごとのストリーミング設定

```python
# モデルごとにストリーミングの設定を管理
STREAMING_CONFIG = {
    "gpt-4o-mini": True,  # ストリーミング有効
    "gpt-3.5-turbo": True,
    "claude-3-5-sonnet-20241022": True,
    "gemini-1.5-pro": False,  # ストリーミング無効
}

def get_llm_config(model_name: str):
    config = RunnableConfig()
    if not STREAMING_CONFIG.get(model_name, True):
        config.configurable = {"disable_streaming": True}
    return config

llm = init_chat_model("gpt-4o-mini")
config = get_llm_config("gpt-4o-mini")
response = llm.invoke([HumanMessage(content="Hello!")], config=config)
```

## 13. Python 3.11未満での非同期処理

Python 3.11未満のバージョンでは、非同期処理を行う際に`asyncio`を使用する必要があります。Python 3.11以降では、`asyncio`の使用が簡略化されていますが、3.11未満でも同様の機能を使用できます。

### 13.1 Python 3.11未満での非同期ストリーミング

```python
import asyncio
from langgraph.graph import StateGraph, START, END
from typing import TypedDict

class State(TypedDict):
    message: str

def process_node(state: State):
    return {"message": f"Processed: {state['message']}"}

graph = (
    StateGraph(State)
    .add_node("process", process_node)
    .add_edge(START, "process")
    .add_edge("process", END)
    .compile()
)

# Python 3.11未満での非同期ストリーミング
async def main():
    async for chunk in graph.astream(
        {"message": "Hello"},
        stream_mode="updates",
    ):
        print(chunk)

# asyncio.run()を使用して実行
if __name__ == "__main__":
    asyncio.run(main())
```

### 13.2 複数の非同期タスクの実行

```python
import asyncio
from langgraph.graph import StateGraph, START, END
from typing import TypedDict

class State(TypedDict):
    task_id: str
    result: str

def task_node(state: State):
    return {"result": f"Task {state['task_id']} completed"}

graph = (
    StateGraph(State)
    .add_node("task", task_node)
    .add_edge(START, "task")
    .add_edge("task", END)
    .compile()
)

async def run_task(task_id: str):
    async for chunk in graph.astream(
        {"task_id": task_id, "result": ""},
        stream_mode="updates",
    ):
        print(f"Task {task_id}: {chunk}")

async def main():
    # 複数のタスクを並列実行
    tasks = [
        run_task(f"task_{i}")
        for i in range(3)
    ]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
```

### 13.3 エラーハンドリング付き非同期ストリーミング

```python
import asyncio
from langgraph.graph import StateGraph, START, END
from typing import TypedDict

class State(TypedDict):
    data: str

def process_node(state: State):
    if state["data"] == "error":
        raise ValueError("Simulated error")
    return {"data": f"Processed: {state['data']}"}

graph = (
    StateGraph(State)
    .add_node("process", process_node)
    .add_edge(START, "process")
    .add_edge("process", END)
    .compile()
)

async def main():
    try:
        async for chunk in graph.astream(
            {"data": "test"},
            stream_mode="updates",
        ):
            print(chunk)
    except Exception as e:
        print(f"Error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())
```

## 14. ストリーミングのベストプラクティス

### 14.1 適切なストリーミングモードの選択

用途に応じて適切なストリーミングモードを選択します：

- **ユーザー向けUI**: `messages`モードでLLMトークンをリアルタイム表示
- **デバッグ**: `debug`モードで詳細な情報を取得
- **状態監視**: `updates`モードで状態の変化を追跡
- **進行状況表示**: `custom`モードでカスタムデータを送信

### 14.2 エラーハンドリング

ストリーミング中にエラーが発生する可能性があるため、適切にエラーハンドリングします。

```python
try:
    for chunk in graph.stream(initial_state, stream_mode="updates"):
        # チャンクの処理
        process_chunk(chunk)
except Exception as e:
    print(f"エラーが発生しました: {e}")
    # エラー処理
```

### 14.3 パフォーマンスの考慮

ストリーミングはオーバーヘッドが発生するため、必要な場合のみ使用します：

- **短い処理**: ストリーミング不要
- **長い処理**: ストリーミング推奨
- **ユーザー体験**: リアルタイム表示が必要な場合に使用

### 14.4 メモリ管理

大量のデータをストリーミングする場合、メモリ使用量に注意します。

```python
# チャンクを処理したらすぐに破棄
for chunk in graph.stream(initial_state, stream_mode="values"):
    process_chunk(chunk)
    # chunkへの参照を保持しない
    del chunk
```

## 15. ストリーミングと`invoke()`の比較

| 特徴 | `invoke()` | `stream()` |
|------|-----------|-----------|
| **戻り値** | 最終状態のみ | 各ノードの状態更新 |
| **待機時間** | 処理完了まで待機 | リアルタイムで結果を返す |
| **ユーザー体験** | 結果を待つ必要がある | 進行状況を確認できる |
| **パフォーマンス** | オーバーヘッドが少ない | オーバーヘッドがある |
| **用途** | バッチ処理、テスト | インタラクティブなアプリケーション |
| **メモリ使用量** | 少ない | ストリーミングモードによる |
| **エラーハンドリング** | 簡単 | ストリーム中のエラー処理が必要 |

## 16. 実践的な使用例

### 16.1 Webアプリケーションでのストリーミング

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from langgraph.graph import StateGraph, START, END
from langchain.messages import HumanMessage
import json

app = FastAPI()

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """チャットのストリーミングエンドポイント"""
    
    def generate():
        initial_state = {
            "messages": [HumanMessage(content=request.message)],
        }
        
        for chunk in graph.stream(initial_state, stream_mode="messages"):
            token, metadata = chunk
            # Server-Sent Events形式でストリーミング
            yield f"data: {json.dumps({'token': token, 'metadata': metadata})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")
```

### 16.2 進行状況バーの実装

```python
from langgraph.config import get_stream_writer
from tqdm import tqdm

def process_with_progress(state):
    writer = get_stream_writer()
    total = 100
    
    with tqdm(total=total) as pbar:
        for i in range(total):
            # 処理
            time.sleep(0.01)
            
            if writer:
                writer({"progress": i + 1})
            
            pbar.update(1)
    
    return {"status": "completed"}

# カスタムデータをストリームして進行状況を表示
for chunk in graph.stream(
    initial_state,
    stream_mode="custom",
):
    progress = chunk.get("progress", 0)
    print(f"Progress: {progress}%")
```

## 17. まとめ

ストリーミングにより、以下のことが可能になります：

1. **リアルタイムでの結果表示**: 処理の完了を待たずに結果を確認
2. **ユーザー体験の向上**: 進行状況を可視化
3. **インタラクティブなアプリケーション**: チャットUIなどでの活用
4. **デバッグの容易さ**: リアルタイムで状態の変化を確認
5. **柔軟なデータ処理**: 複数のモードを組み合わせて使用

適切にストリーミングを実装することで、より良いユーザー体験を提供できます。

## 次のステップ

- [P16: Persistence](./P16_persistence.md): 状態の永続化
- [P17: Functional API](./P17_functional_api.md): 関数型APIの使用方法
- [P18: Interrupts](./P18_interrupts.md): 人間の介入（Human-in-the-loop）
