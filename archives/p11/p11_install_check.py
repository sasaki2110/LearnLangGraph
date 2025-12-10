"""
LangGraph インストール確認スクリプト

このスクリプトは、LangGraphが正しくインストールされているかを確認します。
"""

import warnings

# Python 3.14とPydantic V1の互換性に関する警告を抑制
# 注意: これは警告であり、コードは正常に動作します
warnings.filterwarnings("ignore", message=".*Pydantic V1.*Python 3.14.*")

from langgraph.graph import StateGraph, MessagesState, START, END

def mock_llm(state: MessagesState):
    """モックLLM関数 - 簡単な応答を返す"""
    return {"messages": [{"role": "ai", "content": "hello world"}]}

def main():
    """メイン関数 - LangGraphの動作確認"""
    print("LangGraph インストール確認を開始します...")
    
    # グラフの構築
    graph = StateGraph(MessagesState)
    graph.add_node(mock_llm)
    graph.add_edge(START, "mock_llm")
    graph.add_edge("mock_llm", END)
    graph = graph.compile()
    
    # グラフの実行
    result = graph.invoke({"messages": [{"role": "user", "content": "hi!"}]})
    
    print("\n✅ LangGraphは正常に動作しています！")
    # メッセージの最後の要素を取得（AIMessageオブジェクト）
    last_message = result["messages"][-1]
    print(f"結果: {last_message.content}")

if __name__ == "__main__":
    main()
