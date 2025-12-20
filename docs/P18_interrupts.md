# Interrupts

このドキュメントでは、LangGraphにおける中断（Interrupts）と人間の介入（Human-in-the-loop）について解説します。

公式ドキュメント: https://docs.langchain.com/oss/python/langgraph/interrupts

## 概要

中断（Interrupts）により、グラフの実行を特定のポイントで一時停止し、外部からの入力を待ってから続行できます。これにより、外部からの入力が必要な人間参加型（human-in-the-loop）パターンを実現できます。中断がトリガーされると、LangGraphは[永続化](./P16_persistence.md)レイヤーを使用してグラフの状態を保存し、実行を再開するまで無期限に待機します。

中断は、グラフノード内の任意のポイントで`interrupt()`関数を呼び出すことで機能します。この関数は任意のJSONシリアライズ可能な値を受け取り、呼び出し元に公開されます。続行する準備ができたら、`Command`を使用してグラフを再呼び出しすることで実行を再開します。この値は`interrupt()`呼び出しの戻り値になります。

静的ブレークポイント（特定のノードの前後で一時停止）とは異なり、中断は**動的**です。コード内の任意の場所に配置でき、アプリケーションロジックに基づいて条件付きで使用できます。

重要なポイント：

- **チェックポイントが場所を保持**: チェックポインターは正確なグラフ状態を書き込むため、エラー状態でも後で再開できます。
- **`thread_id`がポインター**: `config={"configurable": {"thread_id": ...}}`を設定して、チェックポインターにどの状態を読み込むかを指示します。
- **中断ペイロードは`__interrupt__`として表示**: `interrupt()`に渡した値は、呼び出し元の`__interrupt__`フィールドに返されるため、グラフが何を待っているかがわかります。

選択した`thread_id`は実質的に永続的なカーソルです。同じIDを再利用すると同じチェックポイントから再開し、新しい値を使用すると空の状態で新しいスレッドが開始されます。

## interrupt()を使用した中断

`interrupt()`関数はグラフの実行を一時停止し、呼び出し元に値を返します。ノード内で`interrupt()`を呼び出すと、LangGraphは現在のグラフ状態を保存し、入力が提供されるまで待機します。

`interrupt()`を使用するには、以下が必要です：

1. グラフ状態を永続化する**チェックポインター**（本番環境では永続的なチェックポインターを使用）
2. ランタイムがどの状態から再開するかを知るための、config内の**スレッドID**
3. 一時停止したい場所で`interrupt()`を呼び出す（ペイロードはJSONシリアライズ可能である必要がある）

```python
from langgraph.types import interrupt

def approval_node(state: State):
    # 一時停止して承認を求める
    approved = interrupt("Do you approve this action?")
    # 再開すると、Command(resume=...)の値がここに返される
    return {"approved": approved}
```

`interrupt()`を呼び出すと、以下が発生します：

1. **グラフの実行が中断される**: `interrupt()`が呼び出された正確なポイントで実行が中断されます
2. **状態が保存される**: チェックポインターを使用して状態が保存され、後で実行を再開できます（本番環境では、データベースなどでバックアップされた永続的なチェックポインターを使用）
3. **値が返される**: 呼び出し元の`__interrupt__`の下に値が返されます。任意のJSONシリアライズ可能な値（文字列、オブジェクト、配列など）を指定できます
4. **グラフは無期限に待機する**: 応答で実行を再開するまで待機します
5. **応答が渡される**: 再開すると、応答がノードに渡され、`interrupt()`呼び出しの戻り値になります

## 中断の再開

中断が実行を一時停止した後、`Command`を含む再開値を指定してグラフを再呼び出しすることで、グラフを再開します。再開値は`interrupt()`呼び出しに渡され、ノードが外部入力を使用して実行を続行できるようになります。

```python
from langgraph.types import Command

# 初期実行 - 中断に到達して一時停止
# thread_idは永続的なポインター（本番環境では安定したIDを保存）
config = {"configurable": {"thread_id": "thread-1"}}
result = graph.invoke({"input": "data"}, config=config)

# 何が中断されたかを確認
# __interrupt__にはinterrupt()に渡されたペイロードが含まれる
print(result["__interrupt__"])
# > [Interrupt(value='Do you approve this action?')]

# 人間の応答で再開
# 再開ペイロードは、ノード内のinterrupt()の戻り値になる
graph.invoke(Command(resume=True), config=config)
```

再開に関する重要なポイント：

- 中断が発生したときに使用した**同じスレッドID**を使用して再開する必要があります
- `Command(resume=...)`に渡した値が`interrupt()`呼び出しの戻り値になります
- ノードは、`interrupt()`が呼び出されたノードの**最初から再開**されます。つまり、`interrupt()`の前のコードが再実行されます
- 再開値として任意のJSONシリアライズ可能な値を渡せます

