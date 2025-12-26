# p21_tasks - LangGraph Tasks（タスク）の実装例

このプロジェクトは、P21_tasks.mdに従ったタスクの使用例を実装したものです。
タスクを使用して、非決定的な操作や副作用を持つ操作をラップする方法を示しています。

## 概要

この例では、複数のURLに対してHTTPリクエストを行うワークフローを実装しています。
各リクエストはタスクとしてラップされており、ワークフローが再開された際に再実行されず、
永続化レイヤーから結果が取得されます。

## 構造

```
p21_tasks/
├── my_agent/              # プロジェクトコード
│   ├── utils/             # グラフ用のユーティリティ
│   │   ├── __init__.py
│   │   ├── state.py       # グラフの状態定義
│   │   └── nodes.py       # グラフ用のノード関数（タスクを使用）
│   ├── __init__.py
│   └── agent.py          # グラフを構築するコード
├── tests/                 # テストコード
│   ├── __init__.py
│   └── test_invoke.py    # invokeを確認するテスト
├── langgraph.json         # LangGraph設定ファイル
└── README.md             # このファイル
```

## セットアップ

### 1. 依存関係のインストール

親フォルダで実行済み。

### 2. 環境変数の設定

親フォルダで実行済み。

### 3. LangGraph Studioで実行

```bash
cd archives/p21_tasks
langgraph dev
```

サーバーが起動すると、以下のURLでアクセスできます：
- **APIエンドポイント**: `http://127.0.0.1:2024`
- **Studio UI**: `https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024`

## 機能

このエージェントは、以下の機能を提供します：

1. **複数のURLを処理**: 複数のURLに対してHTTPリクエストを並列で実行
2. **タスクの使用**: 各リクエストをタスクとしてラップし、再実行を防止
3. **永続化**: チェックポインタを使用して実行履歴を保存
4. **再開可能**: 同じスレッドIDで再実行した場合、タスクは再実行されず、永続化レイヤーから結果が取得される

## 実装の詳細

### タスクの定義

`my_agent/utils/nodes.py`で、HTTPリクエストを行うタスクを定義しています：

```python
@task
def _make_request(url: str) -> str:
    """リクエストを行うタスク"""
    return requests.get(url).text[:100]
```

### ノードでのタスクの使用

ノード内でタスクを作成し、結果を取得します：

```python
def call_api(state: State) -> dict:
    """APIリクエストを行うノードの例"""
    tasks = [_make_request(url) for url in state['urls']]
    results = [task.result() for task in tasks]
    return {"results": results}
```

### グラフのコンパイル

`my_agent/agent.py`で、チェックポインタを指定してグラフをコンパイルしています：

```python
checkpointer = MemorySaver()
graph = builder.compile(checkpointer=checkpointer)
```

## テストの実行

**注意**: テストを実行する前に、親ディレクトリで仮想環境を有効化してください。

```bash
# 親ディレクトリで仮想環境を有効化
cd /root/LearnLangGraph
source venv/bin/activate  # Linux/macOS

# p21_tasksディレクトリに移動
cd archives/p21_tasks

# すべてのテストを実行
pytest

# 特定のテストファイルを実行
pytest tests/test_invoke.py

# 詳細な出力で実行
pytest -v
```

### 実装されているテスト

- **test_graph_invoke**: グラフをinvokeして結果を確認
- **test_graph_invoke_multiple_urls**: 複数のURLを処理するテスト
- **test_graph_invoke_with_same_thread_id**: 同じスレッドIDで再実行した場合、タスクが再実行されないことを確認
- **test_graph_invoke_state_structure**: 状態の構造を確認

## タスクの利点

1. **再実行の防止**: ワークフローが再開されても、タスクは再実行されず、永続化レイヤーから結果が取得される
2. **一貫性の保証**: 同じ実行内で同じタスクは同じ結果を返す
3. **柔軟性**: ノード内の複数の操作を個別のタスクとして管理できる

## 関連ドキュメント

- [P21: Tasks（タスク）](../../docs/P21_tasks.md): タスクの詳細な説明
- [P21: Durable Execution](../../docs/P21_durable_execution.md): 耐久性のある実行の詳細
- [P16: Persistence](../../docs/P16_persistence.md): 状態の永続化の詳細

