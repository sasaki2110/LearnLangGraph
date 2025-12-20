# Persistence

このドキュメントでは、LangGraphにおける状態の永続化（Persistence）について解説します。

公式ドキュメント: https://docs.langchain.com/oss/python/langgraph/persistence

## 概要

LangGraphは、チェックポインタ（checkpointer）を通じて組み込みの永続化レイヤーを提供します。グラフをチェックポインタと共にコンパイルすると、各スーパー・ステップでグラフの状態の「チェックポイント」が保存されます。これらのチェックポイントは「スレッド（thread）」に保存され、グラフの実行後にアクセス可能です。スレッドを通じてグラフの状態にアクセスできるため、ヒューマン・イン・ザ・ループ（human-in-the-loop）、メモリ、タイムトラベル、フォールトトレランスなどの強力な機能が実現されます。

**Agent Serverはチェックポイントを自動的に処理します**  
Agent Serverを使用する場合、チェックポインタを手動で実装または設定する必要はありません。サーバーがバックグラウンドで全ての永続化インフラストラクチャを処理します。

## スレッド（Threads）

スレッドは、チェックポインタによって保存される各チェックポイントに割り当てられる一意のIDまたはスレッド識別子です。これは、一連の実行（runs）の累積状態を含みます。実行が行われると、アシスタントの基盤となるグラフの状態がスレッドに永続化されます。

チェックポインタを使用してグラフを呼び出す際には、`config`の`configurable`部分で`thread_id`を指定する必要があります：

```python
config = {"configurable": {"thread_id": "1"}}
```