## 一般的なパターン

中断が可能にする重要なことは、実行を一時停止して外部入力を待つことです。これは、以下のようなさまざまなユースケースに役立ちます：

- **承認ワークフロー**: 重要なアクション（API呼び出し、データベース変更、金融取引）を実行する前に一時停止
- **レビューと編集**: 人間がLLMの出力やツール呼び出しをレビューして修正してから続行
- **ツール呼び出しの中断**: ツール呼び出しを実行する前に一時停止して、ツール呼び出しをレビューして編集
- **人間の入力の検証**: 次のステップに進む前に人間の入力を検証

### 承認または拒否

中断の最も一般的な用途の1つは、重要なアクションの前に一時停止して承認を求めることです。たとえば、API呼び出し、データベース変更、またはその他の重要な決定について人間の承認を求めることができます。

```python
from typing import Literal
from langgraph.types import interrupt, Command

def approval_node(state: State) -> Command[Literal["proceed", "cancel"]]:
    # 実行を一時停止。ペイロードはresult["__interrupt__"]に表示される
    is_approved = interrupt({
        "question": "Do you want to proceed with this action?",
        "details": state["action_details"]
    })
    # 応答に基づいてルーティング
    if is_approved:
        return Command(goto="proceed")  # 再開ペイロードが提供された後に実行される
    else:
        return Command(goto="cancel")
```

グラフを再開する際は、承認する場合は`true`、拒否する場合は`false`を渡します：

```python
# 承認する場合
graph.invoke(Command(resume=True), config=config)

# 拒否する場合
graph.invoke(Command(resume=False), config=config)
```

### 状態のレビューと編集

時には、人間にグラフ状態の一部をレビューして編集させてから続行したい場合があります。これは、LLMの修正、不足している情報の追加、または調整を行う場合に役立ちます。

```python
from langgraph.types import interrupt

def review_node(state: State):
    # 一時停止して現在のコンテンツをレビュー用に表示（result["__interrupt__"]に表示される）
    edited_content = interrupt({
        "instruction": "Review and edit this content",
        "content": state["generated_text"]
    })
    # 編集されたバージョンで状態を更新
    return {"generated_text": edited_content}
```

再開する際は、編集されたコンテンツを提供します：

```python
graph.invoke(
    Command(resume="The edited and improved text"),  # 値がinterrupt()の戻り値になる
    config=config
)
```

### ツール内での中断

中断をツール関数内に直接配置することもできます。これにより、ツール自体が呼び出されるたびに承認のために一時停止し、実行前にツール呼び出しを人間がレビューして編集できるようになります。

まず、`interrupt()`を使用するツールを定義します：

```python
from langchain.tools import tool
from langgraph.types import interrupt

@tool
def send_email(to: str, subject: str, body: str):
    """Send an email to a recipient."""
    # 送信前に一時停止。ペイロードはresult["__interrupt__"]に表示される
    response = interrupt({
        "action": "send_email",
        "to": to,
        "subject": subject,
        "body": body,
        "message": "Approve sending this email?"
    })
    if response.get("action") == "approve":
        # 再開値で実行前に入力をオーバーライドできる
        final_to = response.get("to", to)
        final_subject = response.get("subject", subject)
        final_body = response.get("body", body)
        return f"Email sent to {final_to} with subject '{final_subject}'"
    return "Email cancelled by user"
```

このアプローチは、承認ロジックをツール自体に配置したい場合に役立ちます。これにより、グラフの異なる部分で再利用できます。LLMはツールを自然に呼び出すことができ、ツールが呼び出されるたびに中断が実行を一時停止し、アクションを承認、編集、またはキャンセルできます。

### 人間の入力の検証

時には、人間からの入力を検証し、無効な場合は再度尋ねる必要があります。これは、ループ内で複数の`interrupt()`呼び出しを使用して行えます。

```python
from langgraph.types import interrupt

def get_age_node(state: State):
    prompt = "What is your age?"
    while True:
        answer = interrupt(prompt)  # ペイロードはresult["__interrupt__"]に表示される
        # 入力を検証
        if isinstance(answer, int) and answer > 0:
            # 有効な入力 - 続行
            break
        else:
            # 無効な入力 - より具体的なプロンプトで再度尋ねる
            prompt = f"'{answer}' is not a valid age. Please enter a positive number."
    return {"age": answer}
```

無効な入力を指定してグラフを再開するたびに、より明確なメッセージで再度尋ねます。有効な入力が提供されると、ノードが完了し、グラフが続行します。

## 中断のルール

