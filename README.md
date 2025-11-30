# LearnLangGraph

https://docs.langchain.com/oss/python/langgraph/overview

## ステップ 0: 仮想環境の作成と有効化

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

## ステップ 1: 依存関係のインストール

```bash
pip install -r requirements.txt
```

## ステップ 2: 環境変数の設定

OpenAI APIを使用するため、`.env`ファイルにAPIキーを設定します。

1. `.env.example`をコピーして`.env`ファイルを作成：
```bash
cp .env.example .env
```

2. `.env`ファイルを編集して、実際のAPIキーを設定：
```bash
# .envファイル
OPENAI_API_KEY="your-api-key-here"
OPENAI_MODEL="gpt-4o-mini"  # オプション: デフォルトは gpt-4o-mini
```

**注意**: 
- APIキーは[OpenAI Platform](https://platform.openai.com/api-keys)で取得できます
- `.env`ファイルは`.gitignore`に含まれているため、Gitにコミットされません（セキュリティ保護）
- デフォルトモデルは`gpt-4o-mini`です。別のモデルを使用する場合は、`.env`ファイルで`OPENAI_MODEL`を変更してください

## ステップ 3: クイックスタートの実行

公式ドキュメントのクイックスタートを参考に、計算エージェントのサンプルコードを実装しました。

```bash
python p12_quickstart.py
```

このスクリプトは以下の機能を実装しています：
- 加算、乗算、除算のツール定義
- LangGraphを使用したエージェントの構築
- 複数のテストケースでの実行
- OpenAI API（gpt-4o-mini）を使用

詳細は [公式クイックスタート](https://docs.langchain.com/oss/python/langgraph/quickstart) を参照してください。