# Thinking in LangGraph

このドキュメントでは、LangGraphの設計思想と、グラフベースの思考法について解説します。

公式ドキュメント: https://docs.langchain.com/oss/python/langgraph/thinking-in-langgraph

## 概要

LangGraphは、**グラフベースの思考法**を採用したエージェントオーケストレーションフレームワークです。従来の線形処理ではなく、**ノードとエッジで構成されるグラフ**としてエージェントを設計することで、より柔軟で強力なシステムを構築できます。

## なぜグラフなのか？

### 従来のアプローチの問題点

従来のエージェント実装では、以下のような問題がありました：

1. **線形処理の限界**: 処理が順番に実行されるため、複雑な分岐やループが難しい
2. **状態管理の複雑さ**: 状態が散在し、追跡が困難
3. **デバッグの難しさ**: 実行フローが不明確で、問題の特定が困難

### グラフベースのアプローチの利点

LangGraphのグラフベースアプローチにより、以下の利点が得られます：

1. **視覚的な理解**: グラフ構造により、エージェントの動作が直感的に理解できる
2. **柔軟な制御フロー**: 条件分岐、ループ、並列処理を自然に表現できる
3. **明確な状態管理**: 状態がグラフ全体で共有され、追跡が容易
4. **デバッグの容易さ**: 実行パスが明確で、問題の特定が容易

## グラフの基本概念

### ノード（Node）

**ノード**は、グラフ内で実行される処理単位です。

- 各ノードは**関数**として実装されます
- ノードは**状態を受け取り、状態を返します**
- ノードは独立しており、再利用可能です

```python
def my_node(state: dict) -> dict:
    """ノード関数の例"""
    # 状態を処理
    result = process(state)
    # 更新された状態を返す
    return {"key": result}
```

### エッジ（Edge）

**エッジ**は、ノード間の接続を定義します。

- **通常エッジ**: 無条件で次のノードへ遷移
- **条件付きエッジ**: 状態に基づいて動的に次のノードを決定

```python
# 通常エッジ
graph.add_edge("node_a", "node_b")

# 条件付きエッジ
graph.add_conditional_edges(
    "node_a",
    should_continue,  # 条件判定関数
    ["node_b", "node_c"]  # 可能な遷移先
)
```

### 状態（State）

**状態**は、グラフ全体で共有されるデータです。

- 各ノードは状態を読み取り、更新できます
- 状態は型安全に定義されます（TypedDict）
- 状態の更新は自動的にマージされます

```python
class MyState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    counter: int
```

## グラフベースの思考法

### 1. プロセスをノードに分解する

エージェントの処理を、**独立したノード**に分解します。

**例: 計算エージェント**

```
ユーザー入力 → LLM分析 → ツール実行 → LLM回答生成 → 出力
```

これをノードに分解すると：

- `llm_call`: LLMが入力を分析し、ツールを呼び出すか判断
- `tool_node`: ツールを実行
- `should_continue`: 次のステップを決定

### 2. ノード間の関係をエッジで表現する

ノード間の関係を、**エッジ**で明確に定義します。

```python
# 開始からLLM呼び出しへ
graph.add_edge(START, "llm_call")

# LLM呼び出しから条件分岐
graph.add_conditional_edges(
    "llm_call",
    should_continue,
    ["tool_node", END]
)

# ツール実行後、再度LLM呼び出しへ
graph.add_edge("tool_node", "llm_call")
```

### 3. 状態でデータの流れを管理する

状態を通じて、ノード間でデータを共有します。

```python
def llm_call(state: MessagesState) -> dict:
    # 状態からメッセージを取得
    messages = state["messages"]
    
    # LLMを呼び出し
    response = model.invoke(messages)
    
    # 状態を更新して返す
    return {"messages": [response]}
```

## エージェント設計の原則

### 1. 単一責任の原則

各ノードは、**一つの明確な責任**を持つべきです。

**良い例**:
- `llm_call`: LLMを呼び出す
- `tool_node`: ツールを実行する
- `validate_input`: 入力を検証する

**悪い例**:
- `process_everything`: すべての処理を行う（責任が不明確）

### 2. 状態の最小化

状態には、**必要な情報のみ**を含めます。

