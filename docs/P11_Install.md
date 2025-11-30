# LangGraph インストール手順

このドキュメントでは、LangGraphの公式ドキュメント（[LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview)）に従って、LangGraphのインストール手順を説明します。

**この手順では、Pythonの仮想環境（venv）を使用することを前提としています。**

## 📋 前提条件

- **Python**: 3.8以上（LangChainを使用する場合は3.10以上が必要）
- 現在のPythonバージョン: 3.14.0 ✅
- **venv**: Python標準ライブラリに含まれているため、追加のインストールは不要

## 🔧 インストール手順

### ステップ 0: 仮想環境の作成と有効化

プロジェクトのルートディレクトリで仮想環境を作成し、有効化します。

```bash
# 仮想環境を作成（venvディレクトリが作成されます）
python3 -m venv venv

# 仮想環境を有効化
# Linux/macOSの場合:
source venv/bin/activate

# Windowsの場合:
# venv\Scripts\activate
```

仮想環境が有効化されると、プロンプトの先頭に `(venv)` が表示されます。

**注意**: 以降のすべてのコマンドは、仮想環境が有効化された状態で実行してください。

### ステップ 1: 依存関係のインストール

プロジェクトルートにある `requirements.txt` に記載された依存関係を一括インストールします。

```bash
pip install -r requirements.txt
```

**注意**: 
- `requirements.txt` には、LangGraphとLangChainが含まれています
- LangChainにはPython 3.10以上が必要です（現在の環境では問題ありません）

### ステップ 2: 新しいパッケージの追加方法

今後、新しいパッケージをインストールする場合は、以下の手順に従ってください：

1. **`requirements.txt` にパッケージ名を追記**
   
   `requirements.txt` を編集して、必要なパッケージを追加します。
   
   例：OpenAIを使用する場合
   ```txt
   # requirements.txt に以下を追記
   openai>=1.0.0
   ```

2. **インストールを実行**
   
   ```bash
   pip install -r requirements.txt
   ```
   
   または、特定のパッケージのみをインストールする場合：
   ```bash
   pip install openai
   ```
   
   その後、`requirements.txt` を更新：
   ```bash
   pip freeze > requirements.txt
   ```

### ステップ 3: プロバイダー固有のパッケージ（必要に応じて）

特定のLLMプロバイダー（OpenAI、Anthropicなど）を使用する場合は、`requirements.txt` に追記してください。

例：
- OpenAI: `requirements.txt` に `openai>=1.0.0` を追記
- Anthropic: `requirements.txt` に `anthropic>=0.1.0` を追記

詳細は[integrations](https://docs.langchain.com/oss/python/integrations/providers/overview)ページを参照してください。

**推奨**: 新しいパッケージを追加する際は、バージョン番号を明記することを推奨します（例: `openai>=1.0.0`）。これにより、環境の再現性が向上します。

## ✅ インストール確認

インストールが完了したら、プロジェクトルートにある `p11_install_check.py` を実行して動作確認を行います。

```bash
python p11_install_check.py
```

### 実行時の警告について

Python 3.14を使用している場合、以下のような警告が表示されることがあります：

```
UserWarning: Core Pydantic V1 functionality isn't compatible with Python 3.14 or greater.
```

**この警告は無視して問題ありません。** コードは正常に動作します。この警告は、LangChainが内部的にPydantic V1の後方互換性レイヤーを使用しているために表示されますが、実際の動作には影響しません。

警告を抑制したい場合は、`p11_install_check.py` のように `warnings` モジュールを使用してフィルタリングできます。

### 手動での動作確認

直接コードを実行して確認する場合：

```python
from langgraph.graph import StateGraph, MessagesState, START, END

def mock_llm(state: MessagesState):
    return {"messages": [{"role": "ai", "content": "hello world"}]}

graph = StateGraph(MessagesState)
graph.add_node(mock_llm)
graph.add_edge(START, "mock_llm")
graph.add_edge("mock_llm", END)
graph = graph.compile()

result = graph.invoke({"messages": [{"role": "user", "content": "hi!"}]})
print(result["messages"][-1].content)  # "hello world" が表示されます
```

## 📝 requirements.txt の管理

### requirements.txt の構造

`requirements.txt` には、プロジェクトで使用するすべてのパッケージとそのバージョンが記載されています。

```txt
# コメント行（# で始まる行は無視されます）
パッケージ名>=最小バージョン
パッケージ名==固定バージョン
```

### パッケージの追加方法

新しいパッケージを追加する際は、以下の2つの方法があります：

#### 方法1: 手動で requirements.txt に追記（推奨）

1. `requirements.txt` を編集して、必要なパッケージを追加
2. `pip install -r requirements.txt` でインストール

この方法では、バージョンを明示的に指定できるため、環境の再現性が高まります。

#### 方法2: pip install 後に freeze で更新

1. `pip install パッケージ名` でインストール
2. `pip freeze > requirements.txt` で更新

この方法は簡単ですが、すべての依存関係（間接的な依存関係も含む）が記録されるため、ファイルが大きくなる可能性があります。

### 環境の再現

他の環境や新しい仮想環境で同じ環境を再現する場合：

```bash
# 仮想環境を作成・有効化後
pip install -r requirements.txt
```

## 🔄 仮想環境の管理

### 仮想環境の無効化

作業が終わったら、以下のコマンドで仮想環境を無効化できます：

```bash
deactivate
```

### 仮想環境の再有効化

次回作業を再開する際は、再度仮想環境を有効化してください：

```bash
# Linux/macOSの場合:
source venv/bin/activate

# Windowsの場合:
# venv\Scripts\activate
```

### 仮想環境の削除

仮想環境を削除する場合は、`venv` ディレクトリを削除するだけです：

```bash
rm -rf venv  # Linux/macOSの場合
# または
# rmdir /s venv  # Windowsの場合
```

## 📚 次のステップ

インストールが完了したら、以下のリソースを参照して学習を進めます：

1. [Quickstart](https://docs.langchain.com/oss/python/langgraph/quickstart) - 基本的な使い方を学ぶ
2. [Thinking in LangGraph](https://docs.langchain.com/oss/python/langgraph/thinking-in-langgraph) - LangGraphの考え方を理解する
3. [Workflows + agents](https://docs.langchain.com/oss/python/langgraph/workflows-agents) - エージェントの構築方法を学ぶ

## 🔗 参考リンク

- [LangGraph公式ドキュメント](https://docs.langchain.com/oss/python/langgraph/overview)
- [インストールページ](https://docs.langchain.com/oss/python/langgraph/install)

