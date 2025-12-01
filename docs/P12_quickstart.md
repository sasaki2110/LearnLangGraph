# LangGraph クイックスタート解説

## 概要

このドキュメントは、LangGraphのクイックスタート（`p12_quickstart.py`）の詳細な解説です。  
公式ドキュメント: https://docs.langchain.com/oss/python/langgraph/quickstart

このサンプルでは、**Graph API**を使用して計算エージェントを構築します。エージェントは加算、乗算、除算のツールを使用して、ユーザーの質問に答えることができます。

## 実行方法

### 前提条件

1. 仮想環境が有効化されていること
2. 依存関係がインストールされていること（`pip install -r requirements.txt`）
3. Claude APIキーが環境変数に設定されていること

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

### 実行コマンド

```bash
python p12_quickstart.py
```

## アーキテクチャの概要

このエージェントは以下のようなフローで動作します：

```
START → llm_call → [ツール呼び出しあり？] → tool_node → llm_call → END
                      ↓
                    [ツール呼び出しなし]
                      ↓
                     END
```

1. **START**: エージェントの開始
2. **llm_call**: LLMがユーザーの質問を分析し、ツールを呼び出すかどうかを決定
3. **should_continue**: 条件分岐ロジック
   - ツール呼び出しあり → `tool_node`へ
   - ツール呼び出しなし → `END`へ
4. **tool_node**: ツールを実行し、結果を返す
5. **llm_call**: ツールの結果を受け取り、最終的な回答を生成
6. **END**: エージェントの終了

## コードの詳細解説

### 1. ツールとモデルの定義

```python
from langchain.tools import tool
from langchain.chat_models import init_chat_model

model = init_chat_model(
    "claude-sonnet-4-5-20250929",
    temperature=0
)
```

- **`init_chat_model`**: Claude Sonnet 4.5モデルを初期化
- **`temperature=0`**: 一貫性のある出力のため、ランダム性を最小化

#### ツールの定義

```python
@tool
def multiply(a: int, b: int) -> int:
    """Multiply `a` and `b`."""
    return a * b
```

- **`@tool`デコレータ**: 関数をLangChainのツールとして登録
- ツールの説明文（docstring）は、LLMがツールを選択する際の重要な情報となります

#### ツールのバインド

```python
tools = [add, multiply, divide]
tools_by_name = {tool.name: tool for tool in tools}
model_with_tools = model.bind_tools(tools)
```

- **`bind_tools`**: LLMにツールをバインドし、LLMがツールを呼び出せるようにする
- **`tools_by_name`**: ツール名からツールオブジェクトを取得するための辞書

### 2. 状態の定義

```python
from typing_extensions import TypedDict, Annotated
import operator

class MessagesState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    llm_calls: int
```

- **`MessagesState`**: エージェントの状態を定義するTypedDict
- **`messages`**: メッセージのリスト
  - `Annotated[list[AnyMessage], operator.add]`: 新しいメッセージが既存のリストに**追加**されることを示す
  - これにより、メッセージ履歴が保持されます
- **`llm_calls`**: LLMの呼び出し回数をカウント

**重要**: `operator.add`を使用することで、状態の更新時にメッセージが置き換えられるのではなく、追加されることが保証されます。

### 3. モデルノードの定義

```111:125:p12_quickstart.py
def llm_call(state: dict):
    """LLMがツールを呼び出すかどうかを決定します。"""
    return {
        "messages": [
            model_with_tools.invoke(
                [
                    SystemMessage(
                        content="You are a helpful assistant tasked with performing arithmetic on a set of inputs."
                    )
                ]
                + state["messages"]
            )
        ],
        "llm_calls": state.get('llm_calls', 0) + 1
    }
```

- **`llm_call`**: LLMを呼び出すノード関数
- **`SystemMessage`**: エージェントの役割を定義するシステムメッセージ
- **`state["messages"]`**: これまでの会話履歴を含む
- **`model_with_tools.invoke`**: ツールがバインドされたモデルを呼び出し
  - LLMは、必要に応じてツールを呼び出すか、直接回答を返すかを決定します
- **`llm_calls`**: 呼び出し回数をインクリメント