```python
# 良い例: 必要な情報のみ
class MessagesState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    llm_calls: int

# 悪い例: 不要な情報も含む
class BloatedState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    llm_calls: int
    temp_data: dict  # 不要な一時データ
    cache: dict  # キャッシュは別途管理すべき
```

### 3. エッジの明確化

エッジは、**明確な条件**で定義します。

```python
def should_continue(state: MessagesState) -> Literal["tool_node", END]:
    """明確な条件判定"""
    last_message = state["messages"][-1]
    
    if last_message.tool_calls:
        return "tool_node"
    return END
```

### 4. エラーハンドリング

各ノードで適切にエラーを処理します。

```python
def tool_node(state: dict) -> dict:
    """エラーハンドリングを含むノード"""
    try:
        result = []
        for tool_call in state["messages"][-1].tool_calls:
            tool = tools_by_name[tool_call["name"]]
            observation = tool.invoke(tool_call["args"])
            result.append(ToolMessage(content=observation, tool_call_id=tool_call["id"]))
        return {"messages": result}
    except Exception as e:
        # エラーを適切に処理
        error_message = ToolMessage(
            content=f"Error: {str(e)}",
            tool_call_id=tool_call["id"]
        )
        return {"messages": [error_message]}
```

## グラフの設計パターン

### パターン1: シンプルな線形フロー

```
START → node_a → node_b → node_c → END
```

**用途**: 順次処理が必要な場合

### パターン2: 条件分岐

```
START → node_a → [条件判定] → node_b
                      ↓
                   node_c → END
```

**用途**: 状態に応じて処理を分岐させる場合

### パターン3: ループ

```
START → node_a → [条件判定] → node_b → node_a
                      ↓
                    END
```

**用途**: 繰り返し処理が必要な場合（例: ツール呼び出しループ）

### パターン4: 並列処理

```
START → node_a → [分岐] → node_b ─┐
                      ↓            ↓
                   node_c ─────→ node_d → END
```

**用途**: 複数の処理を並列に実行し、結果を統合する場合

## 実践的な設計手順

### ステップ1: 要件の明確化

1. エージェントが解決すべき問題を明確にする
2. 必要な入力と出力を定義する
3. 処理の流れを大まかに把握する

### ステップ2: ノードの設計

1. 処理を独立したノードに分解する
2. 各ノードの責任を明確にする
3. ノード間の依存関係を整理する

### ステップ3: エッジの設計

1. ノード間の接続を定義する
2. 条件分岐が必要な場合は、条件付きエッジを使用する
3. ループが必要な場合は、エッジでループを形成する

### ステップ4: 状態の設計

1. 必要な状態を定義する
2. 状態の型を明確にする（TypedDict）
3. 状態の更新方法を決定する（operator.addなど）

### ステップ5: 実装とテスト

1. 各ノードを実装する
2. グラフを構築する
3. テストケースで動作を確認する
4. 必要に応じてリファクタリングする

## よくある設計ミスと回避方法

### ミス1: ノードが大きすぎる

**問題**: 一つのノードに複数の責任がある

**解決策**: ノードを小さく分割し、単一責任の原則に従う

### ミス2: 状態が複雑すぎる

**問題**: 状態に不要な情報が含まれている

**解決策**: 状態を最小化し、必要な情報のみを含める

### ミス3: エッジが不明確

**問題**: 条件判定が複雑で理解が困難

**解決策**: 条件判定関数を明確にし、コメントを追加する

### ミス4: エラーハンドリングの欠如

**問題**: エラーが適切に処理されていない

**解決策**: 各ノードでエラーハンドリングを実装する

## まとめ

LangGraphのグラフベースの思考法により、以下のことが可能になります：

1. **視覚的な理解**: エージェントの動作が直感的に理解できる
2. **柔軟な制御フロー**: 複雑な分岐やループを自然に表現できる
3. **明確な状態管理**: 状態がグラフ全体で共有され、追跡が容易
4. **デバッグの容易さ**: 実行パスが明確で、問題の特定が容易

これらの原則に従うことで、保守性が高く、拡張性のあるエージェントを構築できます。

## 次のステップ

- [P14: Workflows + Agents](./P14_workflows_agents.md): ワークフロー型とエージェント型の違いを学ぶ
- [P15: Streaming](./P15_streaming.md): ストリーミング出力の実装
- [P16: Persistence](./P16_persistence.md): 状態の永続化

