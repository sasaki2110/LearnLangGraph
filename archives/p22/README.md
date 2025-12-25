# p22 - タイムトラベル（Time Travel）の例 - 構造化版

このプロジェクトは、`docs/P22_timetravel.md`をベースに、`docs/P23_application_structure.md`に従って構造化したものです。

## 変更点

- `docs/P23_application_structure.md`に従い、構造化
- LangSmith studioで実行する前提で、graphのコンパイルまでとする（invoke以降はUIに任せる）
- pytestのテストも用意し、invokeとタイムトラベル機能を確認

## 構造

```
p22/
├── my_agent/              # プロジェクトコード
│   ├── utils/             # グラフ用のユーティリティ
│   │   ├── __init__.py
│   │   ├── state.py       # グラフの状態定義
│   │   └── nodes.py       # グラフ用のノード関数
│   ├── __init__.py
│   └── agent.py          # グラフを構築するコード
├── tests/                 # テストコード
│   ├── __init__.py
│   ├── conftest.py       # 共通フィクスチャ
│   └── test_graph.py     # グラフの統合テスト
├── langgraph.json         # LangGraph設定ファイル
└── README.md             # このファイル
```

## 実装内容

1. **グラフ構造**: `generate_topic → write_message` の順で実行
2. **タイムトラベル**: 過去のチェックポイントから実行を再開
3. **状態の更新**: `update_state`を使用して状態を変更して再実行

## 主な機能

- **State定義**: トピックとメッセージを管理
- **generate_topic**: トピックを生成
- **write_message**: トピックに基づいてメッセージを生成
- **チェックポインター**: テスト用に`MemorySaver`を使用（LangSmith studioでは自動処理）

## セットアップ

### 1. 仮想環境の有効化

親ディレクトリ（`/root/LearnLangGraph`）で仮想環境を作成・有効化します。

```bash
# プロジェクトルートで仮想環境を作成（初回のみ）
cd /root/LearnLangGraph
python3 -m venv venv

# 仮想環境を有効化
source venv/bin/activate  # Linux/macOS
# または
# venv\Scripts\activate  # Windows
```

### 2. 依存関係のインストール

親ディレクトリの`requirements.txt`から依存関係をインストールします。

```bash
# 仮想環境が有効化されている状態で
pip install -r requirements.txt
```

## LangSmith Studioで実行

### 1. LangGraph Studioで起動

```bash
# 仮想環境が有効化されている状態で
cd archives/p22
langgraph dev
```

サーバーが起動すると、以下のURLでアクセスできます：
- **APIエンドポイント**: `http://127.0.0.1:2024`
- **Studio UI**: `https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024`

### 2. タイムトラベルの使用

#### 基本的な実行

1. 初期状態でグラフを実行すると、`generate_topic`が実行され、トピックが生成される
2. `write_message`が実行され、トピックに基づいてメッセージが生成される
3. 実行結果の`steps`フィールドに実行履歴が記録される

#### LangSmith Studioでの確認方法

**実行履歴の確認:**
1. グラフを実行後、Studio UIで実行履歴を確認
2. 各チェックポイントで`steps`フィールドを確認すると、どのノードが実行されたかが分かる
3. 例: `["[10:30:45] Step 1: generate_topic → topic='cats'", "[10:30:45] Step 2: write_message → message='A message about cats'"]`

**タイムトラベルの実行:**
1. 実行履歴から、`generate_topic`実行後のチェックポイントを選択
2. そのチェックポイントの状態を確認（`topic`フィールドを確認）
3. `update_state`を使用して状態を変更（例：`topic`を"chickens"に変更）
4. チェックポイントから実行を再開すると、新しいトピックでメッセージが生成される
5. 新しい実行の`steps`フィールドを確認すると、タイムトラベル後の実行が記録される

**確認のポイント:**
- `steps`フィールドで実行の流れを追跡できる
- タイムトラベル前と後の`steps`を比較すると、分岐が確認できる
- 各ステップにタイムスタンプが含まれているため、実行順序が分かる

## テストの実行

**注意**: テストを実行する前に、親ディレクトリで仮想環境を有効化してください。

```bash
# 親ディレクトリで仮想環境を有効化
cd /root/LearnLangGraph
source venv/bin/activate  # Linux/macOS

# p22ディレクトリに移動
cd archives/p22

# すべてのテストを実行
pytest

# 特定のテストファイルを実行
pytest tests/test_graph.py

# 詳細な出力で実行
pytest -v
```

### 実装されているテスト

- **test_graph_invoke**: グラフをinvokeできることを確認
- **test_graph_get_state_history**: 実行履歴を取得できることを確認
- **test_time_travel_update_state**: タイムトラベルで状態を更新して再実行できることを確認
- **test_time_travel_resume_from_checkpoint**: チェックポイントから実行を再開できることを確認

## タイムトラベルの使用方法

### 1. グラフを実行

```python
config = {"configurable": {"thread_id": "thread-1"}}
result = graph.invoke({}, config)
```

### 2. チェックポイントを特定

```python
states = list(graph.get_state_history(config))
for state in states:
    print(f"Checkpoint ID: {state.config['configurable']['checkpoint_id']}")
    print(f"Values: {state.values}")
```

### 3. 状態を更新（オプション）

```python
selected_state = states[1]  # トピック生成後の状態
new_config = graph.update_state(
    selected_state.config,
    values={"topic": "chickens"}
)
```

### 4. チェックポイントから実行を再開

```python
new_result = graph.invoke(None, new_config)
```

## 重要なポイント

- タイムトラベルを使用するにはチェックポインターが必要です
- 過去のチェックポイントから実行を再開すると、新しいフォーク（分岐）が作成されます
- `update_state`を使用して状態を変更すると、新しいチェックポイントが作成されます
- LangGraph API（LangSmith studio）では、persistenceは自動的に処理されます

## 参考資料

- [P22: Time Travel](../docs/P22_timetravel.md)
- [P23: Application Structure](../docs/P23_application_structure.md)