#### 3.1 `model_with_tools.invoke`に送られるプロンプトの詳細

**重要な質問**: `model_with_tools.invoke`を呼び出す際、明示的に渡しているメッセージリスト（`SystemMessage` + `state["messages"]`）だけが送られるのでしょうか？それとも、`bind_tools`によって追加の情報が含まれるのでしょうか？

**答え**: `bind_tools`は、**ツールのスキーマ（関数定義）をAPIリクエストに追加**しますが、**明示的な「ツールを使え」というプロンプトは追加しません**。

##### 実際にLLMに送られる情報

`model_with_tools.invoke`を呼び出すと、以下の情報がLLMに送られます：

1. **明示的に渡したメッセージ**:
   ```python
   [
       SystemMessage(
           content="You are a helpful assistant tasked with performing arithmetic on a set of inputs."
       )
   ] + state["messages"]
   ```

2. **`bind_tools`によって追加されるツール定義**:
   - ツールの名前、説明、パラメータのスキーマ（型、必須/任意など）
   - これは**APIリクエストの`tools`パラメータ**として送信されます
   - メッセージの内容には含まれませんが、LLMがツールを呼び出すための情報として提供されます

##### 具体的な例（OpenAI APIの場合）

OpenAI APIに送信されるリクエストは、以下のような構造になります：

```json
{
  "model": "gpt-4o-mini",
  "messages": [
    {
      "role": "system",
      "content": "You are a helpful assistant tasked with performing arithmetic on a set of inputs."
    },
    {
      "role": "user",
      "content": "Add 3 and 4."
    }
  ],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "add",
        "description": "Adds `a` and `b`.",
        "parameters": {
          "type": "object",
          "properties": {
            "a": {"type": "integer", "description": "First int"},
            "b": {"type": "integer", "description": "Second int"}
          },
          "required": ["a", "b"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "multiply",
        "description": "Multiply `a` and `b`.",
        "parameters": {
          "type": "object",
          "properties": {
            "a": {"type": "integer", "description": "First int"},
            "b": {"type": "integer", "description": "Second int"}
          },
          "required": ["a", "b"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "divide",
        "description": "Divide `a` and `b`.",
        "parameters": {
          "type": "object",
          "properties": {
            "a": {"type": "integer", "description": "First int"},
            "b": {"type": "integer", "description": "Second int"}
          },
          "required": ["a", "b"]
        }
      }
    }
  ]
}
```

##### 重要なポイント

1. **ツール定義は自動的に追加される**: `bind_tools`を呼び出すと、ツールのスキーマがAPIリクエストに含まれます
2. **明示的な「ツールを使え」というプロンプトはない**: モデル自体が、ツール定義を見て、必要に応じてツールを呼び出すかどうかを判断します
3. **SystemMessageの役割**: システムメッセージは、エージェントの役割や動作を定義しますが、ツールの使用方法については、ツール定義（`tools`パラメータ）から推論されます
4. **ツールの説明文（docstring）が重要**: ツールの`@tool`デコレータで定義されたdocstringは、LLMがツールを選択する際の重要な情報となります

##### ツール利用を促すには

もし明示的にツール利用を促したい場合は、`SystemMessage`の内容を変更できます：

```python
SystemMessage(
    content="You are a helpful assistant tasked with performing arithmetic on a set of inputs. "
            "You have access to tools (add, multiply, divide) that you should use when performing calculations. "
            "Always use the appropriate tool to calculate the answer."
)
```

ただし、多くの場合、ツール定義が提供されていれば、モデルは適切にツールを使用します。

### 4. ツールノードの定義

```python
def tool_node(state: dict):
    """ツール呼び出しを実行します。"""
    result = []
    for tool_call in state["messages"][-1].tool_calls:
        tool = tools_by_name[tool_call["name"]]
        observation = tool.invoke(tool_call["args"])
        result.append(ToolMessage(content=observation, tool_call_id=tool_call["id"]))
    return {"messages": result}
```

