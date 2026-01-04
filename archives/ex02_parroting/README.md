# ex02_parroting - オウム返し＋文字数カウントエージェント

このプロジェクトは、文字数をカウントしてStateに保存（加算）するノードと、
入力メッセージの最後に「これまでの合計文字数は 〇〇 文字です」を付与して返すノードを
直列につなぐLangGraphエージェントです。
Vercel AI SDKのチャットから呼び出せるストリーミング対応で、LangGraph Studio（`langgraph dev`）で使用できます。

## 構造

```
ex02_parroting/
├── my_agent/              # プロジェクトコード
│   ├── utils/             # グラフ用のユーティリティ
│   │   ├── __init__.py
│   │   ├── state.py       # グラフの状態定義
│   │   ├── nodes.py       # グラフ用のノード関数（ログ付き）
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

1. **文字数カウント**: ユーザーメッセージの文字数をカウントし、Stateの`char_count`に加算します
2. **オウム返し**: 入力メッセージをそのまま返し、最後に「これまでの合計文字数は 〇〇 文字です」を付与します

## グラフ構造

```
start
  ↓
文字数をカウントするノード
  ↓
オウム返しするLLMノード
  ↓
end
```

### 状態

- `messages`: `Annotated[list[AnyMessage], operator.add]` - メッセージのリスト
- `message`: `Optional[str]` - 最初のユーザーメッセージを保持
- `char_count`: `Annotated[int, operator.add]` - カウントした文字数をカウントアップしていく

### ノード

1. **count_characters**: 文字数をカウントするPythonノード
   - ユーザーメッセージの文字数をカウント
   - `char_count`を`operator.add`でカウントアップ
   - 最初のユーザーメッセージを`message`に保持

2. **parrot_with_count**: オウム返しするLLMノード
   - 入力されたユーザーメッセージに「これまでの合計文字数は 〇〇 文字です」を付与
   - メッセージをそのまま返し、文字数情報を追加

### エッジ

- `start` → `count_characters`
- `count_characters` → `parrot_with_count`
- `parrot_with_count` → `end`

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
cd /root/LearnLangGraph/archives/ex02_parroting
langgraph dev
```

サーバーが起動すると、以下のURLでアクセスできます：
- **APIエンドポイント**: `http://127.0.0.1:2024`

## テスト

### invokeのテスト

```bash
cd /root/LearnLangGraph/archives/ex02_parroting
python tests/test_invoke.py
```

または、pytestを使用：

```bash
pytest tests/test_invoke.py -v
```

## ロギング

このプロジェクトは、p31_streamingのロギング実装を参考にした日本語ログを出力します。

### ログファイル

- `ex02_parroting.log`: すべてのログ
- `ex02_parroting_error.log`: エラーログのみ

### ログレベル

環境変数 `LOG_LEVEL` で設定可能（デフォルト: `INFO`）

### ログの確認方法

1. **コンソール出力**: 実行時にコンソールにログが表示されます
2. **ログファイル**: `ex02_parroting.log` ファイルを確認
3. **エラーログ**: `ex02_parroting_error.log` ファイルでエラーのみを確認

## 使用例

```python
from langchain.messages import HumanMessage
from my_agent.agent import graph

result = graph.invoke({
    "messages": [HumanMessage(content="こんにちは、元気ですか？")],
    "message": None,
    "char_count": 0
})

print(result["message"])  # "こんにちは、元気ですか？"
print(result["char_count"])  # 文字数
print(result["messages"][-1].content)  # オウム返し＋文字数情報
```

## 構成の参考

このプロジェクトは、以下の構成に従って実装されています：
- **構造**: p31_streamingの構造に従った実装
- **ストリーミング対応**: Vercel AI SDKのチャットから呼び出し可能
- **Studio対応**: `langgraph dev`で使用可能
- **ロギング機能**: p30_loggingを参考にした日本語ログを追加
- **テスト**: invokeの動作を確認するテストを含む

