# LangGraph 学習ロードマップ

このドキュメントは、LangGraphを学習するための体系的なロードマップです。各トピックを順番に学習することで、LangGraphの概念から実践的な応用まで段階的に習得できます。

## 📚 ドキュメント一覧

### 基礎編

- **[P11: インストール手順](./P11_Install.md)**
  - LangGraphのインストール方法
  - 仮想環境の設定
  - 依存関係のインストール

- **[P12: クイックスタート](./P12_quickstart.md)**
  - LangGraphの基本概念
  - 計算エージェントの構築
  - グラフの構築とコンパイル
  - 状態管理と条件付きエッジ

### 中級編

- **[P13: Thinking in LangGraph](./P13_thinking_in_langgraph.md)**
  - LangGraphの設計思想
  - グラフベースの思考法
  - エージェント設計の基本原則

- **[P14: Workflows + Agents](./P14_workflows_agents.md)**
  - ワークフロー型とエージェント型の違い
  - それぞれの使い分け
  - 実装パターンとベストプラクティス

- **[P15: Streaming](./P15_streaming.md)**
  - ストリーミング出力の実装
  - リアルタイムでの結果表示
  - ユーザー体験の向上

- **[P16: Persistence](./P16_persistence.md)**
  - 状態の永続化
  - 会話履歴の保存と復元
  - データベースとの統合

### 上級編

- **[P17: Functional API](./P17_functional_api.md)**
  - 関数型APIの使用方法
  - Graph APIとの比較
  - 関数型スタイルでの実装

- **[P18: Interrupts](./P18_interrupts.md)**
  - 人間の介入（Human-in-the-loop）
  - 中断と再開のメカニズム
  - 承認フローの実装

- **[P19: Subgraphs](./P19_subgraphs.md)**
  - サブグラフの概念
  - 複雑なグラフの構造化
  - 再利用可能なコンポーネント

- **[P20: Memory](./P20_memory.md)**
  - 短期メモリと長期メモリ
  - メモリ管理のベストプラクティス
  - コンテキストの保持

- **[P21: Durable Execution](./P21_durable_execution.md)**
  - 長時間実行の管理
  - エラーからの復旧
  - チェックポイントと再開

## 🎯 推奨学習パス

### 初心者向けパス

```
P11 (インストール)
  ↓
P12 (クイックスタート)
  ↓
P13 (Thinking in LangGraph)
  ↓
P14 (Workflows + Agents)
  ↓
P15 (Streaming)
  ↓
P16 (Persistence)
```

### 実践者向けパス

```
P11-P16 (基礎・中級編を完了)
  ↓
P17 (Functional API)
  ↓
P18 (Interrupts)
  ↓
P19 (Subgraphs)
  ↓
P20 (Memory)
  ↓
P21 (Durable Execution)
```

## 📖 各トピックの概要

### 基礎編

#### P11: インストール手順
LangGraphを使い始めるための最初のステップ。環境構築から依存関係のインストールまで。

#### P12: クイックスタート
LangGraphの核心概念を学ぶ。グラフの構築、状態管理、条件付きエッジなど、エージェント開発の基礎。

### 中級編

#### P13: Thinking in LangGraph
LangGraphの設計思想を理解する。グラフベースの思考法と、エージェント設計の基本原則。

#### P14: Workflows + Agents
ワークフロー型とエージェント型の違いを理解し、適切な使い分けを学ぶ。

#### P15: Streaming
リアルタイムで結果を返すストリーミング機能の実装方法。

#### P16: Persistence
状態の永続化により、会話履歴や状態を保存・復元する方法。

### 上級編

#### P17: Functional API
Graph APIの代替として、関数型スタイルで実装する方法。

#### P18: Interrupts
人間の介入が必要な場面での中断と再開のメカニズム。

#### P19: Subgraphs
複雑なグラフを構造化し、再利用可能なコンポーネントとして管理する方法。

#### P20: Memory
短期・長期メモリの管理により、コンテキストを適切に保持する方法。

#### P21: Durable Execution
長時間実行されるエージェントの管理と、エラーからの復旧メカニズム。

## 🔗 参考資料

- [公式ドキュメント](https://docs.langchain.com/oss/python/langgraph/overview)
- [LangGraph GitHub](https://github.com/langchain-ai/langgraph)
- [LangChain ドキュメント](https://python.langchain.com/)

## 📝 学習の進め方

1. **順番に学習**: 各トピックは前のトピックの知識を前提としています
2. **実践しながら**: コードを実際に実行して理解を深めましょう
3. **公式ドキュメントと併用**: このドキュメントと公式ドキュメントを併用することで、より深い理解が得られます
4. **プロジェクトで実践**: 学んだ内容を実際のプロジェクトに適用してみましょう

## 🎓 学習目標

このロードマップを完了することで、以下のことができるようになります：

- ✅ LangGraphの基本概念を理解する
- ✅ エージェントとワークフローを設計・実装できる
- ✅ ストリーミング、永続化などの実用的な機能を実装できる
- ✅ 複雑なエージェントシステムを構築できる
- ✅ 本番環境で動作するエージェントをデプロイできる