- **`tool_node`**: ツールを実行するノード関数
- **`state["messages"][-1].tool_calls`**: 最後のメッセージからツール呼び出しを取得
- **`tool.invoke(tool_call["args"])`**: ツールを実行
- **`ToolMessage`**: ツールの実行結果をメッセージとして返す
  - `tool_call_id`: どのツール呼び出しに対する結果かを識別

### 5. 終了ロジックの定義

```python
def should_continue(state: MessagesState) -> Literal["tool_node", END]:
    """LLMがツールを呼び出したかどうかを確認します。"""
    messages = state["messages"]
    last_message = messages[-1]
    
    if last_message.tool_calls:
        return "tool_node"
    return END
```

- **`should_continue`**: 条件付きエッジ関数
- **`last_message.tool_calls`**: 最後のメッセージにツール呼び出しが含まれているかチェック
- ツール呼び出しあり → `"tool_node"`にルーティング
- ツール呼び出しなし → `END`にルーティング（エージェント終了）

### 6. エージェントの構築とコンパイル

このセクションは、LangGraphの**最も重要な部分**です。ここで、個別に定義したノード（関数）を組み合わせて、実際に動作するエージェントを構築します。

```169:185:p12_quickstart.py
# ワークフローの構築
agent_builder = StateGraph(MessagesState)

# ノードの追加
agent_builder.add_node("llm_call", llm_call)
agent_builder.add_node("tool_node", tool_node)

# ノードを接続するエッジの追加
agent_builder.add_edge(START, "llm_call")
agent_builder.add_conditional_edges(
    "llm_call",
    should_continue,
    ["tool_node", END]
)
agent_builder.add_edge("tool_node", "llm_call")

# エージェントのコンパイル
agent = agent_builder.compile()
```

#### 6.1 StateGraphとは何か

**`StateGraph`**は、LangGraphの核心となるクラスです。これは、**状態を持つ有向グラフ（Directed Graph）**を構築するためのビルダーパターンを提供します。

- **グラフ**: ノード（処理単位）とエッジ（接続）で構成されるデータ構造
- **状態**: グラフの実行中に保持されるデータ（この例では`MessagesState`）
- **有向**: エッジに方向があり、一方向にのみデータが流れる

```python
agent_builder = StateGraph(MessagesState)
```

この行で、`MessagesState`型の状態を管理するグラフビルダーを作成します。このビルダーにノードとエッジを追加していくことで、エージェントの構造を定義します。

#### 6.2 ノードの追加

ノードは、グラフ内で実行される処理単位です。各ノードは関数として実装され、状態を受け取り、状態を返します。

```python
agent_builder.add_node("llm_call", llm_call)
agent_builder.add_node("tool_node", tool_node)
```

- **`add_node(name, function)`**: グラフにノードを追加
  - `name`: ノードの識別子（文字列）
  - `function`: ノードで実行される関数（状態を受け取り、状態を返す）

**重要なポイント**:
- ノード名（`"llm_call"`, `"tool_node"`）は、エッジで参照する際に使用されます
- 各ノードは独立して定義され、グラフ構築時に接続されます
- ノードの実行順序は、エッジの定義によって決定されます

#### 6.3 エッジの追加

エッジは、ノード間の接続を定義します。LangGraphには2種類のエッジがあります：

##### 6.3.1 通常エッジ（Unconditional Edge）

```python
agent_builder.add_edge(START, "llm_call")
agent_builder.add_edge("tool_node", "llm_call")
```

- **`add_edge(from_node, to_node)`**: 無条件で次のノードへ遷移
  - `START`: グラフの開始点（特別な定数）
  - `END`: グラフの終了点（特別な定数）

**動作**:
- `START → "llm_call"`: エージェント開始時、必ず`llm_call`ノードが実行される
- `"tool_node" → "llm_call"`: ツール実行後、必ず再度`llm_call`ノードが実行される

##### 6.3.2 条件付きエッジ（Conditional Edge）

```python
agent_builder.add_conditional_edges(
    "llm_call",
    should_continue,
    ["tool_node", END]
)
```

- **`add_conditional_edges(from_node, condition_func, mapping)`**: 実行時に次のノードを動的に決定
  - `from_node`: 条件分岐の起点となるノード
  - `condition_func`: 状態を評価して次のノードを決定する関数
  - `mapping`: 可能な遷移先のリスト

