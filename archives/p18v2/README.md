# p18v2 - 基本的な中断（Interrupts）の例 - 構造化版

このプロジェクトは、`archives/p18`をベースに、`docs/P23_application_structure.md`に従って構造化したものです。

## 変更点

- `docs/P23_application_structure.md`に従い、構造化
- LangSmith studioで実行する前提で、graphのコンパイルまでとする（invoke以降はUIに任せる）
- pytestのテストも用意し、invokeできることを確認

## 構造

```
p18v2/
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

1. **グラフ構造**: `nodeA → nodeB → nodeC` の順で実行
2. **中断の実装**: `nodeB`で`interrupt()`を使用してユーザー承認を要求
3. **再開処理**: `Command(resume=True)`で再開（LangSmith studioのUIで実行）

## 主な機能

- **State定義**: メッセージ、承認状態、アクションを管理
- **node_a**: 初期処理とアクションの準備
- **node_b**: `interrupt()`で承認を要求（中断）
- **node_c**: 承認結果に基づいて最終処理を実行
- **チェックポインター**: `MemorySaver`を使用（中断に必須）

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
cd archives/p18v2
langgraph dev
```

サーバーが起動すると、以下のURLでアクセスできます：
- **APIエンドポイント**: `http://127.0.0.1:2024`
- **Studio UI**: `https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024`

### 2. 実行フロー

1. 初期状態でグラフを実行すると、`nodeA`が実行される
2. `nodeB`で`interrupt()`が呼び出され、実行が一時停止
3. 中断情報が`result["__interrupt__"]`に表示される
4. LangSmith studioのUIで`Command(resume=True)`を実行して再開
5. `nodeB`が再実行され、`interrupt()`の戻り値として`True`を受け取る
6. `nodeC`が実行される（承認に基づく最終処理）

## テストの実行

**注意**: テストを実行する前に、親ディレクトリで仮想環境を有効化してください。

```bash
# 親ディレクトリで仮想環境を有効化
cd /root/LearnLangGraph
source venv/bin/activate  # Linux/macOS

# p18v2ディレクトリに移動
cd archives/p18v2

# すべてのテストを実行
pytest

# 特定のテストファイルを実行
pytest tests/test_graph.py

# 詳細な出力で実行
pytest -v
```

### 実装されているテスト

- **test_graph_invoke_with_interrupt**: グラフをinvokeして中断が発生することを確認
- **test_graph_invoke_with_resume**: グラフをinvokeして再開できることを確認
- **test_graph_get_state**: グラフの状態を取得できることを確認

## 重要なポイント

- `interrupt()`を使用するにはチェックポインターが必要です
- 同じ`thread_id`を使用して再開する必要があります
- `Command(resume=...)`の値が`interrupt()`の戻り値になります
- ノードは最初から再実行されるため、`interrupt()`の前のコードも再実行されます

## 参考資料

- [P23: Application Structure](../docs/P23_application_structure.md)
- [P18: 基本的な中断（Interrupts）の例](../p18/p18_simple_interrupts.md)

