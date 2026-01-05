# ex06_web_research - 自律的なWebリサーチエージェント

このプロジェクトは、ユーザーから「最新のAIニュースについて調べてまとめて」といった依頼を受け、満足いくまで調査を続ける自律的なWebリサーチエージェントです。
ReAct（Reasoning and Acting）パターンを実装し、ツールを呼び出すかどうかを自律的に判断します。
p31_streaming相当のストリーミング、ロギング機能を実装しています。

## 構造

```
ex06_web_research/
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

1. **テーマ抽出**: ユーザーのメッセージからリサーチテーマを抽出します
2. **思考＋Action**: LLMが現在の状況を分析し、ツールを呼び出すかどうかを判断します
3. **ツール実行**: Web検索ツール（モック実装）を実行し、調査結果を収集します
4. **観察**: 調査結果が十分かどうかを判定します（OpenAI、Google、Anthropic、NVIDIA、Oracleがすべて言及されているか）
5. **最終回答整形**: 収集した調査結果を基に、包括的なレポートを作成します

## 状態（State）

- `messages`: メッセージ履歴
- `theme`: ユーザーが指定したリサーチ対象のテーマ
- `survey_results`: 調査結果を格納していく配列
- `is_sufficient`: 調査結果が十分かどうか
- `tool_count`: リサーチツールを呼んだ回数（モック実装で、何番目のメッセージを返すかを管理）
- `llm_call_count`: 無限ループ防止のカウンター

## ツール

### リサーチツール（search_web）

- **パラメータ**: `theme`（テーマ）、`call_count`（呼び出し回数）
- **モック実装**: 10個の検索結果を定義し、`call_count`番目の情報を返却
- **テストテーマ**: 「最近のAI動向」
- **返却値**: 各返却値にOpenAI、Google、Anthropic、NVIDIA、Oracleを含む

## ノード

1. **ユーザー指定テーマ抽出ノード**（python steps）
   - 最新メッセージの内容を`theme`に格納

2. **思考＋Actionノード**（llm steps）
   - `theme`が格納されていれば、WEB検索ツール利用を返却する
   - 呼ばれるたびに、`llm_call_count`をカウントアップ

3. **ツールノード**（python steps）
   - 指定されたツールを起動
   - 結果を`survey_results`へ追加
   - 状態の`tool_count`をカウントアップ

4. **観察ノード**（llm steps）
   - 調査結果が十分か判定する
   - 十分の判定は、OpenAI、Google、Anthropic、NVIDIA、Oracleが言及されること
   - 判定結果を`is_sufficient`へ格納

5. **最終回答整形ノード**（llm steps）
   - `survey_results`の結果を整形して返却する
   - `llm_call_count > 10`の場合は試行回数オーバーの旨もユーザーへのメッセージに追加

## エッジ

- `start` → ユーザー指定テーマ抽出ノード
- ユーザー指定テーマ抽出ノード → 思考＋Actionノード
- 思考＋Actionノード → 条件分岐
  - ツール呼び出しが必要なら → ツールノード
  - 不要なら → 観察ノード
- ツールノード → 観察ノード
- 観察ノード → 条件分岐
  - `is_sufficient=true` → 最終回答整形ノード
  - `is_sufficient=false` → 思考＋Actionノード
  - `llm_call_count>10` → 最終回答整形ノード
- 最終回答整形ノード → `end`

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
cd /root/LearnLangGraph/archives/ex06_web_research
langgraph dev
```

サーバーが起動すると、以下のURLでアクセスできます：
- **APIエンドポイント**: `http://127.0.0.1:2024`
- **Studio UI**: `https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024`

## Vercel AI SDKからの呼び出し

Vercel AI SDKのチャットから呼び出すには、以下の設定を使用します：

- **API URL**: `http://localhost:2024` (またはデプロイ先のURL)
- **Assistant ID**: `ex06_web_research`

## テスト

invokeが正常に動作することを確認するテストを実行できます：

```bash
cd /root/LearnLangGraph/archives/ex06_web_research
python -m pytest tests/test_invoke.py -v
```

または、直接実行：

```bash
python tests/test_invoke.py
```

テストのテーマは「最近のAI動向」として設定されています。

## ロギング機能

### ログファイル

- **通常ログ**: `ex06_web_research.log` (デフォルト)
- **エラーログ**: `ex06_web_research_error.log` (ERROR/CRITICALレベルのみ)

### 環境変数

以下の環境変数でロギングをカスタマイズできます：

- `LOG_LEVEL`: ログレベル (DEBUG, INFO, WARNING, ERROR) - デフォルト: INFO
- `LOG_FILE`: ログファイル名 - デフォルト: `ex06_web_research.log`
- `LOG_DIR`: ログファイルのディレクトリ - デフォルト: `.` (現在のディレクトリ)
- `LOG_USE_PYTHON_ROTATION`: Pythonローテーションを使用するか (true/false) - デフォルト: true
- `ENVIRONMENT`: 環境 (production, development, staging) - デフォルト: development

### ログの内容

自前実装部分（nodes.py, agent.py）に以下のような日本語ログが出力されます：

- **エージェント初期化**: モデルの初期化、グラフの構築
- **テーマ抽出**: メッセージからテーマを抽出する処理
- **思考＋Action**: LLM呼び出し開始/完了、ツール呼び出し判定
- **ツール実行**: ツール呼び出し、調査結果の追加
- **観察**: 調査結果の十分性判定
- **最終回答整形**: LLM呼び出し開始/完了、最終回答の生成
- **ルーティング**: 条件分岐の判定結果
- **エラー**: エラー発生時の詳細情報

### ログの確認方法

1. **コンソール出力**: 実行時にコンソールにログが表示されます
2. **ログファイル**: `ex06_web_research.log` ファイルを確認
3. **エラーログ**: `ex06_web_research_error.log` ファイルでエラーのみを確認

## 学習のポイント

### ReAct (Reasoning and Acting) パターン

- LLMが自分の思考プロセスを明示し、ツールを呼ぶかどうかを自律的に決める
- 情報が足りなければ、検索を繰り返し、情報をStateに蓄積していく

### 情報の蓄積

- 複数回のツール実行結果をStateに保持し、最終回答に活かす
- `survey_results`配列に調査結果を蓄積

### 状態管理

- `tool_count`: ツール呼び出し回数を管理（モック実装で検索結果のインデックスを決定）
- `llm_call_count`: 無限ループ防止のカウンター（10回を超えると強制終了）

### 条件分岐

- 思考＋Actionノードから: ツール呼び出しの有無で分岐
- 観察ノードから: 調査結果の十分性と試行回数で分岐

## ストリーミング対応

p31_streaming相当のストリーミング機能を実装しています。
Vercel AI SDKのチャットから呼び出して使用できます。

