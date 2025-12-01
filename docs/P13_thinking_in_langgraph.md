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

### ステップ3: 状態を設計する

状態は、エージェント内のすべてのノードがアクセスできる共有**メモリ**です。エージェントがプロセスを進める際に学習し決定したすべてのことを追跡するために使用するノートブックのようなものです。

#### 状態に何を含めるべきか？

各データについて、以下の質問をしてください：

**状態に含めるべきもの**:
- ステップ間で永続化する必要があるか？ → はいの場合、状態に含める

**状態に含めないもの**:
- 他のデータから導出できるか？ → はいの場合、必要なときに計算し、状態に保存しない

**メールエージェントの例**:

状態に含めるべきもの：
- 元のメールと送信者情報（後で再構築できない）
- 分類結果（複数の後続ノードで必要）
- 検索結果と顧客データ（再取得するコストが高い）
- 下書き返信（レビューを通じて永続化する必要がある）
- 実行メタデータ（デバッグと回復のため）

#### 状態は生データを保持し、プロンプトはオンデマンドでフォーマットする

重要な原則：**状態は生データを保存し、フォーマットされたテキストは保存しない**。プロンプトはノード内で必要なときにフォーマットします。

この分離により：
- 異なるノードが同じデータを異なる方法で使用できる
- プロンプトテンプレートを変更しても状態スキーマを変更する必要がない
- デバッグが明確になる - 各ノードが受け取ったデータを正確に確認できる
- エージェントを進化させても既存の状態を壊さない

**状態定義の例**:

```python
from typing import TypedDict, Literal

# メール分類の構造を定義
class EmailClassification(TypedDict):
    intent: Literal["question", "bug", "billing", "feature", "complex"]
    urgency: Literal["low", "medium", "high", "critical"]
    topic: str
    summary: str

class EmailAgentState(TypedDict):
    # 生のメールデータ
    email_content: str
    sender_email: str
    email_id: str
    
    # 分類結果
    classification: EmailClassification | None
    
    # 生の検索/API結果
    search_results: list[str] | None  # 生のドキュメントチャンクのリスト
    customer_history: dict | None  # CRMからの生の顧客データ
    
    # 生成されたコンテンツ
    draft_response: str | None
    messages: list[str] | None
```

状態には生データのみが含まれます - プロンプトテンプレート、フォーマットされた文字列、指示は含まれません。分類出力は、LLMから直接取得した単一の辞書として保存されます。

## 実践的な構築プロセス

LangGraphでエージェントを構築する際は、通常以下の5つのステップに従います。ここでは、**カスタマーサポートメールエージェント**を例に説明します。

### 要件の例

カスタマーサポートメールを処理するAIエージェントを構築するとします。要件は以下の通りです：

- 受信したカスタマーメールを読み取る
- 緊急度とトピックで分類する
- 関連するドキュメントを検索して質問に答える
- 適切な返信を起草する
- 複雑な問題は人間エージェントにエスカレートする
- 必要に応じてフォローアップをスケジュールする

### ステップ1: ワークフローを個別のステップに分解する

プロセス内の個別のステップを特定します。各ステップは**ノード**（1つの特定のことを行う関数）になります。次に、これらのステップがどのように接続されるかをスケッチします。

**カスタマーサポートメールエージェントのノード**:

- `Read Email`: メールの内容を抽出して解析
- `Classify Intent`: LLMを使用して緊急度とトピックを分類し、適切なアクションにルーティング
- `Doc Search`: ナレッジベースをクエリして関連情報を検索
- `Bug Track`: トラッキングシステムで問題を作成または更新
- `Draft Reply`: 適切な返信を生成
- `Human Review`: 人間エージェントに承認または処理をエスカレート
- `Send Reply`: メール返信を送信

**注意**: 一部のノード（`Classify Intent`、`Draft Reply`、`Human Review`）は次の行き先を決定しますが、他のノード（`Read Email`は常に`Classify Intent`へ、`Doc Search`は常に`Draft Reply`へ）は常に同じ次のステップに進みます。

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

### ステップ2: 各ステップが何を行う必要があるかを特定する

グラフ内の各ノードについて、それが表す操作のタイプと、適切に機能するために必要なコンテキストを決定します。

