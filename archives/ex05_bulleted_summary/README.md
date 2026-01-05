# ex05_bulleted_summary - 箇条書きまとめ屋エージェント

このプロジェクトは、p31_streaming相当のロギングとストリーミングを実装した箇条書きまとめ屋エージェントです。
長い文章を、3つのノード（「重要点の抽出」「要約」「整形」）をリレーして短くします。
LangGraph Studio（`langgraph dev`）で使用できます。

## 構造

```
ex05_bulleted_summary/
├── my_agent/              # プロジェクトコード
│   ├── utils/             # グラフ用のユーティリティ
│   │   ├── __init__.py
│   │   ├── state.py       # グラフの状態定義
│   │   ├── nodes.py       # グラフ用のノード関数（ログ付き）
│   │   └── logging_config.py  # ロギング設定
│   ├── __init__.py
│   └── agent.py          # グラフを構築するコード（ログ付き）
├── tests/                # テストファイル
├── langgraph.json         # LangGraph設定ファイル
└── README.md             # このファイル
```

## 機能

このエージェントは、以下の3つのノードで処理を行います：

1. **ノードA (Extractor)**: 重要点抽出ノード
   - 最初に最終メッセージの内容を、状態のraw_textへ格納
   - 文章から「重要な事実・トピック」を5〜10個、箇条書きのリストとして抽出
   - その抽出結果を、状態のextracted_items (list)へ格納

2. **ノードB (Refiner)**: リスト精緻化ノード
   - 抽出されたリスト（extracted_items）を見て、重複を削り、重要度の高い順に並べ替える
   - その結果を、状態のrefined_items (list)へ格納

3. **ノードC (Writer)**: 最終回答作成ノード
   - 整理されたリストを元に、「忙しい人のための3行まとめ」と「詳細な箇条書き」の形式で最終回答を作る
   - その結果を、状態のfinal_reportへ格納

## グラフ構造

```
start
  ↓
ノードA (Extractor) - 重要点抽出
  ↓
ノードB (Refiner) - リスト精緻化
  ↓
ノードC (Writer) - 最終回答作成
  ↓
end
```

## 状態

- **messages**: メッセージ履歴
- **raw_text**: 元の文書
- **extracted_items**: 文書から抽出された重要なトピック・事実を箇条書きにしたもの（list）
- **refined_items**: 重複を削り、優先順位で並べ変えたもの（list）
- **final_report**: 最終的な回答

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
cd /root/LearnLangGraph/archives/ex05_bulleted_summary
langgraph dev
```

サーバーが起動すると、以下のURLでアクセスできます：
- **APIエンドポイント**: `http://127.0.0.1:2024`
- **LangGraph Studio**: `http://127.0.0.1:8123`

## 使用方法

### 基本的な使用例

```python
from langchain.messages import HumanMessage
from my_agent.agent import graph

# 長い文章を要約
long_text = """
人工知能（AI）は、コンピュータシステムが人間の知能を模倣する技術です。
機械学習は、AIの一分野で、データから学習してパターンを認識します。
深層学習は、ニューラルネットワークを使用した機械学習の一種です。
自然言語処理は、コンピュータが人間の言語を理解し、処理する技術です。
コンピュータビジョンは、画像や動画を分析して理解する技術です。
これらの技術は、医療、金融、自動車、エンターテインメントなど、様々な分野で活用されています。
"""

result = graph.invoke({
    "messages": [HumanMessage(content=long_text)]
})

print("最終回答:")
print(result["final_report"])
```

### ストリーミング使用例

```python
from langchain.messages import HumanMessage
from my_agent.agent import graph

# ストリーミングで実行
for chunk in graph.stream({
    "messages": [HumanMessage(content="長い文章...")]
}, stream_mode="updates"):
    print(chunk)
```

## ロギング機能

このエージェントは、p30_loggingとp31_streamingを参考にした日本語ログを出力します。

### ログレベル

環境変数 `LOG_LEVEL` で設定可能：
- `DEBUG`: 詳細なデバッグ情報
- `INFO`: 一般的な情報（デフォルト）
- `WARNING`: 警告メッセージ
- `ERROR`: エラーメッセージ

### ログの種類

- **📝 [EXTRACTOR]**: 重要点抽出ノードのログ
- **✨ [REFINER]**: リスト精緻化ノードのログ
- **📝 [WRITER]**: 最終回答作成ノードのログ
- **エラー**: エラー発生時の詳細情報

### ログの確認方法

1. **コンソール出力**: 実行時にコンソールにログが表示されます
2. **ログファイル**: `ex05_bulleted_summary.log` ファイルを確認
3. **エラーログ**: `ex05_bulleted_summary_error.log` ファイルでエラーのみを確認

## 特徴

- **構造化**: p30_loggingとp31_streamingの構造に従った実装
- **ストリーミング対応**: LangGraphの標準ストリーミング機能を使用
- **Studio対応**: `langgraph dev`で使用可能
- **ロギング機能**: 日本語ログを追加
- **3段階処理**: 抽出→精緻化→整形の3段階で要約を生成

## 出力形式

最終回答は以下の形式で出力されます：

```
【3行まとめ】
1. 最初の重要なポイント
2. 2番目の重要なポイント
3. 3番目の重要なポイント

【詳細な箇条書き】
- 詳細項目1
- 詳細項目2
...
```

## テスト

基本的な動作確認：

```python
from langchain.messages import HumanMessage
from my_agent.agent import graph

# テストケース
test_text = """
Pythonは、1991年にGuido van Rossumによって開発されたプログラミング言語です。
Pythonは、読みやすさとシンプルさを重視した設計で、初心者にも優しい言語です。
Pythonは、Web開発、データサイエンス、機械学習、自動化など、様々な用途で使用されています。
Pythonには、豊富なライブラリとフレームワークがあり、開発効率を高めます。
Pythonは、オープンソースで、大規模なコミュニティに支えられています。
"""

result = graph.invoke({
    "messages": [HumanMessage(content=test_text)]
})

print("=" * 60)
print("最終回答:")
print("=" * 60)
print(result["final_report"])
print("\n" + "=" * 60)
print("抽出された項目数:", len(result.get("extracted_items", [])))
print("精緻化された項目数:", len(result.get("refined_items", [])))
```