**動作メカニズム**:

1. `"llm_call"`ノードが実行される
2. 状態が`should_continue`関数に渡される
3. `should_continue`が状態を評価し、次のノード名を返す
   - `"tool_node"`を返す → ツールノードへ遷移
   - `END`を返す → エージェント終了
4. 返された値に基づいて、対応するノードへ遷移

**`should_continue`関数の再確認**:

```150:159:p12_quickstart.py
def should_continue(state: MessagesState) -> Literal["tool_node", END]:
    """LLMがツールを呼び出したかどうかを確認します。"""
    messages = state["messages"]
    last_message = messages[-1]
    
    # LLMがツールを呼び出した場合、アクションを実行
    if last_message.tool_calls:
        return "tool_node"
    # それ以外の場合、停止（ユーザーに返信）
    return END
```

この関数は、最後のメッセージに`tool_calls`が含まれているかどうかをチェックし、それに基づいて次のノードを決定します。

**重要なポイント**:
- 条件付きエッジにより、**実行時の状態に応じて動的にフローを制御**できます
- これが、LangGraphが「エージェント」を実現するための核心的な機能です
- `mapping`リスト（`["tool_node", END]`）は、`condition_func`が返す可能性のある値を列挙します

#### 6.4 コンパイル

```python
agent = agent_builder.compile()
```

**`compile()`**は、構築したグラフを**実行可能なエージェント**に変換します。

**コンパイル時に何が起こるか**:

1. **グラフの検証**: ノードとエッジの接続が正しいかチェック
2. **最適化**: グラフの構造を最適化（可能な場合）
3. **実行エンジンの準備**: 状態管理、エッジの評価、ノードの実行などの仕組みを準備

**コンパイル後の`agent`オブジェクト**:
- `agent.invoke(state)`: エージェントを実行し、最終状態を返す
- `agent.stream(state)`: エージェントをストリーミング実行（各ノードの実行結果を順次返す）
- `agent.get_graph()`: グラフの構造を可視化

**重要なポイント**:
- コンパイルは**一度だけ**行います
- コンパイル後は、同じエージェントを何度でも実行できます
- コンパイル時にエラーが発生した場合、グラフの定義に問題がある可能性があります

#### 6.5 グラフの完全な構造

構築されたグラフの構造を視覚化すると、以下のようになります：

```
                    START
                      ↓
                  llm_call
                      │
                      ├─[should_continue判定]─┐
                      │                        │
                      │                        │
        [tool_callsあり]              [tool_callsなし]
                      │                        │
                      ↓                        ↓
                tool_node                     END
                      │
                      │ (無条件エッジ)
                      ↓
                  llm_call
                      │
                      ├─[should_continue判定]─┐
                      │                        │
                      │                        │
        [tool_callsあり]              [tool_callsなし]
                      │                        │
                      ↓                        ↓
                tool_node                     END
                      │
                      └─ (ループ可能) ─┘
```

**実行フローの詳細**:

1. **START → llm_call**: エージェント開始
2. **llm_call**: LLMがユーザーの質問を分析
   - ツールが必要な場合: `AIMessage`に`tool_calls`を含める
   - ツールが不要な場合: 直接回答を含む`AIMessage`を返す
3. **条件分岐（should_continue）**:
   - `tool_calls`あり → `"tool_node"`へ
   - `tool_calls`なし → `END`へ（エージェント終了）
4. **tool_node → llm_call**: ツール実行後、必ず再度LLMを呼び出す
   - ツールの結果を`ToolMessage`として状態に追加
   - LLMがツールの結果を解釈し、最終回答を生成
5. **再度条件分岐**: 最終回答にツール呼び出しが含まれていないため、`END`へ

#### 6.6 なぜこの構造が重要なのか

このグラフ構造により、以下のことが実現されます：

1. **ループ処理**: `tool_node → llm_call`のループにより、複数のツールを連続して呼び出すことが可能
2. **動的分岐**: 条件付きエッジにより、実行時に次の処理を決定
3. **状態の永続化**: 各ノードが状態を更新し、次のノードに引き継がれる
4. **拡張性**: 新しいノードやエッジを追加することで、エージェントの機能を拡張可能

