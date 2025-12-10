# Orchestrator-Workerパターンの詳細解説

このドキュメントでは、Orchestrator-Workerパターンで使用される`Send` APIと、リスト内包表記について、Pythonが苦手な方向けに詳しく解説します。

## 目次

1. [Send APIとは](#send-apiとは)
2. [リスト内包表記の理解](#リスト内包表記の理解)
3. [Sendオブジェクトの構造](#sendオブジェクトの構造)
4. [add_conditional_edgesでの使い方](#add_conditional_edgesでの使い方)
5. [通常の並列化との違い](#通常の並列化との違い)

## Send APIとは

`Send` APIは、LangGraphで複数のタスクを**同時に実行**するための仕組みです。

### 簡単な例え話

レストランで料理を作る流れに例えます。

**通常の方法（順番に実行）**:
```
1. サラダを作る（5分）
2. スープを作る（5分）
3. メインを作る（10分）
合計: 20分
```

**Send APIを使う方法（並列実行）**:
```
1. サラダを作る（5分） ← 同時に
2. スープを作る（5分） ← 同時に
3. メインを作る（10分） ← 同時に
合計: 10分（一番時間がかかるもの）
```

### なぜ便利なのか？

1. **速い**: 複数のタスクを同時に実行できる
2. **動的**: タスク数が実行時に決まる場合に対応できる
3. **効率的**: 待ち時間を減らせる

## リスト内包表記の理解

`assign_workers`関数では、リスト内包表記という書き方を使っています。

### 現在のコード

```python
def assign_workers(state: State):
    """計画の各セクションにワーカーを割り当てる"""
    # Send() API経由で並列にセクション書き込みを開始
    return [Send("llm_call", {"section": s}) for s in state["sections"]]
```

このコードは「リスト内包表記」という書き方です。同じ処理を通常のforループで書き直すと次のようになります。

### 通常のforループで書き直した版

```python
def assign_workers(state: State):
    """計画の各セクションにワーカーを割り当てる"""
    # 空のリストを作成（ここに結果を入れていく）
    result = []
    
    # state["sections"]の中の各セクション（s）に対して繰り返す
    for s in state["sections"]:
        # 各セクションに対してSendを作成
        send_command = Send("llm_call", {"section": s})
        # リストに追加
        result.append(send_command)
    
    # 完成したリストを返す
    return result
```

### 具体例で理解する

#### ステップ1: データの準備

`orchestrator`が実行され、3つのセクションが作成されたとします：

```python
state["sections"] = [
    セクション1（"はじめに"という名前）,
    セクション2（"本論"という名前）,
    セクション3（"まとめ"という名前）
]
```

#### ステップ2: forループの動作

```python
result = []  # 空のリスト

# 1回目の繰り返し: s = セクション1
send_command = Send("llm_call", {"section": セクション1})
result.append(send_command)
# result = [Send("llm_call", {"section": セクション1})]

# 2回目の繰り返し: s = セクション2
send_command = Send("llm_call", {"section": セクション2})
result.append(send_command)
# result = [Send("llm_call", {"section": セクション1}), 
#           Send("llm_call", {"section": セクション2})]

# 3回目の繰り返し: s = セクション3
send_command = Send("llm_call", {"section": セクション3})
result.append(send_command)
# result = [Send("llm_call", {"section": セクション1}), 
#           Send("llm_call", {"section": セクション2}),
#           Send("llm_call", {"section": セクション3})]
```

#### ステップ3: 最終結果

```python
return [
    Send("llm_call", {"section": セクション1}),
    Send("llm_call", {"section": セクション2}),
    Send("llm_call", {"section": セクション3})
]
```

### リスト内包表記の読み方

元のコード：
```python
[Send("llm_call", {"section": s}) for s in state["sections"]]
```

読み方：
1. `for s in state["sections"]` → `state["sections"]`の各要素を`s`として取り出す
2. `Send("llm_call", {"section": s})` → 各`s`に対して`Send`を作成
3. `[...]` → それらをリストにする

### セクション数が変わる場合

#### セクションが2つの場合
```python
state["sections"] = [セクション1, セクション2]
# 結果: [Send(...), Send(...)]  # 2つのSend
```

#### セクションが5つの場合
```python
state["sections"] = [セクション1, セクション2, セクション3, セクション4, セクション5]
# 結果: [Send(...), Send(...), Send(...), Send(...), Send(...)]  # 5つのSend
```

#### セクションが1つの場合
```python
state["sections"] = [セクション1]
# 結果: [Send(...)]  # 1つのSend
```

### 視覚的な理解

```
state["sections"] = [セクション1, セクション2, セクション3]
         ↓
    forループで1つずつ処理
         ↓
    ┌─────────┐
    │ セクション1 │ → Send("llm_call", {"section": セクション1})
    ├─────────┤
    │ セクション2 │ → Send("llm_call", {"section": セクション2})
    ├─────────┤
    │ セクション3 │ → Send("llm_call", {"section": セクション3})
    └─────────┘
         ↓
    [Send(...), Send(...), Send(...)]  ← リストとして返す
```

## Sendオブジェクトの構造

`Send`オブジェクトは、LangGraphの特殊なオブジェクトです。

### Sendオブジェクトの内容

`Send`オブジェクトには2つの重要な属性があります：

1. **`node`**: 実行するノード名（文字列）
   - 例: `"llm_call"`

2. **`arg`**: そのノードに渡すデータ（辞書）
   - 例: `{"section": "テストセクション"}`

### 実際の構造

```python
# 1つのSendオブジェクト
send_command = Send("llm_call", {"section": "セクション1"})
# 内容: Send(node='llm_call', arg={'section': 'セクション1'})

# 複数のSendオブジェクトのリスト
sends = [
    Send("llm_call", {"section": "セクション1"}),
    Send("llm_call", {"section": "セクション2"}),
    Send("llm_call", {"section": "セクション3"})
]
# 内容: [
#     Send(node='llm_call', arg={'section': 'セクション1'}),
#     Send(node='llm_call', arg={'section': 'セクション2'}),
#     Send(node='llm_call', arg={'section': 'セクション3'})
# ]
```

### Sendオブジェクトの意味

`Send`オブジェクトは「**このノードを、このデータで実行して**」という**実行指示**を表します。

- `Send("llm_call", {"section": セクション1})` = 「`llm_call`ノードを、`{"section": セクション1}`というデータで実行して」
- `Send("llm_call", {"section": セクション2})` = 「`llm_call`ノードを、`{"section": セクション2}`というデータで実行して」

## add_conditional_edgesでの使い方

`Send` APIを使う場合、`add_conditional_edges`の使い方が通常とは異なります。

### コード例

```python
orchestrator_worker_builder.add_conditional_edges(
    "orchestrator", assign_workers, ["llm_call"]
)
```

### 第3引数`["llm_call"]`の意味

通常の条件付きエッジ（例：`p14_4_routing.py`）では、第3引数は**辞書**です：

```python
# 通常の条件付きエッジ（辞書を使う）
router_builder.add_conditional_edges(
    "llm_call_router",
    route_decision,
    {
        "llm_call_1": "llm_call_1",  # route_decisionが"llm_call_1"を返したら
        "llm_call_2": "llm_call_2",  # route_decisionが"llm_call_2"を返したら
        "llm_call_3": "llm_call_3",  # route_decisionが"llm_call_3"を返したら
    },
)
```

一方、`Send`を使う場合は、第3引数は**リスト**です：

```python
# Sendを使う場合（リストを使う）
orchestrator_worker_builder.add_conditional_edges(
    "orchestrator", 
    assign_workers,  # この関数がSendオブジェクトのリストを返す
    ["llm_call"]      # このリストは「llm_callノードに送信可能」という許可リスト
)
```

### 動作の流れ

1. `orchestrator`ノードが実行される
2. `assign_workers`関数が呼ばれる
3. `assign_workers`が`Send`オブジェクトのリストを返す：
   ```python
   [
       Send(node='llm_call', arg={'section': セクション1}),
       Send(node='llm_call', arg={'section': セクション2}),
       Send(node='llm_call', arg={'section': セクション3})
   ]
   ```
4. LangGraphが各`Send`オブジェクトを確認：
   - `Send`の`node`属性が`"llm_call"`か確認
   - `["llm_call"]`に含まれているか確認（この場合は常にOK）
5. 各`Send`オブジェクトの`arg`を`llm_call`ノードに渡して**並列実行**

### 視覚的な理解

```
orchestrator実行
    ↓
assign_workers実行
    ↓
[
    Send(node='llm_call', arg={'section': セクション1}),
    Send(node='llm_call', arg={'section': セクション2}),
    Send(node='llm_call', arg={'section': セクション3})
]
    ↓
LangGraphが各Sendを処理
    ↓
┌─────────────────────────────────────┐
│ llm_call(WorkerState(section=セクション1)) │ ← 並列実行
│ llm_call(WorkerState(section=セクション2)) │ ← 並列実行
│ llm_call(WorkerState(section=セクション3)) │ ← 並列実行
└─────────────────────────────────────┘
    ↓
すべて完了したら synthesizer へ
```

## 通常の並列化との違い

`Send` APIを使った並列化と、通常の並列化（`p14_3_parallelization.py`）の違いを説明します。

### 主な違い

#### 1. タスク数の決定タイミング

**通常の並列化（p14_3_parallelization.py）**:
- **事前に**タスク数が決まっている（固定）
- コードに3つのノード（`call_llm_1`, `call_llm_2`, `call_llm_3`）を明示的に定義

```python
parallel_builder.add_node("call_llm_1", call_llm_1)
parallel_builder.add_node("call_llm_2", call_llm_2)
parallel_builder.add_node("call_llm_3", call_llm_3)
```

**Send APIを使った並列化（p14_5_orchestrator_worker.py）**:
- **実行時に**タスク数が決まる（動的）
- 同じノード（`llm_call`）を複数回、異なるデータで実行

```python
def assign_workers(state: State):
    return [Send("llm_call", {"section": s}) for s in state["sections"]]
```

#### 2. エッジの定義方法

**通常の並列化**:
- エッジを**静的に**定義（コードに明記）

```python
parallel_builder.add_edge(START, "call_llm_1")
parallel_builder.add_edge(START, "call_llm_2")
parallel_builder.add_edge(START, "call_llm_3")
parallel_builder.add_edge("call_llm_1", "aggregator")
parallel_builder.add_edge("call_llm_2", "aggregator")
parallel_builder.add_edge("call_llm_3", "aggregator")
```

**Send API**:
- エッジを**動的に**生成（実行時に決定）

```python
orchestrator_worker_builder.add_conditional_edges(
    "orchestrator", assign_workers, ["llm_call"]
)
```

#### 3. ノードの使い方

**通常の並列化**:
- 各タスクごとに**専用のノード関数**を用意

```python
def call_llm_1(state: State):
    """最初のLLM呼び出しでジョークを生成"""
    msg = llm.invoke(f"{state['topic']}についてジョークを書いてください")
    return {"joke": msg.content}

def call_llm_2(state: State):
    """2回目のLLM呼び出しでストーリーを生成"""
    msg = llm.invoke(f"{state['topic']}についてストーリーを書いてください")
    return {"story": msg.content}

def call_llm_3(state: State):
    """3回目のLLM呼び出しで詩を生成"""
    msg = llm.invoke(f"{state['topic']}について詩を書いてください")
    return {"poem": msg.content}
```

**Send API**:
- **1つのノード関数**を複数回、異なるデータで実行

```python
def llm_call(state: WorkerState):
    """ワーカーがレポートのセクションを書く"""
    section = llm.invoke([
        SystemMessage(...),
        HumanMessage(
            content=f"セクション名: {state['section'].name}、説明: {state['section'].description}"
        ),
    ])
    return {"completed_sections": [section.content]}
```

### 具体例で理解する

#### 通常の並列化の例

レストランのメニューが**固定**の場合：
- メニューA（サラダ）→ シェフ1
- メニューB（スープ）→ シェフ2
- メニューC（メイン）→ シェフ3

メニューが変わるたびに、シェフを追加・削除する必要がある。

#### Send APIの例

注文に応じて料理数が**変わる**場合：
- 注文が3品なら → 同じシェフが3回、異なる料理を作る
- 注文が5品なら → 同じシェフが5回、異なる料理を作る

シェフは1人で、注文数に応じて動的に対応できる。

### 比較表

| 項目 | 通常の並列化 | Send API |
|------|------------|----------|
| タスク数 | 固定（コードで決定） | 動的（実行時に決定） |
| ノード定義 | タスクごとに専用ノード | 1つのノードを再利用 |
| エッジ定義 | 静的に定義 | 動的に生成 |
| 柔軟性 | 低い（変更にコード修正が必要） | 高い（データに応じて自動調整） |
| 適した用途 | タスク数が固定で明確な場合 | タスク数が変動する場合 |

## まとめ

### Send APIの要点

- `Send`オブジェクトは「このノードを、このデータで実行して」という**実行指示**
- `assign_workers`の戻り値は`Send`オブジェクトの**リスト**
- `["llm_call"]`は「`llm_call`ノードに送信可能」という**許可リスト**

### リスト内包表記の要点

- `state["sections"]`の要素数だけ繰り返す
- 各セクションに対して`Send`を作成
- それらをリストにして返す

### なぜSend APIを使うのか？

- **orchestrator**が、topicをもとに、sections（セクションズ）を作成
- sections（セクションズ）は、**実行するまで、何個になるか解らない**
- だから**動的に割り当てる**必要がある

`Send` APIは、実行時にタスク数が決まる場合（例：レポートのセクション数が変わる）に適しています。

