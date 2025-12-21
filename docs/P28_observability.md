# Observability

このドキュメントでは、LangSmithを使った可観測性（Observability）について解説します。ログとトレーシング、モニタリングとアラート、パフォーマンス分析について説明します。

公式ドキュメント: https://docs.langchain.com/oss/python/langgraph/observability

## 概要

可観測性（Observability）は、アプリケーションの動作を理解し、問題を特定・解決するために重要です。LangSmithを使用することで、LangGraphアプリケーションの実行を可視化し、以下のことが可能になります：

- **デバッグ**: ローカルで実行中のアプリケーションをデバッグ
- **評価**: アプリケーションのパフォーマンスを評価
- **モニタリング**: アプリケーションを監視し、問題を早期に発見

### トレース（Traces）とは

トレースは、アプリケーションが入力から出力まで実行する一連のステップです。各ステップは**ラン（Run）**として表現されます。LangSmithを使用することで、これらの実行ステップを可視化できます。

## 前提条件

- **LangSmithアカウント**: [smith.langchain.com](https://smith.langchain.com)で無料アカウントを作成（またはログイン）
- **LangSmith APIキー**: [APIキー作成ガイド](https://docs.langchain.com/langsmith/create-account-api-key#create-an-api-key)に従ってAPIキーを作成

## トレーシングの有効化

### 基本的な設定

アプリケーションでトレーシングを有効にするには、以下の環境変数を設定します。

```bash
export LANGSMITH_TRACING=true
export LANGSMITH_API_KEY=<your-api-key>
```

または、`.env`ファイルに設定：

```env
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=lsv2_...
```

デフォルトでは、トレースは`default`という名前のプロジェクトにログされます。カスタムプロジェクト名を設定するには、後述の「プロジェクトへのログ」セクションを参照してください。

### Pythonコードでの設定

```python
import os
from dotenv import load_dotenv

load_dotenv()

# 環境変数が設定されていることを確認
assert os.getenv("LANGSMITH_TRACING") == "true"
assert os.getenv("LANGSMITH_API_KEY") is not None
```

詳細は[Trace with LangGraph](https://docs.langchain.com/langsmith/trace-with-langgraph)を参照してください。

## 選択的なトレーシング

特定の呼び出しやアプリケーションの一部のみをトレースしたい場合、LangSmithの`tracing_context`コンテキストマネージャーを使用できます。

### 基本的な使用例

```python
import langsmith as ls

# これはトレースされる
with ls.tracing_context(enabled=True):
    agent.invoke({
        "messages": [{
            "role": "user",
            "content": "Send a test email to alice@example.com"
        }]
    })

# これはトレースされない（LANGSMITH_TRACINGが設定されていない場合）
agent.invoke({
    "messages": [{
        "role": "user",
        "content": "Send another email"
    }]
})
```

### 条件付きトレーシング

特定の条件でのみトレースする場合：

```python
import langsmith as ls

def process_with_conditional_tracing(state, should_trace=False):
    if should_trace:
        with ls.tracing_context(enabled=True):
            return agent.invoke(state)
    else:
        return agent.invoke(state)
```

## プロジェクトへのログ

### 静的設定

環境変数でプロジェクト名を設定：

```bash
export LANGSMITH_PROJECT=my-project-name
```

または、`.env`ファイルに設定：

```env
LANGSMITH_PROJECT=my-project-name
```

### 動的設定

`tracing_context`を使用して動的にプロジェクト名を設定：

```python
import langsmith as ls

with ls.tracing_context(project_name="email-agent-test"):
    agent.invoke({
        "messages": [{
            "role": "user",
            "content": "Send a welcome email"
        }]
    })
```

### 複数プロジェクトの管理

異なる環境やバージョンでプロジェクトを分ける：

```python
import langsmith as ls
import os

environment = os.getenv("ENVIRONMENT", "development")
version = os.getenv("APP_VERSION", "1.0.0")

project_name = f"my-agent-{environment}-{version}"

with ls.tracing_context(project_name=project_name):
    agent.invoke(state)
```

## メタデータの追加

トレースにカスタムメタデータとタグを追加できます。これにより、トレースを検索、フィルタリング、分析しやすくなります。

### メタデータとタグの追加

```python
response = agent.invoke(
    {"messages": [{"role": "user", "content": "Send a welcome email"}]},
    config={
        "tags": ["production", "email-assistant", "v1.0"],
        "metadata": {
            "user_id": "user_123",
            "session_id": "session_456",
            "environment": "production"
        }
    }
)
```

### tracing_contextでのメタデータ

`tracing_context`でもメタデータとタグを指定できます：

```python
import langsmith as ls

with ls.tracing_context(
    project_name="email-agent-test",
    enabled=True,
    tags=["production", "email-assistant", "v1.0"],
    metadata={
        "user_id": "user_123",
        "session_id": "session_456",
        "environment": "production"
    }
):
    response = agent.invoke({
        "messages": [{"role": "user", "content": "Send a welcome email"}]
    })
```

### メタデータの活用

メタデータを使用して、トレースを検索・フィルタリング：

- **ユーザーID**: 特定のユーザーのトレースを検索
- **セッションID**: 特定のセッションのトレースを追跡
- **環境**: 本番環境と開発環境のトレースを分離
- **バージョン**: 異なるバージョンのパフォーマンスを比較

## 機密データの匿名化

機密データがLangSmithにログされないように、匿名化（Anonymization）を使用してマスクできます。

### 匿名化の設定

```python
from langchain_core.tracers.langchain import LangChainTracer
from langgraph.graph import StateGraph, MessagesState
from langsmith import Client
from langsmith.anonymizer import create_anonymizer

# 匿名化ルールを作成
anonymizer = create_anonymizer([
    # SSN（社会保障番号）に一致するパターンをマスク
    {"pattern": r"\b\d{3}-?\d{2}-?\d{4}\b", "replace": "<ssn>"},
    # メールアドレスをマスク
    {"pattern": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "replace": "<email>"},
    # クレジットカード番号をマスク
    {"pattern": r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b", "replace": "<credit-card>"},
])

# 匿名化機能付きのクライアントを作成
tracer_client = Client(anonymizer=anonymizer)
tracer = LangChainTracer(client=tracer_client)

# グラフを定義
graph = (
    StateGraph(MessagesState)
    .add_node("process", process_node)
    .add_edge(START, "process")
    .add_edge("process", END)
    .compile()
    .with_config({'callbacks': [tracer]})
)
```

### カスタム匿名化ルール

独自の匿名化ルールを作成：

```python
from langsmith.anonymizer import create_anonymizer

# カスタムパターンの匿名化
anonymizer = create_anonymizer([
    # 電話番号
    {"pattern": r"\b\d{3}-\d{3}-\d{4}\b", "replace": "<phone>"},
    # IPアドレス
    {"pattern": r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", "replace": "<ip>"},
    # カスタムパターン
    {"pattern": r"SECRET-\w+", "replace": "<secret>"},
])
```

詳細は[Rule-based masking of inputs and outputs](https://docs.langchain.com/langsmith/mask-inputs-outputs#rule-based-masking-of-inputs-and-outputs)を参照してください。

## ログとトレーシング

### ログレベルの設定

適切なログレベルを設定して、必要な情報を記録します。

```python
import logging

# ログレベルの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def process_node(state):
    logger.info(f"Processing state: {state}")
    try:
        result = perform_processing(state)
        logger.info(f"Processing complete: {result}")
        return result
    except Exception as e:
        logger.error(f"Error in process_node: {e}", exc_info=True)
        raise
```

### 構造化ログ

構造化ログを使用して、ログを検索・分析しやすくします。

```python
import json
import logging

class StructuredLogger:
    def __init__(self, name):
        self.logger = logging.getLogger(name)
    
    def log(self, level, message, **kwargs):
        log_data = {
            "message": message,
            **kwargs
        }
        getattr(self.logger, level)(json.dumps(log_data))

logger = StructuredLogger(__name__)

def process_node(state):
    logger.log("info", "Processing started", 
               user_id=state.get("user_id"),
               session_id=state.get("session_id"))
    # 処理を実行
    result = perform_processing(state)
    logger.log("info", "Processing complete",
               user_id=state.get("user_id"),
               session_id=state.get("session_id"),
               result_length=len(str(result)))
    return result
```

### トレースの確認

LangSmithでトレースを確認：

1. [LangSmith](https://smith.langchain.com)にログイン
2. プロジェクトを選択
3. トレースを表示
4. 各ラン（Run）の詳細を確認

## モニタリングとアラート

### ダッシュボード

LangSmithでは、プリビルドとカスタムのダッシュボードを提供しています。

#### プリビルドダッシュボード

各プロジェクトに対して自動的に生成され、以下のメトリクスを表示：

- **トレース数**: 実行されたトレースの数
- **エラー率**: エラーが発生したトレースの割合
- **トークン使用量**: 使用されたトークン数
- **レイテンシー**: 平均応答時間

#### カスタムダッシュボード

特定のメトリクスを監視するカスタムダッシュボードを作成：

1. LangSmithで「Dashboards」を選択
2. 「New Dashboard」をクリック
3. チャートを追加
4. トレーシングプロジェクトを選択
5. フィルタを適用
6. 可視化タイプを選択

### アラートの設定

LangSmithのアラートシステムを使用して、問題を事前に検出できます。

#### アラートの種類

- **エラー率**: エラーが発生したラン数の増加
- **フィードバックスコア**: フィードバックスコアの低下
- **レイテンシー**: 応答時間の増加
- **APIレート制限**: APIレート制限の違反

#### アラートの作成

1. プロジェクトを選択
2. 「Alerts」アイコンをクリック
3. 「New Alert」をクリック
4. アラート条件を設定：
   - **メトリクス**: エラー率、フィードバックスコア、レイテンシーなど
   - **条件**: 閾値、集計方法
   - **通知チャネル**: PagerDuty、Webhookなど

#### アラート設定の例

```python
# アラート設定の例（LangSmith UIで設定）
# エラー率が10%を超えた場合にアラート
{
    "metric": "errored_runs",
    "condition": ">",
    "threshold": 0.1,
    "aggregation": "rate",
    "notification": "webhook"
}
```

詳細は[LangSmith Alerts](https://docs.langchain.com/langsmith/alerts)を参照してください。

## パフォーマンス分析

### メトリクスの監視

以下のメトリクスを監視して、パフォーマンスを分析します：

#### 1. レイテンシー（Latency）

応答時間を監視：

```python
import time
from langsmith import traceable

@traceable
def process_node(state):
    start_time = time.time()
    result = perform_processing(state)
    end_time = time.time()
    
    # レイテンシーをメタデータに追加
    latency = end_time - start_time
    return {
        **result,
        "metadata": {
            "latency": latency,
            "latency_ms": latency * 1000
        }
    }
```

#### 2. スループット（Throughput）

単位時間あたりのリクエスト数を監視：

```python
from collections import deque
import time

class ThroughputMonitor:
    def __init__(self, window_size=60):
        self.requests = deque()
        self.window_size = window_size
    
    def record_request(self):
        self.requests.append(time.time())
        # 古いリクエストを削除
        while self.requests and self.requests[0] < time.time() - self.window_size:
            self.requests.popleft()
    
    def get_throughput(self):
        return len(self.requests) / self.window_size

monitor = ThroughputMonitor()

def process_node(state):
    monitor.record_request()
    throughput = monitor.get_throughput()
    # メタデータに追加
    return {
        **perform_processing(state),
        "metadata": {"throughput": throughput}
    }
```

#### 3. エラー率（Error Rate）

エラーが発生したリクエストの割合を監視：

```python
from collections import defaultdict

class ErrorRateMonitor:
    def __init__(self):
        self.errors = defaultdict(int)
        self.total = defaultdict(int)
    
    def record(self, operation, is_error=False):
        self.total[operation] += 1
        if is_error:
            self.errors[operation] += 1
    
    def get_error_rate(self, operation):
        if self.total[operation] == 0:
            return 0
        return self.errors[operation] / self.total[operation]

monitor = ErrorRateMonitor()

def process_node(state):
    try:
        result = perform_processing(state)
        monitor.record("process_node", is_error=False)
        return result
    except Exception as e:
        monitor.record("process_node", is_error=True)
        raise
```

#### 4. トークン使用量（Token Usage）

LLMのトークン使用量を監視：

```python
from langsmith import traceable

@traceable
def llm_node(state):
    response = llm.invoke(state["messages"])
    
    # トークン使用量をメタデータに追加
    token_usage = {
        "input_tokens": response.usage_metadata.prompt_tokens if hasattr(response, 'usage_metadata') else 0,
        "output_tokens": response.usage_metadata.completion_tokens if hasattr(response, 'usage_metadata') else 0,
        "total_tokens": response.usage_metadata.total_tokens if hasattr(response, 'usage_metadata') else 0,
    }
    
    return {
        "messages": state["messages"] + [response],
        "metadata": {"token_usage": token_usage}
    }
```

### パフォーマンスの最適化

パフォーマンス分析の結果に基づいて、最適化を行います。

#### 1. ボトルネックの特定

LangSmithのトレースを使用して、ボトルネックを特定：

1. トレースを確認
2. 各ノードの実行時間を比較
3. 最も時間がかかっているノードを特定
4. そのノードを最適化

#### 2. キャッシング

頻繁にアクセスされるデータをキャッシュ：

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def expensive_operation(input_data):
    # 高コストな操作
    return result
```

#### 3. 並列処理

可能な場合は並列処理を使用：

```python
import asyncio

async def process_multiple(state):
    tasks = [process_item(item) for item in state["items"]]
    results = await asyncio.gather(*tasks)
    return {"results": results}
```

## ベストプラクティス

### 1. 適切なログレベル

- **DEBUG**: 開発時の詳細情報
- **INFO**: 一般的な情報
- **WARNING**: 警告
- **ERROR**: エラー
- **CRITICAL**: 重大なエラー

### 2. 構造化ログ

構造化ログを使用して、ログを検索・分析しやすくします。

### 3. メタデータの活用

メタデータを使用して、トレースを検索・フィルタリングしやすくします。

### 4. 機密データの保護

機密データは匿名化して、LangSmithに送信しないようにします。

### 5. アラートの設定

重要なメトリクスに対してアラートを設定し、問題を早期に発見します。

### 6. 定期的なレビュー

定期的にダッシュボードとアラートをレビューし、パフォーマンスを改善します。

## トラブルシューティング

### トレースが表示されない

- **環境変数の確認**: `LANGSMITH_TRACING`と`LANGSMITH_API_KEY`が設定されているか確認
- **ネットワークの確認**: LangSmithへの接続を確認
- **プロジェクト名の確認**: 正しいプロジェクト名が設定されているか確認

### パフォーマンスの問題

- **トレースの確認**: LangSmithでトレースを確認し、ボトルネックを特定
- **メトリクスの監視**: レイテンシー、スループット、エラー率を監視
- **最適化**: ボトルネックを最適化

### アラートが動作しない

- **アラート設定の確認**: アラート条件が正しいか確認
- **通知チャネルの確認**: 通知チャネルが正しく設定されているか確認
- **閾値の確認**: 閾値が適切か確認

## まとめ

LangSmithを使った可観測性により：

- ✅ **デバッグ**: ローカルで実行中のアプリケーションをデバッグ
- ✅ **評価**: アプリケーションのパフォーマンスを評価
- ✅ **モニタリング**: アプリケーションを監視し、問題を早期に発見
- ✅ **最適化**: パフォーマンス分析に基づいて最適化
- ✅ **アラート**: 問題を事前に検出

適切な可観測性により、本番環境で安定して動作するLangGraphアプリケーションを構築・保守できます。

## 参考資料

- [公式ドキュメント: LangSmith Observability](https://docs.langchain.com/oss/python/langgraph/observability)
- [Trace with LangGraph](https://docs.langchain.com/langsmith/trace-with-langgraph)
- [LangSmith Alerts](https://docs.langchain.com/langsmith/alerts)
- [LangSmith Dashboards](https://docs.smith.langchain.com/observability/how_to_guides/monitoring/dashboards)
- [LangSmith Documentation](https://docs.langchain.com/langsmith/home)
