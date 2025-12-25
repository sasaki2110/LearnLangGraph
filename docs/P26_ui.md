# UI

このドキュメントでは、LangGraphアプリケーションのユーザーインターフェース（UI）構築について解説します。Agent Chat UIを使用したチャットUIの実装と、リアルタイム更新の実装方法を説明します。

公式ドキュメント: https://docs.langchain.com/oss/python/langgraph/ui

## 概要

Agent Chat UIは、LangGraphエージェントと対話するための会話型インターフェースを提供するNext.jsアプリケーションです。以下の機能をサポートします：

- **リアルタイムチャット**: エージェントとのリアルタイムな会話
- **ツールの可視化**: ツール呼び出しと結果の視覚的な表示
- **タイムトラベルデバッグ**: 過去の状態に戻ってデバッグ
- **状態のフォーク**: 状態を分岐して異なるパスをテスト
- **中断スレッドの表示**: 中断されたスレッドの自動取得と表示

### 主な利点

- **最小限のセットアップ**: 既存のエージェントに簡単に接続
- **オープンソース**: カスタマイズ可能
- **ローカル/デプロイ対応**: ローカル開発とデプロイ環境の両方で動作
- **自動検出**: ツール呼び出しと中断を自動的に検出・表示

## クイックスタート

### ホスト版を使用（最も簡単）

最も簡単な方法は、ホスト版のAgent Chat UIを使用することです。

