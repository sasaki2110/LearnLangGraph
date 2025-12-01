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

## 基本的なメモリ管理

### 状態によるメモリ管理

最も基本的なメモリ管理は、**状態（State）**を使用することです。

```python
class MessagesState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]  # 会話履歴
    context: dict  # コンテキスト情報
    user_preferences: dict  # ユーザー設定
```

### 会話履歴の保持

`operator.add`を使用することで、メッセージが自動的に追加されます。

```python
class MessagesState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]

def llm_call(state: MessagesState) -> dict:
    """LLM呼び出し（会話履歴を含む）"""
    # 会話履歴が自動的に含まれる
    response = model.invoke(state["messages"])
    return {"messages": [response]}  # 新しいメッセージが追加される
```

## 実装例

### 例1: 基本的な会話履歴の管理

```python
from langgraph.graph import StateGraph, START, END
from langchain.messages import HumanMessage, AIMessage

class ConversationState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    conversation_summary: str  # 会話の要約

def llm_call(state: ConversationState) -> dict:
    """LLM呼び出し（会話履歴を使用）"""
    # 会話履歴を使用してLLMを呼び出す
    response = model.invoke(state["messages"])
    return {"messages": [response]}

def summarize_conversation(state: ConversationState) -> dict:
    """会話の要約を生成"""
    # 会話履歴を要約
    summary = summarize(state["messages"])
    return {"conversation_summary": summary}

# グラフの構築
graph = StateGraph(ConversationState)
graph.add_node("llm_call", llm_call)
graph.add_node("summarize", summarize_conversation)

graph.add_edge(START, "llm_call")
graph.add_edge("llm_call", "summarize")
graph.add_edge("summarize", END)

agent = graph.compile()

# 実行（会話履歴が保持される）
result1 = agent.invoke({
    "messages": [HumanMessage(content="Hello")],
    "conversation_summary": ""
})

result2 = agent.invoke({
    "messages": [HumanMessage(content="What did I say before?")],
    "conversation_summary": result1["conversation_summary"]
})
# 前の会話履歴が含まれている
```

### 例2: コンテキスト情報の管理

```python
class ContextState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    context: dict  # コンテキスト情報
    user_info: dict  # ユーザー情報

def update_context(state: ContextState) -> dict:
    """コンテキスト情報を更新"""
    last_message = state["messages"][-1]
    
    # コンテキスト情報を抽出
    new_context = extract_context(last_message)
    
    # 既存のコンテキストとマージ
    updated_context = {**state.get("context", {}), **new_context}
    
    return {"context": updated_context}

def llm_call_with_context(state: ContextState) -> dict:
    """コンテキスト情報を含めてLLMを呼び出す"""
    # コンテキスト情報をシステムメッセージに追加
    system_message = SystemMessage(
        content=f"Context: {state.get('context', {})}"
    )
    
    messages = [system_message] + state["messages"]
    response = model.invoke(messages)
    
    return {"messages": [response]}

# グラフの構築
graph = StateGraph(ContextState)
graph.add_node("update_context", update_context)
graph.add_node("llm_call", llm_call_with_context)

graph.add_edge(START, "update_context")
graph.add_edge("update_context", "llm_call")
graph.add_edge("llm_call", END)

agent = graph.compile()
```

### 例3: 長期メモリとの統合

```python
from langgraph.checkpoint.sqlite import SqliteSaver

class LongTermMemoryState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    user_id: str
    learned_facts: list  # 学習した事実

def learn_from_conversation(state: LongTermMemoryState) -> dict:
    """会話から学習した事実を抽出"""
    # 会話から重要な事実を抽出
    facts = extract_facts(state["messages"])
    
    # 既存の事実とマージ
    existing_facts = state.get("learned_facts", [])
    updated_facts = existing_facts + facts
    
    return {"learned_facts": updated_facts}

def use_learned_facts(state: LongTermMemoryState) -> dict:
    """学習した事実を使用してLLMを呼び出す"""
    # 学習した事実をコンテキストに追加
    facts_context = "\n".join(state.get("learned_facts", []))
    
    system_message = SystemMessage(
        content=f"Learned facts: {facts_context}"
    )
    
    messages = [system_message] + state["messages"]
    response = model.invoke(messages)
    
    return {"messages": [response]}

# 永続化の設定
checkpointer = SqliteSaver.from_conn_string("memory.db")

# グラフの構築
graph = StateGraph(LongTermMemoryState)
graph.add_node("learn", learn_from_conversation)
graph.add_node("llm_call", use_learned_facts)

graph.add_edge(START, "learn")
graph.add_edge("learn", "llm_call")
graph.add_edge("llm_call", END)

agent = graph.compile(checkpointer=checkpointer)

# 実行（長期メモリに保存される）
config = {"configurable": {"thread_id": f"user-{user_id}"}}

result = agent.invoke(
    {
        "messages": [HumanMessage(content="I like Python")],
        "user_id": user_id,
        "learned_facts": []
    },
    config=config
)

# 次回の実行時にも学習した事実が利用可能
result2 = agent.invoke(
    {
        "messages": [HumanMessage(content="What do I like?")],
        "user_id": user_id,
        "learned_facts": []  # 永続化から読み込まれる
    },
    config=config
)
```

