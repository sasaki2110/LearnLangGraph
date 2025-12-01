# Persistence

このドキュメントでは、LangGraphにおける状態の永続化（Persistence）について解説します。

公式ドキュメント: https://docs.langchain.com/oss/python/langgraph/persistence

## 概要

永続化（Persistence）は、エージェントの状態を**データベースやストレージに保存**し、後で**復元**できるようにする機能です。これにより、以下のことが可能になります：

1. **会話履歴の保持**: ユーザーとの会話を保存し、次回に引き継ぐ
2. **エラーからの復旧**: エラー発生時に状態を復元して再開
3. **長時間実行**: 長時間実行されるエージェントの状態を保存
4. **マルチセッション**: 複数のセッションで状態を共有

## 永続化の基本概念

### チェックポイント（Checkpoint）

**チェックポイント**は、エージェントの状態のスナップショットです。

- 各ノードの実行後に自動的に作成される
- 状態の完全なコピーが保存される
- 任意のチェックポイントから実行を再開できる

### チェックポイントライター（Checkpoint Writer）

**チェックポイントライター**は、チェックポイントを保存・読み込むためのインターフェースです。

LangGraphでは、以下のような実装が提供されています：

- **MemorySaver**: メモリ内に保存（開発・テスト用）
- **SqliteSaver**: SQLiteデータベースに保存
- **PostgresSaver**: PostgreSQLデータベースに保存

## 基本的な使用方法

### MemorySaverの使用

開発やテストでは、`MemorySaver`を使用してメモリ内に保存します。

```python
from langgraph.checkpoint.memory import MemorySaver

# MemorySaverの作成
memory = MemorySaver()

# エージェントに永続化を設定
agent = agent_builder.compile(checkpointer=memory)
```

### チェックポイントの保存と読み込み

```python
from langgraph.graph import StateGraph

# エージェントの実行（自動的にチェックポイントが保存される）
config = {"configurable": {"thread_id": "thread-1"}}
result = agent.invoke(
    {"messages": [HumanMessage(content="Hello")]},
    config=config
)

# チェックポイントの読み込み
state = agent.get_state(config)
print(state.values)  # 保存された状態
```

## SQLiteを使用した永続化

### セットアップ

```python
from langgraph.checkpoint.sqlite import SqliteSaver

# SQLiteSaverの作成
checkpointer = SqliteSaver.from_conn_string(":memory:")  # メモリ内
# または
checkpointer = SqliteSaver.from_conn_string("checkpoints.db")  # ファイル

# エージェントに永続化を設定
agent = agent_builder.compile(checkpointer=checkpointer)
```

### スレッドIDの使用

各会話セッションには、一意の**スレッドID**を割り当てます。

```python
# スレッドIDの設定
config = {"configurable": {"thread_id": "user-123-session-1"}}

# エージェントの実行
result = agent.invoke(
    {"messages": [HumanMessage(content="Hello")]},
    config=config
)

# 同じスレッドIDで続きから実行
result = agent.invoke(
    {"messages": [HumanMessage(content="続きの質問")]},
    config=config  # 同じスレッドIDを使用
)
```

## 実装例

### 例1: 基本的な永続化

```python
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END

# MemorySaverの作成
memory = MemorySaver()

# エージェントの構築（P12のコードを参照）
agent = agent_builder.compile(checkpointer=memory)

# スレッドIDの設定
config = {"configurable": {"thread_id": "session-1"}}

# 最初のメッセージ
result1 = agent.invoke(
    {"messages": [HumanMessage(content="Add 3 and 4.")], "llm_calls": 0},
    config=config
)

# 会話履歴が保持されていることを確認
print("最初の実行完了")
print(f"メッセージ数: {len(result1['messages'])}")

# 続きのメッセージ（会話履歴が自動的に引き継がれる）
result2 = agent.invoke(
    {"messages": [HumanMessage(content="What was the previous result?")], "llm_calls": 0},
    config=config  # 同じスレッドID
)

print("\n続きの実行完了")
print(f"メッセージ数: {len(result2['messages'])}")
# 前の会話履歴が含まれている
```

### 例2: SQLiteを使用した永続化

