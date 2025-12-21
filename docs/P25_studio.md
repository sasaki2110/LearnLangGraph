# LangGraph Studio

このドキュメントでは、LangGraph Studio（LangSmith Studio）の使い方について解説します。視覚的なグラフ編集、デバッグ、開発支援機能を説明します。

公式ドキュメント: https://docs.langchain.com/oss/python/langgraph/studio

## 概要

LangGraph Studio（LangSmith Studio）は、LangGraphエージェントを視覚的に開発・テストするための無料のWebインターフェースです。ローカルマシンで実行中のエージェントに接続し、以下の機能を提供します：

- **視覚的なグラフ編集**: グラフ構造を視覚的に理解・編集
- **リアルタイムデバッグ**: エージェントの実行をリアルタイムで監視・デバッグ
- **実行トレースの可視化**: 各ステップの詳細（プロンプト、ツール呼び出し、結果）を表示
- **状態の検査**: 中間状態を検査し、問題を特定
- **ホットリロード**: コード変更を即座に反映

### 主な利点

- **開発効率の向上**: コードを書かずにエージェントの動作を確認・調整
- **デバッグの容易さ**: 実行フローを視覚的に追跡し、問題を迅速に特定
- **プロンプトの反復**: プロンプトを変更して即座に結果を確認
- **状態の理解**: 各ノードでの状態変化を詳細に確認

## 前提条件

### 1. LangSmithアカウント

LangGraph Studioを使用するには、LangSmithアカウントが必要です。