スレッドの現在および過去の状態は取得可能です。状態を永続化するためには、実行前にスレッドを作成する必要があります。LangSmith APIは、スレッドとその状態の作成および管理のための複数のエンドポイントを提供しています。詳細は[APIリファレンス](https://reference.langchain.com)をご参照ください。

チェックポインタは`thread_id`を主キーとしてチェックポイントの保存と取得を行います。これがないと、チェックポインタは状態を保存したり、[中断](https://docs.langchain.com/oss/python/langgraph/interrupts)後に実行を再開したりすることができません。

### スレッドIDの設計

スレッドIDは、以下のような形式を推奨します：

```python
# ユーザーID + セッションID
thread_id = f"user-{user_id}-session-{session_id}"

# または、UUIDを使用
import uuid
thread_id = str(uuid.uuid4())
```

## チェックポイント（Checkpoints）

スレッドの特定の時点での状態は「チェックポイント」と呼ばれます。チェックポイントは、各スーパー・ステップで保存されるグラフ状態のスナップショットであり、以下の主要なプロパティを持つ`StateSnapshot`オブジェクトで表されます：

- **`config`**：このチェックポイントに関連付けられた設定。
- **`metadata`**：このチェックポイントに関連付けられたメタデータ。
- **`values`**：この時点での状態チャネルの値。
- **`next`**：グラフ内で次に実行するノード名のタプル。
- **`tasks`**：次に実行されるタスクに関する情報を含む`PregelTask`オブジェクトのタプル。以前にステップが試行された場合、エラー情報が含まれます。ノード内で[動的に](https://docs.langchain.com/oss/python/langgraph/interrupts)グラフが中断された場合、`tasks`には中断に関連する追加データが含まれます。

チェックポイントは永続化され、後でスレッドの状態を復元するために使用できます。

### 基本的な例

以下に、シンプルなグラフを呼び出した際に保存されるチェックポイントの例を示します：

```python
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables import RunnableConfig
from typing import Annotated
from typing_extensions import TypedDict
from operator import add

class State(TypedDict):
    foo: str
    bar: Annotated[list[str], add]

def node_a(state: State):
    return {"foo": "a", "bar": ["a"]}

def node_b(state: State):
    return {"foo": "b", "bar": ["b"]}

workflow = StateGraph(State)
workflow.add_node("node_a", node_a)
workflow.add_node("node_b", node_b)
workflow.add_edge(START, "node_a")
workflow.add_edge("node_a", "node_b")
workflow.add_edge("node_b", END)

checkpointer = MemorySaver()
graph = workflow.compile(checkpointer=checkpointer)

config = RunnableConfig(configurable={"thread_id": "1"})
graph.invoke({}, config)
```

このコードを実行すると、以下のチェックポイントが保存されます：

1. **初期状態**：`{"foo": "", "bar": []}`
2. **`node_a`実行後**：`{"foo": "a", "bar": ["a"]}`
3. **`node_b`実行後**：`{"foo": "b", "bar": ["a", "b"]}`

各チェックポイントは、グラフの特定の時点での状態をキャプチャし、後での分析や再実行に役立ちます。

## 状態の取得（Get State）

チェックポインタを使用すると、スレッドの現在の状態を取得できます。これは、グラフの実行中や実行後に状態を確認するのに役立ちます。

### 基本的な使用方法

```python
from langchain_core.runnables import RunnableConfig

config = RunnableConfig(configurable={"thread_id": "1"})
state = graph.get_state(config)

print(state.values)  # 現在の状態の値
print(state.config)  # チェックポイントの設定
print(state.metadata)  # チェックポイントのメタデータ
```

### 特定のチェックポイントの取得

特定のチェックポイントIDから状態を取得することも可能です：

```python
# チェックポイントIDを指定して状態を取得
state = graph.get_state(config, as_of="checkpoint-id-here")
```

## 状態履歴の取得（Get State History）

チェックポインタは、スレッドの全履歴を取得する機能も提供します。これにより、グラフの各ステップでの状態を確認できます。

### 基本的な使用方法

```python
config = RunnableConfig(configurable={"thread_id": "1"})
history = graph.get_state_history(config)

for checkpoint in history:
    print(f"チェックポイントID: {checkpoint.id}")
    print(f"タイムスタンプ: {checkpoint.ts}")
    print(f"状態: {checkpoint.values}")
    print(f"次に実行するノード: {checkpoint.next}")
    print("---")
```

### 履歴のフィルタリング

履歴をフィルタリングして、特定の条件に一致するチェックポイントのみを取得することも可能です：

```python
# 特定のノード実行後のチェックポイントのみを取得
history = graph.get_state_history(
    config,
    filter={"node": "node_a"}
)
```

## リプレイ（Replay）

チェックポイントを使用すると、以前の状態からグラフの実行を再開することができます。これは、エラーが発生した場合や異なるパスを試したい場合に役立ちます。

### 基本的な使用方法

`thread_id`と`checkpoint_id`を指定してグラフを`invoke`すると、指定された`checkpoint_id`に対応するチェックポイントまでの以前に実行されたステップを再生し、その後のステップのみを新たに実行します。

```python
config = {
    "configurable": {
        "thread_id": "1",
        "checkpoint_id": "0c62ca34-ac19-445d-bbb0-5b4984975b2a"
    }
}

# 指定したチェックポイントから再実行
result = graph.invoke(None, config=config)
```

重要なのは、LangGraphは特定のステップが以前に実行されたかどうかを認識していることです。以前に実行されたステップは再生され、新たに実行されることはありませんが、提供された`checkpoint_id`以降のステップは、新たに実行されます。

### リプレイの詳細

リプレイの詳細については、[タイムトラベルのガイド](https://docs.langchain.com/oss/python/langgraph/time-travel)をご参照ください。

## 状態の更新（Update State）

特定のチェックポイントからグラフを再生するだけでなく、グラフの状態を編集することも可能です。これには`update_state`メソッドを使用します。

### 基本的な使用方法

`update_state`メソッドは以下の引数を受け取ります：

- **`config`**：更新するスレッドを指定する`thread_id`を含める必要があります。`thread_id`のみを渡すと、現在の状態を更新（またはフォーク）します。オプションで`checkpoint_id`フィールドを含めると、選択したチェックポイントをフォークします。
- **`values`**：状態を更新するために使用される値です。この更新は、ノードからの更新と同様に扱われます。つまり、これらの値は、グラフ状態の一部のチャネルに対して定義されている場合、リデューサ関数に渡されます。

### 例：リデューサの動作

以下に例を示します。グラフの状態を以下のスキーマで定義しているとします：

```python
from typing import Annotated
from typing_extensions import TypedDict
from operator import add

class State(TypedDict):
    foo: int
    bar: Annotated[list[str], add]
```

現在のグラフの状態が以下の通りであるとします：

```python
{"foo": 1, "bar": ["a"]}
```

状態を以下のように更新すると：

```python
config = {"configurable": {"thread_id": "1"}}
graph.update_state(config, {"foo": 2, "bar": ["b"]})
```

結果は以下のようになります：

```python
{"foo": 2, "bar": ["a", "b"]}  # "bar"はリデューサにより追加される
```

`update_state`はすべてのチャネルの値を自動的に上書きするわけではなく、リデューサがないチャネルのみを上書きします。

### チェックポイントのフォーク

特定のチェックポイントから状態をフォークすることも可能です：

```python
config = {
    "configurable": {
        "thread_id": "1",
        "checkpoint_id": "previous-checkpoint-id"
    }
}

# 指定したチェックポイントから状態をフォーク
graph.update_state(config, {"foo": 3})
```

## メモリストア（Memory Store）

LangGraphは、メモリストアを通じて永続的なデータ保存をサポートします。これにより、スレッド間でデータを共有したり、長期的なデータ保存が可能となります。

### InMemoryStoreの使用

メモリストアを使用するには、`InMemoryStore`を設定します：

```python
from langgraph.store.memory import InMemoryStore

store = InMemoryStore()
graph = workflow.compile(checkpointer=checkpointer, store=store)
```

### セマンティック検索

メモリストアは、セマンティック検索をサポートしています。これにより、保存されたデータに対して意味的な検索が可能となります。

```python
# データの保存
await store.aput("key", "value")

# セマンティック検索
results = await store.asearch("query", limit=10)
```

### LangGraphでの使用

メモリストアをLangGraphで使用するには、グラフのコンパイル時に`store`パラメータを指定します：

```python
from langgraph.graph import StateGraph
from langgraph.store.memory import InMemoryStore

store = InMemoryStore()
graph = StateGraph(...).compile(
    checkpointer=checkpointer,
    store=store
)
```

これにより、グラフの実行中にデータをメモリストアに保存できます。

## チェックポインタライブラリ（Checkpointer Libraries）

LangGraphは、複数のチェックポインタライブラリをサポートしています。これにより、異なるストレージバックエンドに対してチェックポイントを保存できます。

### MemorySaver（InMemorySaver）

`MemorySaver`（または`InMemorySaver`）は、メモリ内にチェックポイントを保存するシンプルな実装です。開発やテスト時に使用されます。

```python
from langgraph.checkpoint.memory import MemorySaver

checkpointer = MemorySaver()
graph = workflow.compile(checkpointer=checkpointer)
```

**注意**：`MemorySaver`はメモリ内にのみ保存するため、プロセスが終了するとデータは失われます。本番環境では使用しないでください。

### SqliteSaver

`SqliteSaver`は、SQLiteデータベースにチェックポイントを保存します。小規模から中規模のアプリケーションに適しています。

#### セットアップ

```python
from langgraph.checkpoint.sqlite import SqliteSaver

# メモリ内のSQLiteデータベース
checkpointer = SqliteSaver.from_conn_string(":memory:")

# または、ファイルベースのSQLiteデータベース
checkpointer = SqliteSaver.from_conn_string("checkpoints.db")

graph = workflow.compile(checkpointer=checkpointer)
```

#### データベーススキーマ

`SqliteSaver`は、以下のテーブルを作成します：

- **`checkpoints`**：チェックポイントの保存
  - `thread_id`：スレッドID
  - `checkpoint_ns`：チェックポイントの名前空間
  - `checkpoint_id`：チェックポイントID
  - `checkpoint`：チェックポイントデータ（JSON）
  - `metadata`：メタデータ（JSON）
  - `parent_checkpoint_id`：親チェックポイントID
  - `timestamp`：タイムスタンプ

- **`checkpoint_blobs`**：大きなデータの保存
  - `thread_id`：スレッドID
  - `checkpoint_ns`：チェックポイントの名前空間
  - `checkpoint_id`：チェックポイントID
  - `channel`：チャネル名
  - `blob`：大きなデータ（BLOB）

#### 接続文字列の形式

```python
# ファイルパス
checkpointer = SqliteSaver.from_conn_string("checkpoints.db")

# メモリ内
checkpointer = SqliteSaver.from_conn_string(":memory:")

# 絶対パス
checkpointer = SqliteSaver.from_conn_string("/path/to/checkpoints.db")
```

### PostgresSaver

`PostgresSaver`は、PostgreSQLデータベースにチェックポイントを保存します。本番環境やスケーラブルなアプリケーションに適しています。

#### セットアップ

```python
from langgraph.checkpoint.postgres import PostgresSaver

# 接続文字列を使用
checkpointer = PostgresSaver.from_conn_string(
    "postgresql://user:password@localhost:5432/dbname"
)

# または、接続パラメータを使用
checkpointer = PostgresSaver(
    sync_connection="postgresql://user:password@localhost:5432/dbname",
    async_connection="postgresql+asyncpg://user:password@localhost:5432/dbname"
)

graph = workflow.compile(checkpointer=checkpointer)
```

#### データベーススキーマ

`PostgresSaver`は、以下のテーブルを作成します：

- **`checkpoints`**：チェックポイントの保存
- **`checkpoint_blobs`**：大きなデータの保存

#### マイグレーション

`PostgresSaver`は、初回使用時に自動的にテーブルを作成します。既存のデータベースを使用する場合は、マイグレーションスクリプトを実行する必要がある場合があります。

```python
# テーブルの作成
checkpointer.setup()

# または、マイグレーションの実行
checkpointer.migrate()
```

## チェックポインタインターフェース（Checkpointer Interface）

カスタムのチェックポインタを作成する場合、`BaseCheckpointSaver`クラスを継承して実装することができます。

### 基本的な実装

```python
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.base import Checkpoint, CheckpointMetadata
from typing import Optional, Iterator

class CustomCheckpointSaver(BaseCheckpointSaver):
    """カスタムチェックポイントライター"""
    
    def put(
        self,
        config: dict,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: dict,
    ) -> RunnableConfig:
        """チェックポイントを保存"""
        thread_id = config["configurable"]["thread_id"]
        # カスタム実装
        # チェックポイントを保存するロジック
        return config
    
    def get(self, config: dict) -> Optional[Checkpoint]:
        """チェックポイントを取得"""
        thread_id = config["configurable"]["thread_id"]
        # カスタム実装
        # チェックポイントを取得するロジック
        return checkpoint
    
    def list(
        self,
        config: dict,
        filter: Optional[dict] = None,
        before: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Iterator[Checkpoint]:
        """チェックポイントの一覧を取得"""
        thread_id = config["configurable"]["thread_id"]
        # カスタム実装
        # チェックポイントの一覧を取得するロジック
        yield checkpoint
```

### 必須メソッド

カスタムチェックポインタは、以下のメソッドを実装する必要があります：

- **`put`**：チェックポイントを保存します。
- **`get`**：チェックポイントを取得します。
- **`list`**：チェックポイントの一覧を取得します。

## シリアライザ（Serializer）

チェックポイントのシリアライズとデシリアライズをカスタマイズするために、カスタムシリアライザを使用することができます。

### デフォルトのシリアライゼーション

デフォルトでは、LangGraphはPythonの`pickle`モジュールを使用して状態をシリアライズします。これは多くのケースで十分ですが、セキュリティやパフォーマンスの要件に応じて、他のシリアライゼーション手法を検討することができます。

### カスタムシリアライザの実装

```python
from langgraph.checkpoint.serde import Serializer

class CustomSerializer(Serializer):
    """カスタムシリアライザ"""
    
    def serialize(self, obj: Any) -> bytes:
        """オブジェクトをシリアライズ"""
        # カスタム実装（例：JSON、MessagePackなど）
        import json
        return json.dumps(obj).encode()
    
    def deserialize(self, data: bytes) -> Any:
        """データをデシリアライズ"""
        # カスタム実装
        import json
        return json.loads(data.decode())
```

### シリアライザの使用

カスタムシリアライザを使用するには、チェックポインタの作成時に指定します：

```python
from langgraph.checkpoint.memory import MemorySaver

serializer = CustomSerializer()
checkpointer = MemorySaver(serde=serializer)
```

## 暗号化（Encryption）

保存される状態のセキュリティを強化するために、暗号化を導入することができます。これにより、保存されたデータが不正アクセスから保護されます。

### 暗号化の実装

```python
from cryptography.fernet import Fernet
from langgraph.checkpoint.serde import Serializer

class EncryptedSerializer(Serializer):
    """暗号化シリアライザ"""
    
    def __init__(self, key: bytes):
        self.cipher = Fernet(key)
        super().__init__()
    
    def serialize(self, obj: Any) -> bytes:
        """オブジェクトをシリアライズして暗号化"""
        import pickle
        data = pickle.dumps(obj)
        return self.cipher.encrypt(data)
    
    def deserialize(self, data: bytes) -> Any:
        """データを復号化してデシリアライズ"""
        import pickle
        decrypted = self.cipher.decrypt(data)
        return pickle.loads(decrypted)
```

### 暗号化の使用

```python
from cryptography.fernet import Fernet

# 暗号化キーの生成
key = Fernet.generate_key()

# 暗号化シリアライザの作成
serializer = EncryptedSerializer(key)

# チェックポインタの作成
checkpointer = MemorySaver(serde=serializer)
```

## 実装例

### 例1: 基本的な永続化

```python
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig

# MemorySaverの作成
checkpointer = MemorySaver()

# エージェントの構築（P12のコードを参照）
agent = agent_builder.compile(checkpointer=checkpointer)

# スレッドIDの設定
config = RunnableConfig(configurable={"thread_id": "session-1"})

# 最初のメッセージ
result1 = agent.invoke(
    {"messages": [HumanMessage(content="Add 3 and 4.")]},
    config=config
)

# 会話履歴が保持されていることを確認
print("最初の実行完了")
print(f"メッセージ数: {len(result1['messages'])}")

# 続きのメッセージ（会話履歴が自動的に引き継がれる）
result2 = agent.invoke(
    {"messages": [HumanMessage(content="What was the previous result?")]},
    config=config  # 同じスレッドID
)

print("\n続きの実行完了")
print(f"メッセージ数: {len(result2['messages'])}")
# 前の会話履歴が含まれている
```

### 例2: SQLiteを使用した永続化

```python
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
import os

# データベースファイルのパス
db_path = "checkpoints.db"

# 既存のデータベースを削除（テスト用）
if os.path.exists(db_path):
    os.remove(db_path)

# SqliteSaverの作成
checkpointer = SqliteSaver.from_conn_string(db_path)

# エージェントに永続化を設定
agent = agent_builder.compile(checkpointer=checkpointer)

# スレッドIDの設定
config = RunnableConfig(configurable={"thread_id": "user-123"})

# エージェントの実行
result = agent.invoke(
    {"messages": [HumanMessage(content="Add 3 and 4.")]},
    config=config
)

print("実行完了")
print(f"データベース: {db_path}")

# 状態の確認
state = agent.get_state(config)
print(f"チェックポイント数: {len(state.history) if hasattr(state, 'history') else 'N/A'}")
```

### 例3: 会話履歴の管理

```python
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig

checkpointer = MemorySaver()
agent = agent_builder.compile(checkpointer=checkpointer)

# ユーザーごとのスレッドID
user_threads = {
    "user-1": "thread-user-1",
    "user-2": "thread-user-2"
}

# ユーザー1の会話
config1 = RunnableConfig(configurable={"thread_id": user_threads["user-1"]})
result1 = agent.invoke(
    {"messages": [HumanMessage(content="Hello")]},
    config=config1
)

# ユーザー2の会話（独立した会話履歴）
config2 = RunnableConfig(configurable={"thread_id": user_threads["user-2"]})
result2 = agent.invoke(
    {"messages": [HumanMessage(content="Hello")]},
    config=config2
)

# 各ユーザーの会話履歴は独立している
state1 = agent.get_state(config1)
state2 = agent.get_state(config2)

print(f"ユーザー1のメッセージ数: {len(state1.values['messages'])}")
print(f"ユーザー2のメッセージ数: {len(state2.values['messages'])}")
```

### 例4: リプレイの使用

```python
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables import RunnableConfig

checkpointer = MemorySaver()
agent = agent_builder.compile(checkpointer=checkpointer)

config = RunnableConfig(configurable={"thread_id": "replay-example"})

# 最初の実行
result1 = agent.invoke(
    {"messages": [HumanMessage(content="What is 2+2?")]},
    config=config
)

# 状態履歴を取得
history = agent.get_state_history(config)
checkpoint_id = None

for checkpoint in history:
    print(f"チェックポイントID: {checkpoint.id}")
    checkpoint_id = checkpoint.id

# 特定のチェックポイントから再実行
if checkpoint_id:
    replay_config = RunnableConfig(
        configurable={
            "thread_id": "replay-example",
            "checkpoint_id": checkpoint_id
        }
    )
    result2 = agent.invoke(None, config=replay_config)
```

### 例5: 状態の更新

```python
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables import RunnableConfig

checkpointer = MemorySaver()
agent = agent_builder.compile(checkpointer=checkpointer)

config = RunnableConfig(configurable={"thread_id": "update-example"})

# 最初の実行
result1 = agent.invoke(
    {"messages": [HumanMessage(content="Hello")]},
    config=config
)

# 状態を更新
agent.update_state(
    config,
    {"messages": [HumanMessage(content="Updated message")]}
)

# 更新後の状態を確認
state = agent.get_state(config)
print(f"更新後のメッセージ数: {len(state.values['messages'])}")
```

## ベストプラクティス

### 1. スレッドIDの設計

スレッドIDは、以下のような形式を推奨します：

```python
# ユーザーID + セッションID
thread_id = f"user-{user_id}-session-{session_id}"

# または、UUIDを使用
import uuid
thread_id = str(uuid.uuid4())
```

### 2. データベースの選択

用途に応じて適切なデータベースを選択します：

- **開発・テスト**: `MemorySaver`（メモリ内）
- **小規模アプリ**: `SqliteSaver`（ファイルベース）
- **本番環境**: `PostgresSaver`（スケーラブル）

### 3. チェックポイントのクリーンアップ

古いチェックポイントを定期的に削除します。

```python
# 古いチェックポイントを削除（実装例）
def cleanup_old_checkpoints(checkpointer, days=30):
    """30日以上古いチェックポイントを削除"""
    # 実装
    pass
```

### 4. エラーハンドリング

永続化のエラーを適切に処理します。

```python
try:
    result = agent.invoke(initial_state, config=config)
except Exception as e:
    print(f"永続化エラー: {e}")
    # フォールバック処理
```

### 5. パフォーマンスの最適化

大量のチェックポイントを扱う場合は、以下の点を考慮します：

- チェックポイントのサイズを最小限に抑える
- 定期的に古いチェックポイントを削除する
- インデックスを適切に設定する（データベースの場合）

## まとめ

永続化により、以下のことが可能になります：

1. **会話履歴の保持**: ユーザーとの会話を保存し、次回に引き継ぐ
2. **エラーからの復旧**: エラー発生時に状態を復元して再開
3. **長時間実行**: 長時間実行されるエージェントの状態を保存
4. **マルチセッション**: 複数のセッションで状態を共有
5. **タイムトラベル**: 過去の状態から実行を再開
6. **ヒューマン・イン・ザ・ループ**: 人間の介入を可能にする

適切に永続化を実装することで、より堅牢で実用的なエージェントシステムを構築できます。

## 次のステップ

- [P17: Functional API](./P17_functional_api.md): 関数型APIの使用方法
- [P18: Interrupts](./P18_interrupts.md): 人間の介入（Human-in-the-loop）
- [P19: Subgraphs](./P19_subgraphs.md): サブグラフの概念
- [P20: Memory](./P20_memory.md): メモリ管理
- [P21: Durable Execution](./P21_durable_execution.md): 耐久性のある実行

---

ここから gemini の解説

---

Cursorの解説は専門用語が多く、初めての方には少しイメージしにくいですよね。
LangGraphの永続化を、一言でいうと**「ゲームのセーブ機能」**に例えると非常に分かりやすくなります。

それぞれの用語を、かみ砕いて解説しますね。

---

### 1. 状態の永続化（Persistence）とは何？

**「プログラムが終了したりエラーが起きたりしても、これまでの会話や進捗を消さずに取っておくこと」**です。

通常、AIとの会話プログラムは終了すると中身が消えてしまいます。しかし、永続化（セーブ）しておくことで、数日後に同じ会話を再開したり、エラーで止まった場所からやり直したりできるようになります。

### 2. チェックポインタ（Checkpointer）とは何？

**「セーブを実行する『レコーダー（記録係）』」**のことです。

LangGraphの処理が進むたびに、このチェックポインタが「今の状態はこうです」とノートに書き留める役割を担います。

### 3. 永続化レイヤーとは何？

**「データを保存するための『専用の保管場所（土台）』」**のことです。

「レイヤー（層）」という言葉は、システムの中で「保存を担当する階層」という意味で使われます。メモリ（一時的）やデータベース（長期的）など、保存先がどこであっても、それを管理する仕組み全体を指します。

### 4. スーパーステップ（Super-step）とは何？

**「AIが一区切りの処理を終える『1ターン』」**のことです。

LangGraphは、複数のAIエージェントが連携して動きます。

1. エージェントAが考える
2. エージェントBが実行する
3. 結果をまとめる
この「一連のまとまった工程」が1つのスーパーステップです。LangGraphはこの**1ターンが終わるごとに自動でセーブ**してくれます。

### 5. スレッド（Thread）とは何？

**「セーブデータの『スロット（保存枠）』」**のことです。

ゲームで「セーブデータ1」「セーブデータ2」と分けるように、ユーザーAさんとの会話は「スレッドA」、Bさんとの会話は「スレッドB」という風に、ID（Thread ID）をつけて管理します。これによって、複数の会話を混ざらずに並行して進められます。

### 6. スレッドに保存されるとはどういう事？

**「特定のID（スレッドID）に関連付けて、その時点の記憶をデータベースに書き込む」**という意味です。

「スレッドに保存」されているおかげで、次回プログラムを動かすときに「スレッドID：123」を指定するだけで、前回中断した「123番の続き」からAIが話し始めることができるようになります。

---

### まとめ：イメージ図

| 用語 | ゲームに例えると |
| --- | --- |
| **永続化** | セーブすることそのもの |
| **チェックポインタ** | セーブボタン（または自動セーブ機能） |
| **スーパーステップ** | ステージクリアなどの「区切り」 |
| **スレッド** | セーブデータのスロット（ファイル1、ファイル2...） |

> **💡 これができると何が嬉しいの？**
> AIが途中で間違えたときに「1つ前のセーブポイント（スーパーステップ）に戻ってやり直す（タイムトラベル）」といった高度な操作ができるようになります。

この解説で、少しイメージは湧きましたでしょうか？
もし具体的なコードの書き方や、特定の用語についてもっと深掘りしたい場合は、続けてお手伝いします！

---

ここでいう永続化（セーブ）の対象は何ですか？

グラフのステートだけですか？
それとも、過去のノードの結果やエッジの遷移状態等も保存されますか？

---

結論から言うと、**「グラフのステート（State）の履歴すべて」**が保存されます。

単に「今の最新の状態」を上書き保存するのではなく、**「どのノードを通って、ステートがどう変化したか」という全プロセスのスナップショット**が保存されるのが LangGraph の永続化の凄いところです。

具体的に何が保存されているのか、詳しく解説します。

### 1. 保存される対象：チェックポイント

チェックポインタが保存するデータの塊を「チェックポイント」と呼びますが、これには以下の情報が含まれます。

* **ステート（State）の全内容**:
ユーザーが定義した TypedDict などのステートに入っている現在の値すべてです。
* **ノードの実行結果**:
どのノードが実行され、その結果ステートのどの変数がどう更新されたかという差分情報が含まれます。
* **次のノードの情報（Next Steps）**:
次にどのノードが実行される予定か、エッジの条件分岐の結果、次にどこへ進むべきかという「予約チケット」のような情報も保存されます。

### 2. 「過去の履歴」も残る（タイムトラベル機能）

「最新の状態だけ」ではなく、**ステップごとの履歴**が保存されます。

* **エッジの遷移状態**: 「ノードAからノードBへ移動した」という履歴が残ります。
* **過去の状態**: 5ステップ前のステートがどうだったか、という情報もスレッド内に保持されています。

これによって、以下のような操作が可能になります。

* **タイムトラベル**: 「3ステップ前の状態に戻って、別の回答を試させる」
* **フォーク（分岐）**: 「過去のある地点から、別の選択肢を選ばせてシミュレーションする」

### 3. 具体的なイメージ

例えば、「検索」→「要約」というグラフがある場合、保存されるのは以下の情報のセットです。

1. **ステップ1終了時**: 「検索ノード」が終わった直後のステート（検索結果が入っている状態）＋「次は要約ノードに行く」という予定。
2. **ステップ2終了時**: 「要約ノード」が終わった直後のステート（要約文が入っている状態）＋「次は終了（END）に行く」という予定。

### まとめ

保存されるのは、**「その時点でのステートの完全なコピー」＋「そこに至るまでの文脈（どのノードが動いたか）」**です。

ですので、ご質問にある「過去のノードの結果やエッジの遷移状態」も、**「各ステップのステートの履歴」という形で実質的にすべて保存されている**と考えて間違いありません。

これにより、プログラムが途中でクラッシュしても、完全に同じ地点、同じ文脈から再開（レジューム）できる仕組みになっています。

---

という事は、この例では、

1. 最初～グラフの実行　までは、永続化の作法（チェックポイント付でグラフを作って実行すれば、勝手に永続化される）   
2. 状態の取得以降は、そのセーブ内容の確認　と考えて良いですか？

---

はい、その認識で完璧です！

提示されたコードの流れを整理すると、まさに**「自動録画の設定」**と**「録画内容の再生・確認」**という構成になっています。

より正確に、各セクションが何をしているのかを補足します。

---

### 1. 永続化の作法（セーブの設定と実行）

「5. グラフの実行」までの工程は、一度設定してしまえばあとはLangGraphが裏側で自動的にセーブを行ってくれるフェーズです。

* **チェックポインタ（MemorySaver）の作成**: 「セーブデータの書き込み先」を準備します。
* **コンパイル（compile）**: グラフに「実行するたびにセーブしてね」という命令を組み込みます。
* **スレッドIDの設定**: 「セーブデータのスロット番号（名前）」を決めます。
* **グラフの実行（invoke）**: ここで実際に処理が動き、**各ノードが終わるたびに（スーパーステップごとに）自動でチェックポイントが保存**されます。

### 2. セーブ内容の確認（データの取得）

「6. 状態の取得」以降は、保存されたデータを引っ張り出して中身をのぞき見ているフェーズです。

* **`get_state`**: 「一番新しいセーブデータ」を1つ取り出しています。
* **`get_state_history`**: 「これまでの全セーブ履歴（アルバム）」をまるごと取り出しています。

---

### この例で特に注目すべきポイント

このコードを動かすと、**「なぜ永続化が必要なのか」**がわかる面白いポイントが2つあります。

#### ① `bar` リストの変化（Reducersの動き）

`State` の定義で `bar: Annotated[list[str], add]` となっています。

* `node_a` で `["a"]` を返す
* `node_b` で `["b"]` を返す
セーブデータを確認すると、`bar` の値は上書きされず `["a", "b"]` と積み上がっているはずです。永続化層がこの「積み上げ」の履歴を正確に保持していることがわかります。

#### ② `next`（次に実行するノード）の意味

セーブデータの中には「次にどこへ進むべきか」という情報（`state.next`）も入っています。
もし `node_a` が終わった直後にプログラムが強制終了しても、このセーブデータから再開すれば、AIは迷わず「次は `node_b` から始めればいいんだな」と判断できるのです。

---

### 次に試してみると面白いこと

このコードの最後に、以下のような処理を付け加えてみると、永続化の真価がさらにわかります。

> **「同じスレッドIDを使って、もう一度 `graph.invoke` を呼んでみる」**
> すると、また最初から実行されるのではなく、**前回の `["a", "b"]` を持った状態（前回の続き）からスタート**します。

もしよろしければ、この「続きから実行される様子」を確認するための追加コード案を作成しましょうか？

---

bar: Annotated[list[str], add]  # リデューサを使用してリストに追加

を解説してください。

1. Python が不得手で、Annotated[list[str], add]が全く理解できません。
2. リデューサはLangGraphにおける、なんらかのパターン見たいですね。

---

Pythonの標準的な書き方とは少し違うため、最初は戸惑いますよね。
これは**「データの更新ルールを予約する」**ためのLangGraph特有の書き方です。

---

### 1. `Annotated[list[str], add]` とは何か？

一言でいうと、**「このデータは上書きせず、足し算（追加）で更新してね」**という指示です。

通常、変数は新しい値を代入すると前の値は消えてしまいます（上書き）。
しかし、会話履歴やログなどの場合、前のデータを残したまま末尾に追加していきたいですよね。それを実現するのがこの書き方です。

中身を分解するとこうなります：

* **`list[str]`**: データの型（文字列のリストであること）を指定しています。
* **`add`**: **「どうやって更新するか」のルール**です。Pythonの標準ライブラリ（operator.add）で、リストに対して使うと「リスト同士を結合する（`[1] + [2] = [1, 2]`）」という動きをします。
* **`Annotated[...]`**: Pythonの仕組みで、「型（list）」に「追加情報（addというルール）」を付箋のように貼り付けるための書き方です。

---

### 2. リデューサ（Reducer）はどんなパターン？

ご推察の通り、リデューサはLangGraphにおける非常に重要な**「状態更新のパターン」**です。

#### なぜ「リデューサ」が必要なのか？

LangGraphは複数のノードが並行して動いたり、何度も同じノードを通ったりします。
その際、単純な上書きだと、**「他のノードが書き込んだ大切な情報を消してしまう」**という事故が起きます。

リデューサを設定しておくと、LangGraphは以下のように動きます：

1. **現在の値**を確認する。
2. ノードから返ってきた**新しい値**を受け取る。
3. 指定されたルール（今回の場合は `add`）を使って、**「現在」と「新」を合体**させる。
4. 合体した結果を**新しい状態（State）**として保存する。

#### 具体的な動きの例

今回のコードを例にすると、以下のようになります。

1. **初期状態**: `bar` は空っぽ `[]`
2. **node_a が終了**: `{"bar": ["a"]}` を返す。
* 計算： `[]` + `["a"]` = `["a"]`
* Stateは `["a"]` になる。


3. **node_b が終了**: `{"bar": ["b"]}` を返す。
* 計算： `["a"]` + `["b"]` = `["a", "b"]`
* Stateは `["a", "b"]` になる。



> **もしリデューサ（add）がなかったら？**
> `node_b` が終わったとき、`bar` は最後に来た `["b"]` だけになってしまい、`"a"` は消えてしまいます。

---

### まとめ

* **Annotated**: 「型」と「更新ルール」をセットにするための封筒。
* **add**: リストを繋げる（結合する）という具体的なルール。
* **リデューサ**: 「新しいデータが来たら、今のデータとどうやって混ぜ合わせるか？」を決める仕組み。

ちなみに、`foo: str` の方にはこれが付いていませんよね？
そのため、`foo` は `node_b` が終わった瞬間に、`node_a` が書いた `"a"` は消えて `"b"` に**上書き**されます。

この「上書き」と「追加（リデューサ）」の使い分けが、LangGraphで賢いAIを作るコツになります。

次は、実際にこの「add」が動いている様子を、コードの結果から確認してみますか？