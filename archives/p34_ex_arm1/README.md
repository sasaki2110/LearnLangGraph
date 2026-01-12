# p34_ex_arm1 - ロボットアーム学習エージェント

このプロジェクトは、ユーザーの指示に基づいてロボットアームを制御するLangGraphエージェントです。
p31_streaming相当のロギング・ストリーミングを実装しています。

## 構造

```
p34_ex_arm1/
├── my_agent/              # プロジェクトコード
│   ├── utils/             # グラフ用のユーティリティ
│   │   ├── __init__.py
│   │   ├── state.py       # グラフの状態定義
│   │   ├── nodes.py       # グラフ用のノード関数（ログ付き）
│   │   ├── tools.py       # ロボットアーム用のツール関数
│   │   └── logging_config.py  # ロギング設定
│   ├── __init__.py
│   └── agent.py          # グラフを構築するコード（ログ付き）
├── tests/                # テストファイル
│   ├── __init__.py
│   ├── test_invoke.py    # invokeのテスト
│   └── test_stream.py    # streamのテスト
├── langgraph.json         # LangGraph設定ファイル
└── README.md             # このファイル
```

## 機能

このエージェントは、以下の処理を行います：

1. **Extractor（抽出）**: ユーザーメッセージから指示を取得します
2. **Planner（計画）**: LLMを使用して、全体のタスクリストを生成します（構造化出力を使用）
3. **Task Selector（タスク選択）**: 依存関係が満たされた次のタスクを選択します
4. **Tool Executor（ツール実行）**: 選択されたタスクを実行します
   - `get_object_position(item_name)`: 物体の位置を取得（結果は`object_positions`に保存）
   - `move_arm_to(x, y, z)`: アームを指定座標に移動
   - `control_gripper(action)`: グリッパーを開閉
5. **Task Updater（タスク更新）**: 実行完了したタスクを完了済みにマークします
6. **Verifier（検証）**: すべてのタスクが完了したかどうかを確認します
7. **Final Answer（最終回答）**: タスクが完了した場合、LLMを使用して最終結果を整形して返却します

### ToDos（タスクリスト）ベースの設計

このエージェントは、ToDos（タスクリスト）ベースの設計を採用しています：
- **タスクの分解**: Plannerが全体のタスクを複数のステップに分解
- **依存関係の管理**: 各タスクは依存するタスクのIDリストを持つ
- **順次実行**: 依存関係が満たされたタスクから順次実行
- **状態の保存**: 取得した物体位置や実行結果を状態に保存

### 無限ループ防止機能

実行可能なタスクが存在しない場合（依存関係が満たされないなど）、無限ループを防止するため自動的に終了します。

## ステート

- `messages`: メッセージ履歴
- `gripper_position_x`, `gripper_position_y`, `gripper_position_z`: グリッパーの位置
- `gripper_state`: グリッパーの状態（"open" または "close"）
- `instruction`: ユーザーからの指示
- `task_list`: 生成されたタスクリスト（List[Task]）
- `completed_tasks`: 完了したタスクの結果（List[dict]）
- `object_positions`: 取得済みの物体位置（dict、例: {"赤いコップ": (10.0, 20.0, 5.0)}）
- `current_task_id`: 現在実行中のタスクID
- `task_completed`: すべてのタスクが完了したかどうか

## ツール

| 関数名 | 引数 | 説明 |
| --- | --- | --- |
| `get_object_position(item_name)` | `item_name` (str) | 指定した物体の3次元座標を返す |
| `move_arm_to(x, y, z)` | `x, y, z` (float) | アームの先端（グリッパー）を指定座標へ移動させる |
| `control_gripper(action)` | `action` ("open" or "close") | グリッパーの開閉を行う |

## グラフ構造

```
start -> extractor -> planner -> task_selector -> tool_executor -> task_updater -> verifier
                                                                                    ↓
                                                                               条件分岐
                                                                                ↓      ↓
                                                                          final_answer  task_selector
                                                                                ↓
                                                                              end
```

条件分岐の詳細:
- **task_completed == True**: 最終回答を生成（final_answer -> end）
- **task_completed == False かつ 実行可能なタスクがある**: 次のタスクを選択（task_selector）
- **task_completed == False かつ 実行可能なタスクがない**: 無限ループ防止のため終了（end）

## セットアップ

### 1. 依存関係のインストール

以下の依存関係が必要です：
- langchain
- langchain-openai
- langgraph
- python-dotenv (オプション)