ノード内で`interrupt()`を呼び出すと、LangGraphは実行を中断する例外をスローすることで実行を一時停止します。この例外は呼び出しスタックを伝播し、ランタイムによってキャッチされ、グラフに現在の状態を保存して外部入力を待つように通知します。

実行が再開されると（要求された入力を提供した後）、ランタイムはノードを**最初から再起動**します。つまり、`interrupt()`が呼び出された正確な行から再開するのではなく、ノードの最初から再開します。つまり、`interrupt()`の前に実行されたコードが再実行されます。このため、中断が期待どおりに動作するように、いくつかの重要なルールに従う必要があります。

### interrupt()呼び出しをtry/exceptでラップしない

`interrupt()`が呼び出されたポイントで実行を一時停止する方法は、特別な例外をスローすることです。`interrupt()`呼び出しをtry/exceptブロックでラップすると、この例外をキャッチしてしまい、中断がグラフに渡されなくなります。

- ✅ `interrupt()`呼び出しをエラーが発生しやすいコードから分離する
- ✅ try/exceptブロックで特定の例外タイプを使用する

```python
def node_a(state: State):
    # ✅ 良い例: 最初に中断し、次にエラー条件を個別に処理
    interrupt("What's your name?")
    try:
        fetch_data()  # これは失敗する可能性がある
    except Exception as e:
        print(e)
    return state
```

- 🔴 `interrupt()`呼び出しを裸のtry/exceptブロックでラップしない

```python
def node_a(state: State):
    # ❌ 悪い例: interrupt()を裸のtry/exceptでラップすると中断例外がキャッチされる
    try:
        interrupt("What's your name?")
    except Exception as e:
        print(e)
    return state
```

### ノード内でinterrupt()呼び出しの順序を変えない

1つのノードで複数の中断を使用することは一般的ですが、注意深く処理しないと予期しない動作につながる可能性があります。

ノードに複数の`interrupt()`呼び出しが含まれている場合、LangGraphはノードを実行しているタスク固有の再開値のリストを保持します。実行が再開されると、ノードの最初から開始されます。各`interrupt()`に遭遇すると、LangGraphはタスクの再開リストに一致する値が存在するかどうかを確認します。マッチングは**厳密にインデックスベース**であるため、ノード内の`interrupt()`呼び出しの順序が重要です。

- ✅ ノード実行全体で`interrupt()`呼び出しを一貫して保持する

```python
def node_a(state: State):
    # ✅ 良い例: interrupt()呼び出しは毎回同じ順序で発生する
    name = interrupt("What's your name?")
    age = interrupt("What's your age?")
    city = interrupt("What's your city?")
    return {
        "name": name,
        "age": age,
        "city": city
    }
```

- 🔴 ノード内で条件付きに`interrupt()`呼び出しをスキップしない
- 🔴 実行全体で決定論的でないロジックを使用して`interrupt()`呼び出しをループしない

```python
def node_a(state: State):
    # ❌ 悪い例: 条件付きにinterrupt()をスキップすると順序が変わる
    name = interrupt("What's your name?")
    # 最初の実行では、これはinterrupt()をスキップする可能性がある
    # 再開時にはスキップしない可能性がある - インデックスの不一致を引き起こす
    if state.get("needs_age"):
        age = interrupt("What's your age?")
    city = interrupt("What's your city?")
    return {"name": name, "city": city}
```

### interrupt()呼び出しで複雑な値を返さない

使用するチェックポインターによっては、複雑な値がシリアライズできない場合があります（たとえば、関数をシリアライズできません）。グラフをあらゆるデプロイメントに適応させるには、合理的にシリアライズ可能な値のみを使用するのがベストプラクティスです。

- ✅ `interrupt()`にシンプルなJSONシリアライズ可能な型を渡す
- ✅ シンプルな値を持つ辞書/オブジェクトを渡す

```python
def node_a(state: State):
    # ✅ 良い例: シリアライズ可能なシンプルな型を渡す
    name = interrupt("What's your name?")
    count = interrupt(42)
    approved = interrupt(True)
    return {"name": name, "count": count, "approved": approved}
```

- 🔴 関数、クラスインスタンス、またはその他の複雑なオブジェクトを`interrupt()`に渡さない

```python
def validate_input(value):
    return len(value) > 0

def node_a(state: State):
    # ❌ 悪い例: interrupt()に関数を渡す
    # 関数はシリアライズできない
    response = interrupt({
        "question": "What's your name?",
        "validator": validate_input  # これは失敗する
    })
    return {"name": response}
```

### interrupt()の前に呼び出された副作用は冪等性を持つ必要がある

中断は、呼び出されたノードを再実行することで機能するため、`interrupt()`の前に呼び出された副作用は（理想的には）冪等性を持つ必要があります。冪等性とは、同じ操作を複数回適用しても、初期実行を超えて結果が変わらないことを意味します。