1. [smith.langchain.com](https://smith.langchain.com)にアクセス
2. 無料アカウントを作成（またはログイン）

### 2. LangSmith APIキー

APIキーを取得して設定します。

1. [LangSmith設定ページ](https://smith.langchain.com/settings)にアクセス
2. 「API Keys」セクションでAPIキーを作成
3. 作成したAPIキーをコピー

### 3. トレーシングの設定（オプション）

データをLangSmithに送信したくない場合は、トレーシングを無効化できます。

```env
# .env
LANGSMITH_TRACING=false
```

トレーシングを無効化すると、データはローカルサーバーにのみ保存され、LangSmithには送信されません。

## セットアップ手順

### ステップ1: LangGraph CLIのインストール

LangGraph CLIをインストールします。Python 3.11以上が必要です。

```bash
pip install --upgrade "langgraph-cli[inmem]"
```

`[inmem]`オプションは、メモリベースのチェックポインタを使用する場合に必要です。

### ステップ2: エージェントの準備

既存のLangGraphエージェントを使用するか、新しいエージェントを作成します。

#### 例: シンプルなエージェント

```python
# src/agent.py
from langchain.agents import create_agent
from langchain_core.tools import tool

@tool
def send_email(to: str, subject: str, body: str) -> str:
    """メールを送信するツール"""
    # メール送信ロジック
    return f"Email sent to {to}"

# エージェントを作成
agent = create_agent(
    "gpt-4o",
    tools=[send_email],
    system_prompt="You are an email assistant. Always use the send_email tool.",
)
```

`create_agent`関数は、自動的にコンパイル済みのLangGraphグラフを返します。

### ステップ3: 環境変数の設定

プロジェクトのルートディレクトリに`.env`ファイルを作成し、LangSmith APIキーを設定します。

```env
# .env
LANGSMITH_API_KEY=lsv2_...
```

**重要**: `.env`ファイルはバージョン管理（Gitなど）にコミットしないでください。`.gitignore`に追加することを推奨します。

### ステップ4: LangGraph設定ファイルの作成

プロジェクトのルートディレクトリに`langgraph.json`ファイルを作成します。

```json
{
  "dependencies": ["."],
  "graphs": {
    "agent": "./src/agent.py:agent"
  },
  "env": ".env"
}
```

#### 設定ファイルの説明

- **`dependencies`**: プロジェクトの依存関係を指定（`"."`は現在のディレクトリ）
- **`graphs`**: デプロイするグラフを指定
  - 形式: `"<グラフ名>": "<ファイルパス>:<変数名>"`
  - 例: `"./src/agent.py:agent"` → `src/agent.py`ファイルの`agent`変数
- **`env`**: 環境変数ファイルのパス

詳細は[Application Structure](./P23_application_structure.md)のドキュメントを参照してください。

### ステップ5: 依存関係のインストール

プロジェクトの依存関係をインストールします。

```bash
pip install langchain langchain-openai
```

または、`requirements.txt`を使用する場合：

```bash
pip install -r requirements.txt
```

### ステップ6: Studioでエージェントを表示

開発サーバーを起動して、Studioに接続します。

```bash
langgraph dev
```

サーバーが起動すると、以下のURLでアクセスできます：

- **APIエンドポイント**: `http://127.0.0.1:2024`
- **Studio UI**: `https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024`

**注意**: Safariブラウザは`localhost`への接続をブロックする場合があります。その場合は、`--tunnel`オプションを使用してセキュアなトンネル経由でアクセスできます。

```bash
langgraph dev --tunnel
```

## Studioの使い方

### エージェントビュー

Studioに接続すると、エージェントの視覚的な表現が表示されます。

- **グラフ構造**: ノードとエッジが視覚的に表示される
- **実行トレース**: 各ステップの詳細が表示される
- **状態の検査**: 各ノードでの状態変化を確認できる

### エージェントの実行

1. **入力の入力**: チャットインターフェースまたはAPI経由で入力
2. **実行の監視**: リアルタイムで実行フローを確認
3. **結果の確認**: 最終的な出力と中間状態を確認

### 実行トレースの確認

Studioでは、以下の情報を確認できます：

- **プロンプト**: LLMに送信されたプロンプト
- **ツール呼び出し**: 呼び出されたツールとその引数
- **ツール結果**: ツールの戻り値
- **トークン/レイテンシー**: パフォーマンスメトリクス
- **例外**: エラーが発生した場合の詳細情報

### ホットリロード

開発サーバーはホットリロードをサポートしています：

1. コードを変更（プロンプトやツールシグネチャなど）
2. Studioが自動的に変更を検出
3. 即座に反映される（サーバーの再起動不要）

### 会話スレッドの管理

Studioでは、会話スレッドを管理できます：

- **スレッドの作成**: 新しい会話を開始
- **スレッドの再実行**: 任意のステップから再実行して変更をテスト
- **スレッドの履歴**: 過去の会話を確認

## デバッグ機能

### 実行フローの追跡

Studioでは、エージェントの実行フローを詳細に追跡できます：

1. **ノードの実行順序**: どのノードが実行されたかを確認
2. **状態の遷移**: 各ノードでの状態変化を確認
3. **条件分岐**: 条件付きエッジでの分岐を確認

### 状態の検査

各ノードでの状態を詳細に検査できます：

- **入力状態**: ノードに渡された状態
- **出力状態**: ノードから返された状態
- **状態の差分**: 状態の変化を確認

### エラーのデバッグ

エラーが発生した場合、Studioでは以下を確認できます：

- **エラーメッセージ**: 例外の詳細
- **エラー発生時の状態**: エラーが発生した時点の状態
- **スタックトレース**: エラーの発生箇所

### ブレークポイントの設定

Studioでは、グラフを実行する前にUIで静的ブレークポイントを設定できます：

1. グラフビューでノードを選択
2. ブレークポイントを設定
3. 実行時にそのノードで停止
4. 状態を検査してから続行

詳細は[Interrupts](./P18_interrupts.md)のドキュメントを参照してください。

## 高度な機能

### プロンプトの反復

Studioでは、プロンプトを変更して即座に結果を確認できます：

1. コードでプロンプトを変更
2. ホットリロードで自動反映
3. 同じスレッドから再実行
4. 結果を比較

### データセットへの追加

実行結果をデータセットに追加して、後で評価に使用できます：

1. ノードの実行結果を選択
2. 「Add to dataset」をクリック
3. データセットに追加
4. 評価に使用

### LangSmith統合

StudioはLangSmithと統合されており、以下の機能が利用できます：

- **トレーシング**: 実行トレースをLangSmithに保存
- **評価**: データセットを使用した評価
- **プロンプトエンジニアリング**: プロンプトの最適化

## 使用例

### 例1: シンプルなエージェントのデバッグ

```python
# src/agent.py
from langchain.agents import create_agent
from langchain_core.tools import tool

@tool
def calculate(expression: str) -> str:
    """数式を計算するツール"""
    try:
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Error: {e}"

agent = create_agent(
    "gpt-4o",
    tools=[calculate],
    system_prompt="You are a calculator assistant.",
)
```

1. `langgraph dev`でサーバーを起動
2. Studioでエージェントを開く
3. 「2 + 2」と入力して実行
4. 実行トレースを確認
5. `calculate`ツールが呼び出されたことを確認
6. 結果が正しいことを確認

### 例2: 複雑なグラフのデバッグ

```python
# src/agent.py
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict

class MyState(TypedDict):
    messages: list
    step: str

def node1(state: MyState) -> dict:
    return {"step": "node1_completed"}

def node2(state: MyState) -> dict:
    return {"step": "node2_completed"}

def should_continue(state: MyState) -> str:
    if state.get("step") == "node1_completed":
        return "node2"
    return "end"

graph = StateGraph(MyState)
graph.add_node("node1", node1)
graph.add_node("node2", node2)
graph.add_edge(START, "node1")
graph.add_conditional_edges("node1", should_continue)
graph.add_edge("node2", END)

agent = graph.compile()
```

1. Studioでグラフ構造を確認
2. 条件付きエッジの動作を確認
3. 各ノードでの状態変化を確認
4. 問題があれば修正して再実行

## トラブルシューティング

### サーバーが起動しない

- **ポートの確認**: ポート2024が使用中でないか確認
- **依存関係の確認**: すべての依存関係がインストールされているか確認
- **設定ファイルの確認**: `langgraph.json`が正しく設定されているか確認

### Studioに接続できない

- **APIキーの確認**: `.env`ファイルの`LANGSMITH_API_KEY`が正しいか確認
- **ネットワークの確認**: インターネット接続を確認
- **トンネルオプション**: Safariを使用している場合は`--tunnel`オプションを使用

### ホットリロードが動作しない

- **ファイルの保存**: ファイルが正しく保存されているか確認
- **サーバーの再起動**: 必要に応じてサーバーを再起動
- **キャッシュのクリア**: ブラウザのキャッシュをクリア

### グラフが表示されない

- **グラフのエクスポート**: グラフが正しくエクスポートされているか確認
- **設定ファイルの確認**: `langgraph.json`の`graphs`キーが正しいか確認
- **エラーログの確認**: サーバーのログを確認

## ベストプラクティス

### 1. 開発ワークフローの確立

1. **コードを書く**: エージェントのコードを実装
2. **Studioで確認**: Studioで動作を確認
3. **デバッグ**: 問題があれば修正
4. **反復**: プロンプトやロジックを調整
5. **テスト**: 複数の入力でテスト

### 2. プロンプトの最適化

1. Studioでプロンプトを変更
2. 即座に結果を確認
3. 複数のバージョンを比較
4. 最適なプロンプトを選択

### 3. 状態の理解

1. 各ノードでの状態を確認
2. 状態の遷移を追跡
3. 予期しない状態変化を特定
4. 必要に応じて修正

### 4. エラーハンドリング

1. エラーが発生した場合、Studioで詳細を確認
2. エラー発生時の状態を確認
3. エラーハンドリングロジックを追加
4. 再テスト

## まとめ

LangGraph Studioを使用することで：

- ✅ **視覚的な開発**: グラフ構造を視覚的に理解・編集
- ✅ **リアルタイムデバッグ**: 実行フローをリアルタイムで監視
- ✅ **迅速な反復**: プロンプトやロジックを即座にテスト
- ✅ **状態の理解**: 各ノードでの状態変化を詳細に確認
- ✅ **エラーの特定**: 問題を迅速に特定・修正

LangGraph Studioは、エージェント開発を大幅に効率化する強力なツールです。

## 参考資料

- [公式ドキュメント: LangSmith Studio](https://docs.langchain.com/oss/python/langgraph/studio)
- [LangSmith Studio ガイド](https://docs.langchain.com/langsmith/use-studio)
- [LangGraph CLI リファレンス](https://docs.langchain.com/langsmith/cli)
- [Application Structure](./P23_application_structure.md)