1. **[Agent Chat UI](https://agentchat.vercel.app)**にアクセス
2. **エージェントに接続**: デプロイURLまたはローカルサーバーアドレスを入力
3. **チャット開始**: UIが自動的にツール呼び出しと中断を検出・表示

### ローカル開発

カスタマイズやローカル開発が必要な場合は、Agent Chat UIをローカルで実行できます。

#### 方法1: npxを使用（推奨）

```bash
# 新しいAgent Chat UIプロジェクトを作成
npx create-agent-chat-app --project-name my-chat-ui

# プロジェクトディレクトリに移動
cd my-chat-ui

# 依存関係をインストールして起動
# pnpmを使用する場合:
pnpm install
pnpm dev

# または、npmを使用する場合:
npm install
npm run dev
```

#### 方法2: リポジトリをクローン

```bash
# リポジトリをクローン
git clone https://github.com/langchain-ai/agent-chat-ui.git
cd agent-chat-ui

# 依存関係をインストール
# pnpmを使用する場合:
pnpm install

# または、npmを使用する場合:
npm install

# 開発サーバーを起動
# pnpmを使用する場合:
pnpm dev

# または、npmを使用する場合:
npm run dev
```

アプリケーションは`http://localhost:3000`でアクセスできます。

## エージェントへの接続

Agent Chat UIは、ローカルエージェントとデプロイ済みエージェントの両方に接続できます。

### ローカルエージェントサーバーの起動

ローカルエージェントに接続するには、まずローカルでエージェントサーバーを起動する必要があります。

プロジェクトのルートディレクトリで以下のコマンドを実行します：

```bash
langgraph dev
```

このコマンドを実行すると、ポート2024でAPIエンドポイントが起動します：

- **APIエンドポイント**: `http://localhost:2024`（または`http://127.0.0.1:2024`）

**注意**: 
- サーバーが起動している間は、このターミナルを開いたままにしておく必要があります
- ポート2024が既に使用されている場合は、エラーが発生します
- 詳細は[LangGraph Studio](./P25_studio.md)のドキュメントを参照してください

### 接続設定

Agent Chat UIを起動すると、以下の情報を入力する必要があります：

1. **Graph ID**: グラフ名（`langgraph.json`ファイルの`graphs`キーで定義されている名前を指定）
   - `langgraph.json`の`graphs`キーを確認し、そこに定義されているグラフ名を使用します
   - 例: `langgraph.json`に`"graphs": { "calculator_agent": "./my_agent/agent.py:graph" }`とある場合、`graphId`は`"calculator_agent"`を指定します
2. **Deployment URL**: エージェントサーバーのエンドポイント
   - ローカル開発: `http://localhost:2024`
   - デプロイ環境: デプロイ済みエージェントのURL
3. **LangSmith API key（オプション）**: LangSmith APIキー（ローカルエージェントサーバーを使用する場合は不要）

### 設定例

#### ローカルエージェントに接続

**一般的な例**:
```json
{
  "graphId": "agent",
  "deploymentUrl": "http://localhost:2024",
  "langsmithApiKey": ""  // ローカルの場合は空でOK
}
```

**具体的な例（archives/p23の場合）**:
`archives/p23/langgraph.json`に以下のように定義されている場合：
```json
{
  "graphs": {
    "calculator_agent": "./my_agent/agent.py:graph"
  }
}
```

この場合、`graphId`には`"calculator_agent"`を指定します：
```json
{
  "graphId": "calculator_agent",
  "deploymentUrl": "http://localhost:2024",
  "langsmithApiKey": ""
}
```

**重要**: `graphId`は、プロジェクトの`langgraph.json`ファイルの`graphs`キーで定義されている名前と完全に一致させる必要があります。

#### デプロイ済みエージェントに接続

```json
{
  "graphId": "agent",
  "deploymentUrl": "https://your-deployed-agent.com",
  "langsmithApiKey": "lsv2_..."
}
```

### 中断スレッドの自動取得

設定が完了すると、Agent Chat UIは自動的に中断されたスレッドを取得して表示します。これにより、中断された会話を続けることができます。

## リアルタイム更新の実装

### ストリーミングの基本

Agent Chat UIは、LangGraphのストリーミング機能を活用してリアルタイム更新を実現します。

#### エージェント側の実装

エージェントでストリーミングを有効にするには、`stream`メソッドを使用します。

```python
# src/agent.py
from langchain.agents import create_agent
from langchain_core.tools import tool

@tool
def calculate(expression: str) -> str:
    """数式を計算するツール"""
    try:
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Error: {e}"

agent = create_agent(
    "gpt-4o",
    tools=[calculate],
    system_prompt="You are a calculator assistant.",
)
```

#### ストリーミングモード

LangGraphでは、以下のストリーミングモードが利用できます：

- **`values`**: 完全な状態をストリーム
- **`updates`**: 状態の差分をストリーム
- **`messages`**: LLMトークンとメタデータをストリーム
- **`custom`**: カスタムデータをストリーム
- **`debug`**: 詳細なトレースをストリーム

```python
# ストリーミングの例
for chunk in agent.stream(
    {"messages": [HumanMessage(content="2 + 2")]},
    stream_mode="messages"
):
    print(chunk)
```

### UI側でのストリーミング処理

Agent Chat UIは、自動的にストリーミングを処理します。カスタマイズする場合は、以下のように実装できます。

#### Next.jsでの実装例

```typescript
// app/api/chat/route.ts
import { NextRequest } from 'next/server';

export async function POST(req: NextRequest) {
  const { messages } = await req.json();
  
  // LangGraphエージェントに接続
  const response = await fetch('http://localhost:2024/threads/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      graph_id: 'agent',
      input: { messages },
    }),
  });

  // ストリーミングレスポンスを返す
  return new Response(response.body, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
    },
  });
}
```

#### フロントエンドでの処理

```typescript
// components/Chat.tsx
'use client';

import { useState } from 'react';

export function Chat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // 新しいメッセージを追加
    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');

    // ストリーミングリクエスト
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ messages: [...messages, userMessage] }),
    });

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();
    let assistantMessage = { role: 'assistant', content: '' };

    if (reader) {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = JSON.parse(line.slice(6));
            // ストリーミングデータを処理
            if (data.type === 'message') {
              assistantMessage.content += data.content;
              setMessages(prev => [...prev.slice(0, -1), assistantMessage]);
            }
          }
        }
      }
    }
  };

  return (
    <div>
      {/* メッセージ表示 */}
      {messages.map((msg, i) => (
        <div key={i}>{msg.content}</div>
      ))}
      
      {/* 入力フォーム */}
      <form onSubmit={handleSubmit}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="メッセージを入力..."
        />
        <button type="submit">送信</button>
      </form>
    </div>
  );
}
```

## ツールの可視化

Agent Chat UIは、ツール呼び出しと結果を自動的に検出して表示します。

### ツール呼び出しの表示

ツールが呼び出されると、UIに以下の情報が表示されます：

- **ツール名**: 呼び出されたツールの名前
- **引数**: ツールに渡された引数
- **結果**: ツールの戻り値
- **実行時間**: ツールの実行にかかった時間

### カスタマイズ

ツールの表示をカスタマイズするには、Agent Chat UIのコンポーネントを編集します。

```typescript
// components/ToolCall.tsx
export function ToolCall({ toolCall }) {
  return (
    <div className="tool-call">
      <div className="tool-name">{toolCall.name}</div>
      <div className="tool-args">
        {JSON.stringify(toolCall.args, null, 2)}
      </div>
      <div className="tool-result">
        {toolCall.result}
      </div>
    </div>
  );
}
```

## 中断（Interrupts）の処理

Agent Chat UIは、中断されたスレッドを自動的に検出して表示します。

### 中断の表示

エージェントが中断されると、UIに以下が表示されます：

- **中断メッセージ**: 中断の理由
- **現在の状態**: 中断時点の状態
- **続行ボタン**: 会話を続けるためのボタン

### 中断からの続行

```typescript
// 中断されたスレッドを続行
const continueThread = async (threadId: string) => {
  const response = await fetch(
    `http://localhost:2024/threads/${threadId}/continue`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        graph_id: 'agent',
        input: { action: 'continue' },
      }),
    }
  );
  
  return response.json();
};
```

## タイムトラベルデバッグ

Agent Chat UIは、タイムトラベルデバッグ機能をサポートしています。

### 状態の履歴表示

会話の各ステップでの状態を確認できます：

1. 会話履歴からステップを選択
2. その時点の状態を表示
3. 状態を編集して再実行

### 状態のフォーク

状態を分岐して、異なるパスをテストできます：

1. 特定のステップで状態をフォーク
2. 異なる入力で再実行
3. 結果を比較

## カスタマイズ

### メッセージの非表示

特定のメッセージタイプを非表示にできます。

```typescript
// 設定でメッセージを非表示
const config = {
  hideMessages: ['tool_call', 'tool_result'],
};
```

詳細は[Agent Chat UIのGitHubリポジトリ](https://github.com/langchain-ai/agent-chat-ui)を参照してください。

### テーマのカスタマイズ

Agent Chat UIのテーマをカスタマイズできます。

```typescript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        primary: '#your-color',
      },
    },
  },
};
```

### コンポーネントのカスタマイズ

Agent Chat UIのコンポーネントをカスタマイズして、独自のUIを実装できます。

```typescript
// components/CustomChat.tsx
import { Chat } from '@langchain/agent-chat-ui';