```python
from langgraph.checkpoint.sqlite import SqliteSaver
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
config = {"configurable": {"thread_id": "user-123"}}

# エージェントの実行
result = agent.invoke(
    {"messages": [HumanMessage(content="Add 3 and 4.")], "llm_calls": 0},
    config=config
)

print("実行完了")
print(f"データベース: {db_path}")

# 状態の確認
state = agent.get_state(config)
print(f"チェックポイント数: {len(state.history)}")
```

### 例3: 会話履歴の管理

```python
from langgraph.checkpoint.memory import MemorySaver

memory = MemorySaver()
agent = agent_builder.compile(checkpointer=memory)

# ユーザーごとのスレッドID
user_threads = {
    "user-1": "thread-user-1",
    "user-2": "thread-user-2"
}

# ユーザー1の会話
config1 = {"configurable": {"thread_id": user_threads["user-1"]}}
result1 = agent.invoke(
    {"messages": [HumanMessage(content="Hello")], "llm_calls": 0},
    config=config1
)

# ユーザー2の会話（独立した会話履歴）
config2 = {"configurable": {"thread_id": user_threads["user-2"]}}
result2 = agent.invoke(
    {"messages": [HumanMessage(content="Hello")], "llm_calls": 0},
    config=config2
)

# 各ユーザーの会話履歴は独立している
state1 = agent.get_state(config1)
state2 = agent.get_state(config2)

print(f"ユーザー1のメッセージ数: {len(state1.values['messages'])}")
print(f"ユーザー2のメッセージ数: {len(state2.values['messages'])}")
```

## チェックポイントの操作

### チェックポイントの取得

```python
# 最新の状態を取得
state = agent.get_state(config)

# 特定のチェックポイントを取得
state = agent.get_state(config, as_of=checkpoint_id)
```

### チェックポイントの一覧取得

```python
# チェックポイントの履歴を取得
history = agent.get_state_history(config)

for checkpoint in history:
    print(f"チェックポイントID: {checkpoint.id}")
    print(f"タイムスタンプ: {checkpoint.ts}")
    print(f"状態: {checkpoint.values}")
```

### チェックポイントからの再開

```python
# 特定のチェックポイントから再開
state = agent.get_state(config, as_of=checkpoint_id)

# その状態から実行を再開
result = agent.invoke(
    {"messages": [HumanMessage(content="Continue")]},
    config=config
)
```

## データベーススキーマ

### SQLiteのスキーマ

SQLiteSaverは、以下のテーブルを作成します：

- **checkpoints**: チェックポイントの保存
- **checkpoint_blobs**: 大きなデータの保存

### カスタムチェックポイントライター

独自のチェックポイントライターを実装することも可能です。

```python
from langgraph.checkpoint.base import BaseCheckpointSaver

class CustomCheckpointSaver(BaseCheckpointSaver):
    """カスタムチェックポイントライター"""
    
    def put(self, config, checkpoint, metadata, new_versions):
        """チェックポイントを保存"""
        # カスタム実装
        pass
    
    def get(self, config):
        """チェックポイントを取得"""
        # カスタム実装
        pass
    
    def list(self, config, filter=None):
        """チェックポイントの一覧を取得"""
        # カスタム実装
        pass
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

- **開発・テスト**: MemorySaver（メモリ内）
- **小規模アプリ**: SqliteSaver（ファイルベース）
- **本番環境**: PostgresSaver（スケーラブル）

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

## まとめ

永続化により、以下のことが可能になります：

1. **会話履歴の保持**: ユーザーとの会話を保存し、次回に引き継ぐ
2. **エラーからの復旧**: エラー発生時に状態を復元して再開
3. **長時間実行**: 長時間実行されるエージェントの状態を保存
4. **マルチセッション**: 複数のセッションで状態を共有

適切に永続化を実装することで、より堅牢で実用的なエージェントシステムを構築できます。

## 次のステップ

- [P17: Functional API](./P17_functional_api.md): 関数型APIの使用方法
- [P18: Interrupts](./P18_interrupts.md): 人間の介入（Human-in-the-loop）
- [P19: Subgraphs](./P19_subgraphs.md): サブグラフの概念