#### ノードタイプの分類

**1. LLM steps（LLMステップ）**

理解、分析、テキスト生成、または推論決定が必要な場合に使用します。

- `Classify intent`: メールの意図を分類
- `Draft reply`: 返信を起草

**2. Data steps（データステップ）**

外部ソースから情報を取得する必要がある場合に使用します。

- `Document search`: ドキュメント検索
- `Customer history lookup`: 顧客履歴の検索

**3. Action steps（アクションステップ）**

外部アクションを実行する必要がある場合に使用します。

- `Send reply`: 返信を送信
- `Bug track`: バグトラッキング

**4. User input steps（ユーザー入力ステップ）**

人間の介入が必要な場合に使用します。

- `Human review node`: 人間によるレビューノード

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

### ステップ4: ノードを構築する

各ステップを関数として実装します。LangGraphのノードは、現在の状態を受け取り、その状態への更新を返すPython関数です。

#### エラーハンドリング

異なるエラーには異なる処理戦略が必要です：

| エラータイプ | 誰が修正するか | 戦略 | 使用するタイミング |
|------------|------------|------|----------------|
| **Transient errors**（一時的なエラー）<br>ネットワーク問題、レート制限 | システム（自動） | リトライポリシー | 通常、リトライで解決する一時的な失敗 |
| **LLM-recoverable errors**<br>（LLMが回復可能なエラー）<br>ツール失敗、パース問題 | LLM | エラーを状態に保存してループバック | LLMがエラーを確認してアプローチを調整できる場合 |
| **User-fixable errors**<br>（ユーザーが修正可能なエラー）<br>情報不足、不明確な指示 | 人間 | `interrupt()`で一時停止 | ユーザー入力が必要な場合 |
| **Unexpected errors**<br>（予期しないエラー） | 開発者 | バブルアップさせる | デバッグが必要な未知の問題 |

**リトライポリシーの実装例**:

```python
from langgraph.types import RetryPolicy

workflow.add_node(
    "search_documentation",
    search_documentation,
    retry_policy=RetryPolicy(max_attempts=3, initial_interval=1.0)
)
```

#### エラーハンドリングの実装例

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
        # LLMが回復可能なエラー: エラーを状態に保存してループバック
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

### ステップ5: グラフを接続する

ノードを動作するグラフに接続します。ノードが独自のルーティング決定を処理するため、いくつかの基本的なエッジのみが必要です。

**人間の介入（human-in-the-loop）を有効にする**:

`interrupt()`を使用するには、実行間で状態を保存するために**checkpointer**でコンパイルする必要があります：

```python
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import RetryPolicy

# グラフを作成
workflow = StateGraph(EmailAgentState)

# 適切なエラーハンドリングでノードを追加
workflow.add_node("read_email", read_email)
workflow.add_node("classify_intent", classify_intent)

# 一時的な失敗の可能性があるノードにリトライポリシーを追加
workflow.add_node(
    "search_documentation",
    search_documentation,
    retry_policy=RetryPolicy(max_attempts=3)
)
workflow.add_node("bug_tracking", bug_tracking)
workflow.add_node("draft_response", draft_response)
workflow.add_node("human_review", human_review)
workflow.add_node("send_reply", send_reply)

# 基本的なエッジのみを追加
workflow.add_edge(START, "read_email")
workflow.add_edge("read_email", "classify_intent")
workflow.add_edge("send_reply", END)

# 永続化のためにcheckpointerでコンパイル
# （Local_Serverでグラフを実行する場合は、checkpointerなしでコンパイルしてください）
memory = MemorySaver()
app = workflow.compile(checkpointer=memory)
```

**グラフ構造が最小限な理由**:

グラフ構造が最小限なのは、ルーティングがノード内で**Command**オブジェクトを通じて行われるためです。各ノードは、`Command[Literal["node1", "node2"]]`のような型ヒントを使用して、どこに行けるかを宣言します。これにより、フローが明確で追跡可能になります。

**interrupt()関数**:

`interrupt()`関数は実行を無期限に一時停止し、すべての状態を保存し、入力を提供したときに正確に中断した場所から再開します。ノード内で他の操作と組み合わせて使用する場合、最初に実行する必要があります。