export function CustomChat() {
  return (
    <Chat
      customComponents={{
        Message: CustomMessage,
        ToolCall: CustomToolCall,
      }}
    />
  );
}
```

## ジェネレーティブUI

Agent Chat UIは、ジェネレーティブUIをサポートしています。これにより、エージェントが動的にUIコンポーネントを生成できます。

詳細は[Implement generative user interfaces with LangGraph](https://docs.langchain.com/langsmith/generative-ui-react)を参照してください。

## ベストプラクティス

### 1. エラーハンドリング

ストリーミング中にエラーが発生した場合の処理を実装します。

```typescript
try {
  const response = await fetch('/api/chat', { ... });
  // ストリーミング処理
} catch (error) {
  console.error('Error:', error);
  // エラーメッセージを表示
}
```

### 2. ローディング状態

ストリーミング中はローディング状態を表示します。

```typescript
const [isLoading, setIsLoading] = useState(false);

const handleSubmit = async () => {
  setIsLoading(true);
  try {
    // ストリーミング処理
  } finally {
    setIsLoading(false);
  }
};
```

### 3. メッセージの永続化

会話履歴を永続化して、ページをリロードしても保持します。

```typescript
// ローカルストレージに保存
useEffect(() => {
  localStorage.setItem('messages', JSON.stringify(messages));
}, [messages]);

// 読み込み
useEffect(() => {
  const saved = localStorage.getItem('messages');
  if (saved) {
    setMessages(JSON.parse(saved));
  }
}, []);
```

### 4. パフォーマンス最適化

大量のメッセージがある場合のパフォーマンスを最適化します。

```typescript
// 仮想スクロールを使用
import { useVirtualizer } from '@tanstack/react-virtual';

const virtualizer = useVirtualizer({
  count: messages.length,
  getScrollElement: () => parentRef.current,
  estimateSize: () => 100,
});
```

## トラブルシューティング

### エージェントに接続できない

- **URLの確認**: Deployment URLが正しいか確認
- **Graph IDの確認**: `langgraph.json`の`graphs`キーを確認
- **サーバーの起動**: エージェントサーバーが起動しているか確認

### ストリーミングが動作しない

- **ストリーミングモードの確認**: エージェントでストリーミングが有効か確認
- **CORSの設定**: クロスオリジンリクエストが許可されているか確認
- **ネットワークの確認**: ネットワーク接続を確認

### ツールが表示されない

- **ツールの定義**: エージェントにツールが正しく定義されているか確認
- **メッセージタイプの確認**: ツール呼び出しメッセージが正しい形式か確認

## まとめ

Agent Chat UIを使用することで：

- ✅ **簡単なセットアップ**: 最小限の設定でエージェントに接続
- ✅ **リアルタイム更新**: ストリーミングによるリアルタイムな会話
- ✅ **ツールの可視化**: ツール呼び出しと結果の自動表示
- ✅ **デバッグ機能**: タイムトラベルデバッグと状態のフォーク
- ✅ **カスタマイズ可能**: オープンソースで自由にカスタマイズ

Agent Chat UIは、LangGraphエージェントにユーザーフレンドリーなインターフェースを提供する強力なツールです。

## 参考資料

- [公式ドキュメント: Agent Chat UI](https://docs.langchain.com/oss/python/langgraph/ui)
- [Agent Chat UI GitHub](https://github.com/langchain-ai/agent-chat-ui)
- [Streaming](./P15_streaming.md)
- [Interrupts](./P18_interrupts.md)
- [Time Travel](./P22_timetravel.md)
