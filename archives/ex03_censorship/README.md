# ex03_censorship - 検閲エージェント

このプロジェクトは、キャッチコピーを生成し、NGワードをチェックして、
NGワードがあれば再生成するループ構造のLangGraphエージェントです。
Vercel AI SDKのチャットから呼び出せるストリーミング対応で、LangGraph Studio（`langgraph dev`）で使用できます。

## 構造

```
ex03_censorship/
├── my_agent/              # プロジェクトコード
│   ├── utils/             # グラフ用のユーティリティ
│   │   ├── __init__.py
│   │   ├── state.py       # グラフの状態定義
│   │   ├── nodes.py        # グラフ用のノード関数（ログ付き）
│   │   └── logging_config.py  # ロギング設定
│   ├── __init__.py
│   └── agent.py          # グラフを構築するコード（ログ付き）
├── tests/                # テストファイル
│   ├── __init__.py
│   └── test_invoke.py    # invokeのテスト
├── langgraph.json         # LangGraph設定ファイル
└── README.md             # このファイル
```

## 機能

このエージェントは、以下の処理を行います：

1. **キャッチコピー生成**: ユーザーの要望に合わせてキャッチコピーを1つ生成します
2. **NGワードチェック**: 生成されたコピーにNGワード（最高、日本一、絶対）が含まれていないかチェックします
3. **ループ処理**: NGワードが含まれていれば、Generatorに戻って作り直します（改善ポイントをフィードバック）

## グラフ構造

```
start
  ↓
Generator（キャッチコピー生成）
  ↓
Checker（NGワードチェック）
  ↓ (条件エッジ)
  ├─ has_ngword=true → Generator（再生成）
  └─ has_ngword=false → end
```

### 状態

- `messages`: `Annotated[list[AnyMessage], operator.add]` - メッセージ履歴
- `new_product_catchphrase_idea`: `Optional[str]` - ユーザーが最初に提示したキャッチフレーズ案
- `catchphrase`: `Optional[str]` - 生成されたキャッチフレーズ
- `has_ngword`: `Optional[bool]` - NGワードが含まれるか？
- `improvement_points`: `Optional[str]` - 改善ポイント

### ノード

1. **generator**: キャッチコピーを生成するLLMノード
   - `new_product_catchphrase_idea`が未設定なら、最後のメッセージを格納
   - 改善ポイントが設定されていれば、それを改善するように生成

2. **checker**: NGワードをチェックするPythonノード
   - 生成されたキャッチフレーズに、NGワード（最高、日本一、絶対）が含まれるか確認
   - 含まれていなければ: `has_ngword=false`, `improvement_points`をクリア
   - 含まれていれば: `has_ngword=true`, `improvement_points`に「〇〇をキャッチコピーに含めてはいけません。」を設定（複数の場合はカンマ区切り）

### エッジ

- `start` → `generator`
- `generator` → `checker`
- `checker` → 条件エッジ（`route_by_ngword`関数）
  - `has_ngword=true` → `generator`（再生成）
  - `has_ngword=false` → `end`

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
cd /root/LearnLangGraph/archives/ex03_censorship
langgraph dev
```

サーバーが起動すると、以下のURLでアクセスできます：
- **APIエンドポイント**: `http://127.0.0.1:2024`

## テスト

### invokeのテスト

```bash
cd /root/LearnLangGraph/archives/ex03_censorship
python tests/test_invoke.py
```

または、pytestを使用：

```bash
pytest tests/test_invoke.py -v
```

## ロギング

このプロジェクトは、p31_streamingのロギング実装を参考にした日本語ログを出力します。

### ログファイル

- `ex03_censorship.log`: すべてのログ
- `ex03_censorship_error.log`: エラーログのみ

### ログレベル

環境変数 `LOG_LEVEL` で設定可能（デフォルト: `INFO`）

### ログの確認方法

1. **コンソール出力**: 実行時にコンソールにログが表示されます
2. **ログファイル**: `ex03_censorship.log` ファイルを確認
3. **エラーログ**: `ex03_censorship_error.log` ファイルでエラーのみを確認

## 使用例

```python
from langchain.messages import HumanMessage
from my_agent.agent import graph

result = graph.invoke({
    "messages": [HumanMessage(content="新しいスマートフォンのキャッチコピー案")],
    "new_product_catchphrase_idea": None,
    "catchphrase": None,
    "has_ngword": None,
    "improvement_points": None
})

print(result["catchphrase"])  # 生成されたキャッチコピー
print(result["has_ngword"])  # NGワードが含まれているか
```

## NGワード

デフォルトのNGワードリスト：
- 最高
- 日本一
- 絶対

これらのワードが含まれているキャッチコピーは、自動的に再生成されます。

## 構成の参考

このプロジェクトは、以下の構成に従って実装されています：
- **構造**: p31_streamingの構造に従った実装
- **ストリーミング対応**: Vercel AI SDKのチャットから呼び出し可能
- **Studio対応**: `langgraph dev`で使用可能
- **ロギング機能**: p30_loggingを参考にした日本語ログを追加
- **テスト**: invokeの動作を確認するテストを含む
- **ループ構造**: 条件エッジを使用したループ処理を実装

