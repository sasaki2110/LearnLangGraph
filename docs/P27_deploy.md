# Deploy

このドキュメントでは、LangGraphアプリケーションの本番環境へのデプロイ方法について解説します。LangSmith Cloudへのデプロイ、その他のクラウドプラットフォームへの展開、スケーリングとパフォーマンス最適化について説明します。

公式ドキュメント: https://docs.langchain.com/oss/python/langgraph/deploy

## 概要

LangGraphアプリケーションを本番環境にデプロイするには、状態を保持し、長時間実行されるエージェントの特性を考慮する必要があります。従来のステートレスなWebアプリケーション向けのホスティングプラットフォームとは異なり、LangGraphエージェントには専用のデプロイメント戦略が必要です。

### デプロイメントの考慮事項

- **状態の永続化**: エージェントの状態を永続化する必要がある
- **長時間実行**: バックグラウンドでの実行をサポート
- **スケーラビリティ**: 負荷に応じて自動的にスケール
- **可用性**: 高可用性の確保
- **セキュリティ**: APIキーや機密情報の適切な管理

## LangSmith Cloudへのデプロイ

LangSmith Cloudは、エージェントワークロード専用に設計された完全管理型のホスティングプラットフォームです。GitHubリポジトリから直接デプロイでき、LangSmithがインフラ、スケーリング、運用を管理します。

**⚠️ 重要**: LangSmith Cloudへのデプロイには、有料プラン（Plus Plan以上）への加入が必要です。無料プラン（Developer Plan）ではデプロイ機能は利用できません。

### 前提条件

