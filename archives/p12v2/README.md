# p12v2 - LangGraph クイックスタート（構造化版）

このプロジェクトは、P23_application_structure.mdに従った構造で、計算エージェントを実装したものです。
LangGraph Studio（`langgraph dev`）で使用できます。

## 構造

```
p12v2/
├── my_agent/              # プロジェクトコード
│   ├── utils/             # グラフ用のユーティリティ
│   │   ├── __init__.py
│   │   ├── state.py       # グラフの状態定義
│   │   ├── nodes.py       # グラフ用のノード関数
│   │   └── tools.py      # グラフ用のツール
│   ├── __init__.py
│   └── agent.py          # グラフを構築するコード
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
langgraph dev
```

サーバーが起動すると、以下のURLでアクセスできます：
- **APIエンドポイント**: `http://127.0.0.1:2024`
- **Studio UI**: `https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024`

## 機能

このエージェントは、以下の計算ツールを使用できます：

- **add**: 2つの数値を加算
- **multiply**: 2つの数値を乗算
- **divide**: 2つの数値を除算

## 元のコードとの違い

- **構造化**: P23_application_structure.mdに従った構造
- **モジュール化**: 状態、ノード、ツールを別ファイルに分離
- **Studio対応**: `langgraph dev`で使用可能