たとえば、ノード内にレコードを更新するAPI呼び出しがあるとします。`interrupt()`がその呼び出しの後に呼び出されると、ノードが再開されると複数回再実行され、初期更新が上書きされたり、重複レコードが作成されたりする可能性があります。

- ✅ `interrupt()`の前に冪等性のある操作を使用する
- ✅ 副作用を`interrupt()`呼び出しの後に配置する
- ✅ 可能な場合は副作用を別のノードに分離する

```python
def node_a(state: State):
    # ✅ 良い例: 冪等性のあるupsert操作を使用
    # これを複数回実行しても同じ結果になる
    db.upsert_user(
        user_id=state["user_id"],
        status="pending_approval"
    )
    approved = interrupt("Approve this change?")
    return {"approved": approved}
```

- 🔴 `interrupt()`の前に非冪等性のある操作を実行しない
- 🔴 存在するかどうかを確認せずに新しいレコードを作成しない

```python
def node_a(state: State):
    # ❌ 悪い例: interrupt()の前に新しいレコードを作成
    # これは各再開時に重複レコードを作成する
    audit_id = db.create_audit_log({
        "user_id": state["user_id"],
        "action": "pending_approval",
        "timestamp": datetime.now()
    })
    approved = interrupt("Approve this change?")
    return {"approved": approved, "audit_id": audit_id}
```

## 関数として呼び出されるサブグラフでの使用

ノード内でサブグラフを呼び出す場合、親グラフはサブグラフが呼び出されたノードの**最初から**実行を再開し、`interrupt()`がトリガーされました。同様に、**サブグラフ**も`interrupt()`が呼び出されたノードの最初から再開されます。

```python
def node_in_parent_graph(state: State):
    some_code()  # <-- これは再開時に再実行される
    # サブグラフを関数として呼び出す
    # サブグラフには`interrupt()`呼び出しが含まれている
    subgraph_result = subgraph.invoke(some_input)
    # ...

def node_in_subgraph(state: State):
    some_other_code()  # <-- これも再開時に再実行される
    result = interrupt("What's your name?")
    # ...
```

## 中断を使ったデバッグ

グラフをデバッグしてテストするには、静的ブレークポイントとして中断を使用して、グラフの実行をノードごとにステップ実行できます。静的ブレークポイントは、ノードの実行前または実行後に定義されたポイントでトリガーされます。これらは、グラフをコンパイルする際に`interrupt_before`と`interrupt_after`を指定することで設定できます。

> **注意**: 静的ブレークポイントは、人間参加型ワークフローには推奨されません。代わりに`interrupt()`関数を使用してください。

### コンパイル時に設定

```python
graph = builder.compile(
    interrupt_before=["node_a"],
    interrupt_after=["node_b", "node_c"],
    checkpointer=checkpointer,
)

# スレッドIDをグラフconfigに渡す
config = {
    "configurable": {
        "thread_id": "some_thread"
    }
}

# ブレークポイントまでグラフを実行
graph.invoke(inputs, config=config)

# グラフを再開
graph.invoke(None, config=config)
```

- ブレークポイントは`compile`時に設定されます
- `interrupt_before`は、ノードが実行される前に実行を一時停止するノードを指定します
- `interrupt_after`は、ノードが実行された後に実行を一時停止するノードを指定します
- ブレークポイントを有効にするにはチェックポインターが必要です
- グラフは最初のブレークポイントに到達するまで実行されます
- グラフは、入力として`None`を渡すことで再開されます。これにより、グラフは次のブレークポイントに到達するまで実行されます

### LangGraph Studioの使用

[LangGraph Studio](https://docs.langchain.com/langsmith/studio)を使用して、グラフを実行する前にUIで静的ブレークポイントを設定できます。また、UIを使用して、実行中の任意のポイントでグラフ状態を検査できます。

## まとめ

中断（Interrupts）により、以下のことが可能になります：

1. **動的な中断**: コード内の任意の場所で`interrupt()`を呼び出して実行を一時停止
2. **人間参加型ワークフロー**: 重要なアクションの承認、状態のレビューと編集、入力の検証
3. **ツール内での中断**: ツール関数内で中断を使用して、実行前にツール呼び出しをレビュー
4. **デバッグ**: 静的ブレークポイントを使用してグラフの実行をステップ実行

適切に中断を実装することで、より安全で制御可能なエージェントシステムを構築できます。

## 次のステップ

- [P19: Subgraphs](./P19_subgraphs.md): サブグラフの概念
- [P20: Memory](./P20_memory.md): メモリ管理
- [P21: Durable Execution](./P21_durable_execution.md): 長時間実行の管理