- **GitHubアカウント**: コードをGitHubリポジトリにプッシュ
- **LangSmithアカウント**: [smith.langchain.com](https://smith.langchain.com)でアカウントを作成
- **有料プラン**: LangSmithの有料プラン（Plus Plan以上）への加入が必要

### デプロイ手順

#### ステップ1: GitHubリポジトリの作成

アプリケーションのコードをGitHubリポジトリにプッシュします。公開リポジトリとプライベートリポジトリの両方がサポートされています。

1. GitHubでリポジトリを作成
2. ローカルサーバーのセットアップガイドに従って、アプリをLangGraph互換にする
3. コードをリポジトリにプッシュ

#### ステップ2: LangSmithにデプロイ

1. **LangSmith Deploymentに移動**
   - [LangSmith](https://smith.langchain.com)にログイン
   - 左サイドバーで「Deployments」を選択

2. **新しいデプロイメントを作成**
   - 「+ New Deployment」ボタンをクリック
   - 必要な情報を入力

3. **リポジトリをリンク**
   - 初回使用時やプライベートリポジトリを追加する場合、「Add new account」ボタンをクリック
   - GitHubアカウントを接続する手順に従う

4. **リポジトリをデプロイ**
   - アプリケーションのリポジトリを選択
   - 「Submit」をクリックしてデプロイ
   - 完了まで約15分かかります
   - 「Deployment details」ビューでステータスを確認

#### ステップ3: Studioでアプリケーションをテスト

デプロイが完了したら：

1. 作成したデプロイメントを選択して詳細を表示
2. 右上の「Studio」ボタンをクリック
3. Studioが開き、グラフが表示されます

#### ステップ4: API URLを取得

1. LangGraphの「Deployment details」ビューで「API URL」をクリック
2. URLをクリップボードにコピー

#### ステップ5: APIをテスト

##### Python SDKを使用

```bash
pip install langgraph-sdk
```

```python
from langgraph_sdk import get_sync_client  # または get_client（非同期）

client = get_sync_client(
    url="your-deployment-url",
    api_key="your-langsmith-api-key"
)

for chunk in client.runs.stream(
    None,  # Threadless run
    "agent",  # langgraph.jsonで定義されたエージェント名
    input={
        "messages": [{
            "role": "human",
            "content": "What is LangGraph?",
        }],
    },
    stream_mode="updates",
):
    print(f"Receiving new event of type: {chunk.event}...")
    print(chunk.data)
    print("\n\n")
```

##### REST APIを使用

```bash
curl -X POST "https://your-deployment-url/threads/stream" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-langsmith-api-key" \
  -d '{
    "graph_id": "agent",
    "input": {
      "messages": [{
        "role": "human",
        "content": "What is LangGraph?"
      }]
    }
  }'
```

### LangSmith Deploymentの利点

- **完全管理**: インフラ、スケーリング、運用をLangSmithが管理
- **GitHub統合**: リポジトリから直接デプロイ
- **自動スケーリング**: 負荷に応じて自動的にスケール
- **高可用性**: 高可用性のインフラストラクチャ
- **セキュリティ**: セキュアな環境変数管理

### その他のデプロイオプション

LangSmithでは、Cloud以外にも以下のデプロイオプションを提供しています：

- **Control Plane（ハイブリッド/セルフホスト）**: 独自のインフラでコントロールプレーンを使用
- **Standalone Servers**: スタンドアロンサーバーとしてデプロイ

詳細は[Deployment overview](https://docs.langchain.com/langsmith/deployments)を参照してください。

## その他のクラウドプラットフォームへのデプロイ

### AWSへのデプロイ

#### ECS Fargate

ECS Fargateは、サーバーレスコンテナサービスで、サーバー管理なしでデプロイできます。

**特徴**:
- Dockerコンテナ化されたデプロイ
- CloudFormationによるインフラストラクチャ as Code
- 暗号化されたシークレット管理
- CPU/メモリ使用率に基づく自動スケーリング
- ヘルスチェック付きロードバランシング

**デプロイ例**:

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["langgraph", "dev"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  langgraph:
    build: .
    ports:
      - "2024:2024"
    environment:
      - LANGSMITH_API_KEY=${LANGSMITH_API_KEY}
```

#### AWS Lambda

サーバーレスアーキテクチャの場合、AWS Lambdaを使用できます。

**特徴**:
- 効率的なスケーリング動作
- 高スループットレベルでの低い推論時間
- 従量課金モデル

**制限事項**:
- 実行時間の制限（最大15分）
- 状態の永続化には外部ストレージが必要

### Azureへのデプロイ

#### Azure Kubernetes Service (AKS)

AKSは、マネージドKubernetesサービスです。

**特徴**:
- 自動スケーリング
- 他のAzureサービスとの統合
- 高可用性

#### Azure Functions

サーバーレスデプロイの場合、Azure Functionsを使用できます。

**特徴**:
- 迅速なスケーリング
- コスト効率（最大45%のコスト削減）
- 他のAzureサービスとの統合

### GCPへのデプロイ

#### Google Kubernetes Engine (GKE)

GKEは、マネージドKubernetesサービスです。

**特徴**:
- 自動スケーリング
- 他のGCPサービスとの統合
- 高可用性

#### Cloud Functions

サーバーレスデプロイの場合、GCP Cloud Functionsを使用できます。

**特徴**:
- 自動スケーリング
- 従量課金モデル
- 他のGCPサービスとの統合

**パフォーマンス**:
- A2インスタンス（A100 GPU）で最速の推論時間
- 最高のスループット

## スケーリングとパフォーマンス最適化

### スケーリング戦略

#### 水平スケーリング

複数のインスタンスを追加してスケールアウトします。

```python
# ロードバランサー設定例
# 複数のLangGraphインスタンスをロードバランサーの背後に配置
instances = [
    "http://langgraph-instance-1:2024",
    "http://langgraph-instance-2:2024",
    "http://langgraph-instance-3:2024",
]
```

#### 垂直スケーリング

既存のインスタンスのリソースを増やしてスケールアップします。

- CPU/メモリの増加
- GPUの追加（LLM推論の場合）

#### 自動スケーリング

負荷に応じて自動的にスケールします。

```yaml
# Kubernetes HPA（Horizontal Pod Autoscaler）の例
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: langgraph-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: langgraph
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### パフォーマンス最適化

#### 1. キャッシング

頻繁にアクセスされるデータをキャッシュします。

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def expensive_operation(input_data):
    # 高コストな操作
    return result
```

#### 2. 非同期処理

長時間実行されるタスクを非同期で処理します。

```python
import asyncio

async def process_async(state):
    # 非同期処理
    result = await long_running_task(state)
    return result
```

#### 3. バッチ処理

複数のリクエストをバッチで処理します。

```python
def process_batch(requests):
    # バッチ処理
    results = []
    for request in requests:
        result = process(request)
        results.append(result)
    return results
```

#### 4. データベース最適化

- インデックスの追加
- クエリの最適化
- 接続プーリング

```python
# 接続プーリングの例
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    "postgresql://user:pass@localhost/db",
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20
)
```

#### 5. メモリ管理

不要なデータを適切にクリーンアップします。

```python
import gc

def process_with_cleanup(state):
    result = process(state)
    # メモリクリーンアップ
    del state
    gc.collect()
    return result
```

### モニタリングとメトリクス

#### パフォーマンスメトリクス

以下のメトリクスを監視します：

- **レイテンシー**: リクエストからレスポンスまでの時間
- **スループット**: 単位時間あたりのリクエスト数
- **エラー率**: エラーが発生したリクエストの割合
- **リソース使用率**: CPU、メモリ、ネットワークの使用率

#### ログとトレーシング

```python
import logging
from langsmith import traceable

@traceable
def process_node(state):
    logger = logging.getLogger(__name__)
    logger.info(f"Processing state: {state}")
    # 処理を実行
    result = perform_processing(state)
    logger.info(f"Processing complete: {result}")
    return result
```

## セキュリティのベストプラクティス

### 1. 環境変数の管理

機密情報は環境変数で管理します。

```python
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
```

### 2. API認証

APIへのアクセスを認証で保護します。

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer

security = HTTPBearer()

def verify_token(token: str = Depends(security)):
    if token.credentials != os.getenv("API_TOKEN"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    return token
```

### 3. HTTPSの使用

本番環境では必ずHTTPSを使用します。

### 4. レート制限

APIのレート制限を実装します。

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/chat")
@limiter.limit("10/minute")
async def chat(request: Request):
    # チャット処理
    pass
```

## デプロイメントチェックリスト

デプロイ前に以下を確認します：

- [ ] アプリケーションがLangGraph互換である
- [ ] `langgraph.json`が正しく設定されている
- [ ] 環境変数が適切に設定されている
- [ ] 依存関係がすべてインストールされている
- [ ] テストがすべて通過している
- [ ] セキュリティ設定が適切である
- [ ] モニタリングとログが設定されている
- [ ] バックアップ戦略が確立されている
- [ ] 災害復旧計画が準備されている

## トラブルシューティング

### デプロイが失敗する

- **ログの確認**: デプロイメントログを確認
- **設定ファイルの確認**: `langgraph.json`が正しいか確認
- **依存関係の確認**: すべての依存関係がインストール可能か確認

### パフォーマンスの問題

- **リソースの確認**: CPU、メモリ、ネットワークの使用率を確認
- **ボトルネックの特定**: プロファイリングツールを使用
- **スケーリングの検討**: 必要に応じてスケールアップ/アウト

### 接続の問題

- **ネットワークの確認**: ファイアウォールやセキュリティグループの設定を確認
- **エンドポイントの確認**: URLが正しいか確認
- **認証の確認**: APIキーが正しいか確認

## まとめ

LangGraphアプリケーションのデプロイには：

- ✅ **LangSmith Cloud**: 最も簡単で推奨される方法
- ✅ **その他のクラウドプラットフォーム**: AWS、Azure、GCPなど
- ✅ **スケーリング**: 水平/垂直スケーリングと自動スケーリング
- ✅ **パフォーマンス最適化**: キャッシング、非同期処理、バッチ処理など
- ✅ **セキュリティ**: 環境変数管理、API認証、HTTPSなど

適切なデプロイメント戦略により、本番環境で安定して動作するLangGraphアプリケーションを構築できます。

## 参考資料

- [公式ドキュメント: LangSmith Deployment](https://docs.langchain.com/oss/python/langgraph/deploy)
- [LangSmith Deployment Overview](https://docs.langchain.com/langsmith/deployments)
- [Application Structure](./P23_application_structure.md)
- [Observability](./P28_observability.md)