親フォルダで実行済みの場合、それらを使用できます。

### 2. 環境変数の設定

親フォルダで実行済み。

### 3. LangGraph Studioで実行

```bash
cd /root/LearnLangGraph/archives/p34_ex_arm1
langgraph dev
```

サーバーが起動すると、以下のURLでアクセスできます：
- **APIエンドポイント**: `http://127.0.0.1:2024`
- **Studio UI**: `https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024`

## テスト

### invokeのテスト

```bash
cd /root/LearnLangGraph/archives/p34_ex_arm1
python -m pytest tests/test_invoke.py -v
```

または、直接実行：

```bash
python tests/test_invoke.py
```

### streamのテスト

```bash
cd /root/LearnLangGraph/archives/p34_ex_arm1
python -m pytest tests/test_stream.py -v
```

または、直接実行：

```bash
python tests/test_stream.py
```

## ロギング機能

### ログファイル

- **通常ログ**: `p34_ex_arm1.log` (デフォルト)
- **エラーログ**: `p34_ex_arm1_error.log` (ERROR/CRITICALレベルのみ)

### 環境変数

以下の環境変数でロギングをカスタマイズできます：

- `LOG_LEVEL`: ログレベル (DEBUG, INFO, WARNING, ERROR) - デフォルト: INFO
- `LOG_FILE`: ログファイル名 - デフォルト: `p34_ex_arm1.log`
- `LOG_DIR`: ログファイルのディレクトリ - デフォルト: `.` (現在のディレクトリ)
- `LOG_USE_PYTHON_ROTATION`: Pythonローテーションを使用するか (true/false) - デフォルト: true
- `ENVIRONMENT`: 環境 (production, development, staging) - デフォルト: development

### ログの内容

自前実装部分（nodes.py, agent.py, tools.py）に以下のような日本語ログが出力されます：

- **エージェント初期化**: モデルの初期化、グラフの構築
- **指示抽出**: ユーザーメッセージから指示を抽出する処理
- **プランニング**: LLM呼び出し開始/完了、生成されたタスクリスト
- **タスク選択**: 選択されたタスクの情報
- **ツール実行**: 各ツールの実行状況、取得した位置情報
- **タスク更新**: 完了したタスクの情報
- **検証**: 状態の確認、タスク完了判定
- **最終回答生成**: LLM呼び出し開始/完了、生成された最終回答
- **エラー**: エラー発生時の詳細情報

### ログの確認方法

1. **コンソール出力**: 実行時にコンソールにログが表示されます
2. **ログファイル**: `p34_ex_arm1.log` ファイルを確認
3. **エラーログ**: `p34_ex_arm1_error.log` ファイルでエラーのみを確認

## ストリーミング

p31_streaming相当のストリーミング機能を実装しています。

### 使用例

```python
from my_agent.agent import graph
from langchain.messages import HumanMessage

initial_state = {
    "messages": [HumanMessage(content="赤いコップを青いトレイに置いて")],
    "gripper_position_x": 0.0,
    "gripper_position_y": 0.0,
    "gripper_position_z": 0.0,
    "gripper_state": "open",
    "executed_tool": None,
    "tool_args": None,
    "instruction": None,
    "task_completed": False,
    "planner_call_count": 0
}

# ストリーミング実行
for chunk in graph.stream(initial_state, stream_mode="updates"):
    node_name = list(chunk.keys())[0]
    print(f"[{node_name}] {chunk[node_name]}")
```

## 使用例

### 基本的な使用

```python
from my_agent.agent import graph
from langchain.messages import HumanMessage

initial_state = {
    "messages": [HumanMessage(content="赤いコップを青いトレイに置いて")],
    "gripper_position_x": 0.0,
    "gripper_position_y": 0.0,
    "gripper_position_z": 0.0,
    "gripper_state": "open",
    "instruction": None,
    "task_completed": False
}

result = graph.invoke(initial_state)
print(f"タスク完了: {result['task_completed']}")
print(f"生成されたタスク数: {len(result.get('task_list', []))}")
print(f"完了したタスク数: {len(result.get('completed_tasks', []))}")
print(f"取得した物体位置: {result.get('object_positions', {})}")
# 最終回答はmessagesに含まれています
if result.get("messages"):
    for msg in result["messages"]:
        if hasattr(msg, "content"):
            print(f"最終回答: {msg.content}")
```