## メモリの最適化

### 1. 会話履歴の要約

長い会話履歴は、要約してメモリを節約します。

```python
def summarize_old_messages(state: MessagesState) -> dict:
    """古いメッセージを要約"""
    messages = state["messages"]
    
    # 最新のN件を保持し、それ以前を要約
    if len(messages) > 10:
        old_messages = messages[:-10]
        new_messages = messages[-10:]
        
        summary = summarize_messages(old_messages)
        summary_message = SystemMessage(content=f"Previous conversation: {summary}")
        
        return {"messages": [summary_message] + new_messages}
    
    return {"messages": messages}
```

### 2. 重要情報の抽出

会話から重要な情報のみを抽出して保存します。

```python
def extract_important_info(state: MessagesState) -> dict:
    """重要な情報を抽出"""
    messages = state["messages"]
    
    # 重要な情報を抽出
    important_info = {
        "user_name": extract_user_name(messages),
        "preferences": extract_preferences(messages),
        "key_facts": extract_key_facts(messages)
    }
    
    return {"important_info": important_info}
```

### 3. メモリのクリーンアップ

不要な情報を定期的に削除します。

```python
def cleanup_memory(state: MessagesState) -> dict:
    """メモリのクリーンアップ"""
    # 古い情報を削除
    cleaned_context = {
        k: v for k, v in state.get("context", {}).items()
        if is_recent(k)  # 最近の情報のみ保持
    }
    
    return {"context": cleaned_context}
```

## ベストプラクティス

### 1. メモリの適切なサイズ管理

メモリが大きくなりすぎないように、適切に管理します。

```python
# 会話履歴の最大長を設定
MAX_MESSAGES = 50

def limit_messages(state: MessagesState) -> dict:
    """メッセージ数を制限"""
    messages = state["messages"]
    if len(messages) > MAX_MESSAGES:
        # 古いメッセージを要約
        old_messages = messages[:-MAX_MESSAGES]
        summary = summarize_messages(old_messages)
        return {"messages": [SystemMessage(content=summary)] + messages[-MAX_MESSAGES:]}
    return {"messages": messages}
```

### 2. 関連情報のグループ化

関連する情報をグループ化して管理します。

```python
class OrganizedMemoryState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    user_profile: dict  # ユーザープロフィール
    conversation_context: dict  # 会話コンテキスト
    task_history: list  # タスク履歴
```

### 3. メモリの検証

メモリの内容を定期的に検証し、整合性を保ちます。

```python
def validate_memory(state: MessagesState) -> dict:
    """メモリの検証"""
    # 矛盾する情報を検出
    conflicts = detect_conflicts(state)
    
    if conflicts:
        # 矛盾を解決
        resolved_state = resolve_conflicts(state, conflicts)
        return resolved_state
    
    return state
```

## まとめ

メモリ管理により、以下のことが可能になります：

1. **会話履歴の保持**: 過去の会話を参照できる
2. **コンテキストの維持**: 関連情報を保持できる
3. **学習**: 過去の経験から学習できる
4. **パーソナライゼーション**: ユーザーごとの情報を保持できる

適切にメモリを管理することで、より賢く、パーソナライズされたエージェントを構築できます。

## 次のステップ

- [P21: Durable Execution](./P21_durable_execution.md): 長時間実行の管理
- [P16: Persistence](./P16_persistence.md): 状態の永続化
- [P00: Roadmap](./P00_roadmap.md): 学習ロードマップに戻る