```python
from langgraph.types import interrupt

def human_review(state: EmailAgentState):
    # interrupt()は最初に実行する必要がある
    interrupt()
    # 人間のレビュー後の処理
    return {"reviewed": True}
```

## 実践的な設計手順（まとめ）

1. **要件の明確化**: エージェントが解決すべき問題を明確にする
2. **ノードの設計**: 処理を独立したノードに分解する
3. **エッジの設計**: ノード間の接続を定義する
4. **状態の設計**: 必要な状態を定義する（生データのみ）
5. **実装とテスト**: 各ノードを実装し、グラフを構築してテストする

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

## 重要な洞察（Key Insights）

このメールエージェントの構築を通じて、LangGraphの思考方法が示されました：

### 1. 個別のステップに分解する

各ノードは1つのことをうまく行います。この分解により、ストリーミング進行状況の更新、一時停止して再開できる永続的な実行、ステップ間で状態を検査できる明確なデバッグが可能になります。

### 2. 状態は共有メモリ

生データを保存し、フォーマットされたテキストは保存しません。これにより、異なるノードが同じ情報を異なる方法で使用できます。

### 3. ノードは関数

状態を受け取り、作業を行い、更新を返します。ルーティング決定が必要な場合、状態の更新と次の宛先の両方を指定します。

### 4. エラーはフローの一部

一時的な失敗はリトライされ、LLMが回復可能なエラーはコンテキストと共にループバックし、ユーザーが修正可能な問題は入力のために一時停止し、予期しないエラーはデバッグのためにバブルアップします。

### 5. 人間の入力は第一級

`interrupt()`関数は実行を無期限に一時停止し、すべての状態を保存し、入力を提供したときに正確に中断した場所から再開します。ノード内で他の操作と組み合わせて使用する場合、最初に実行する必要があります。

### 6. グラフ構造は自然に出現する

基本的な接続を定義し、ノードが独自のルーティングロジックを処理します。これにより、制御フローが明確で追跡可能になります - 現在のノードを見ることで、エージェントが次に何をするかを常に理解できます。

## 高度な考慮事項（Advanced Considerations）

### ノードの粒度のトレードオフ

ノードを細かく分割すると：
- **利点**: デバッグが容易、ストリーミングが可能、再利用性が高い
- **欠点**: より多くのノード間の状態管理が必要

ノードを大きくすると：
- **利点**: 実装が簡単、状態管理が少ない
- **欠点**: デバッグが困難、ストリーミングが制限される

適切なバランスを見つけることが重要です。

## まとめ

LangGraphのグラフベースの思考法により、以下のことが可能になります：

1. **視覚的な理解**: エージェントの動作が直感的に理解できる
2. **柔軟な制御フロー**: 複雑な分岐やループを自然に表現できる
3. **明確な状態管理**: 状態がグラフ全体で共有され、追跡が容易
4. **デバッグの容易さ**: 実行パスが明確で、問題の特定が容易
5. **永続的な実行**: 一時停止して再開できる
6. **人間の介入**: `interrupt()`による人間の入力のサポート

これらの原則に従うことで、保守性が高く、拡張性のあるエージェントを構築できます。

## 次のステップ

このドキュメントで学んだ基礎を、以下のトピックで拡張できます：

- **Human-in-the-loop patterns**: 実行前のツール承認、バッチ承認などのパターンを学ぶ
- **Subgraphs**: 複雑なマルチステップ操作のためのサブグラフを作成
- **Streaming**: ユーザーにリアルタイムの進行状況を表示するストリーミングを追加
- **Observability**: LangSmithを使用したデバッグとモニタリングのための可観測性を追加
- **Tool Integration**: Web検索、データベースクエリ、API呼び出しのためのより多くのツールを統合
- **Retry Logic**: 失敗した操作のための指数バックオフによるリトライロジックを実装

## 関連ドキュメント

- [P14: Workflows + Agents](./P14_workflows_agents.md): ワークフロー型とエージェント型の違いを学ぶ
- [P15: Streaming](./P15_streaming.md): ストリーミング出力の実装
- [P16: Persistence](./P16_persistence.md): 状態の永続化