#### 6.7 実際の実行例

「Add 3 and 4.」という質問に対する実行フロー：

```
1. START
   ↓
2. llm_call
   入力: [HumanMessage("Add 3 and 4.")]
   出力: AIMessage(tool_calls=[{"name": "add", "args": {"a": 3, "b": 4}}])
   状態: {messages: [HumanMessage, AIMessage], llm_calls: 1}
   ↓
3. should_continue判定
   → tool_callsあり → "tool_node"へ
   ↓
4. tool_node
   入力: 状態（tool_callsを含む）
   実行: add(3, 4) = 7
   出力: ToolMessage(content="7", tool_call_id="...")
   状態: {messages: [..., ToolMessage], llm_calls: 1}
   ↓
5. llm_call（再実行）
   入力: 状態（ToolMessageを含む）
   出力: AIMessage(content="3 + 4 = 7")
   状態: {messages: [..., AIMessage], llm_calls: 2}
   ↓
6. should_continue判定
   → tool_callsなし → ENDへ
   ↓
7. END
   最終状態を返す
```

このように、グラフの構造により、エージェントは自動的に適切な順序でノードを実行し、状態を管理しながら処理を進めます。

### 7. エージェントの実行

```python
messages = [HumanMessage(content="Add 3 and 4.")]
result = agent.invoke({"messages": messages, "llm_calls": 0})
```

- **`HumanMessage`**: ユーザーの入力メッセージ
- **`agent.invoke`**: エージェントを実行
  - 入力: 初期状態（メッセージとLLM呼び出し回数）
  - 出力: 最終状態（すべてのメッセージとLLM呼び出し回数）

## 実行フローの例

### 例: "Add 3 and 4." の処理

1. **START → llm_call**
   - 入力: `[HumanMessage("Add 3 and 4.")]`
   - LLMが分析し、`add`ツールを呼び出すことを決定
   - 出力: `AIMessage(tool_calls=[{"name": "add", "args": {"a": 3, "b": 4}}])`

2. **llm_call → tool_node** (should_continueが"tool_node"を返す)
   - `add(3, 4)`を実行
   - 出力: `ToolMessage(content="7", tool_call_id="...")`

3. **tool_node → llm_call**
   - ツールの結果を受け取り、最終回答を生成
   - 出力: `AIMessage(content="3 + 4 = 7")`

4. **llm_call → END** (should_continueがENDを返す)
   - ツール呼び出しがないため、エージェント終了

## 重要な概念

### 状態の永続性

LangGraphでは、状態がエージェントの実行中に保持されます。`operator.add`を使用することで、メッセージが追加され、会話履歴が維持されます。

### 条件付きエッジ

`add_conditional_edges`を使用することで、実行時に動的に次のノードを決定できます。これにより、複雑な分岐ロジックを実装できます。

### ツールの統合

LLMにツールをバインドすることで、LLMは必要に応じてツールを呼び出すことができます。これは、LLMの能力を拡張する強力な方法です。

## トラブルシューティング

### エラー: APIキーが見つからない

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

### エラー: モジュールが見つからない

依存関係がインストールされているか確認してください：

```bash
pip install -r requirements.txt
```

### 実行が遅い

LLMの呼び出しには時間がかかります。特に初回実行時は、モデルのロードに時間がかかる場合があります。

## 次のステップ

- [Thinking in LangGraph](https://docs.langchain.com/oss/python/langgraph/thinking-in-langgraph): LangGraphの設計思想を学ぶ
- [Functional API](https://docs.langchain.com/oss/python/langgraph/functional-api): 関数型APIを使用した実装方法
- [Streaming](https://docs.langchain.com/oss/python/langgraph/streaming): ストリーミング出力の実装
- [Persistence](https://docs.langchain.com/oss/python/langgraph/persistence): 状態の永続化

## 参考資料

- [公式クイックスタート](https://docs.langchain.com/oss/python/langgraph/quickstart)
- [LangGraph Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api)
- [LangChain Tools](https://python.langchain.com/docs/modules/tools/)

