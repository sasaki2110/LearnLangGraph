"""
LangGraph サブグラフの基本例（関数ノード内でサブグラフを呼び出す方法）
公式ドキュメント: https://docs.langchain.com/oss/python/langgraph/use-subgraphs

この例では、サブグラフを関数ノード内で呼び出す方法を示します。
この方法により、メッセージの重複問題を回避できます。
"""

from langchain.messages import AnyMessage, AIMessage, HumanMessage
from typing_extensions import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
import operator


# ============================================
# 状態の定義
# ============================================
class MessagesState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]


# ============================================
# ヘルパー関数
# ============================================
def clean(messages: list[AnyMessage]) -> str:
    """データのクリーニング（デモ用）"""
    if not messages:
        return "No messages to clean"
    
    # 最後のメッセージの内容を取得
    last_message = messages[-1]
    content = last_message.content if hasattr(last_message, 'content') else str(last_message)
    
    # 簡単なクリーニング処理（実際の実装ではより複雑な処理を行う）
    cleaned = content.strip().upper()
    return f"[CLEANED] {cleaned}"


def validate(messages: list[AnyMessage]) -> str:
    """データの検証（デモ用）"""
    if not messages:
        return "No messages to validate"
    
    # 最後のメッセージの内容を取得
    last_message = messages[-1]
    content = last_message.content if hasattr(last_message, 'content') else str(last_message)
    
    # 簡単な検証処理（実際の実装ではより複雑な処理を行う）
    validated = content.replace("[CLEANED] ", "[VALIDATED] ")
    return validated


def process(messages: list[AnyMessage]) -> str:
    """データの処理（デモ用）"""
    if not messages:
        return "No messages to process"
    
    # 最後のメッセージの内容を取得
    last_message = messages[-1]
    content = last_message.content if hasattr(last_message, 'content') else str(last_message)
    
    # 簡単な処理（実際の実装ではより複雑な処理を行う）
    processed = content.replace("[VALIDATED] ", "[PROCESSED] ")
    return processed


def postprocessing_function(state: MessagesState) -> dict:
    """後処理関数"""
    print("    [親グラフ: postprocessing] 実行中...")
    print(f"    [親グラフ: postprocessing] 現在のメッセージ数: {len(state['messages'])}")
    if not state["messages"]:
        return {"messages": [AIMessage(content="No messages to postprocess")]}
    
    # 最後のメッセージの内容を取得
    last_message = state["messages"][-1]
    content = last_message.content if hasattr(last_message, 'content') else str(last_message)
    
    # 後処理（実際の実装ではより複雑な処理を行う）
    postprocessed = content.replace("[PROCESSED] ", "[FINAL] ")
    result = {"messages": [AIMessage(content=postprocessed)]}
    print(f"    [親グラフ: postprocessing] 追加するメッセージ: {postprocessed}")
    return result


# ============================================
# サブグラフ1: データ前処理
# ============================================
def create_preprocessing_subgraph():
    """前処理サブグラフ"""
    subgraph = StateGraph(MessagesState)
    
    def clean_data(state: MessagesState) -> dict:
        """データのクリーニング"""
        print("    [サブグラフ1: clean_data] 実行中...")
        print(f"    [サブグラフ1: clean_data] 現在のメッセージ数: {len(state['messages'])}")
        cleaned = clean(state["messages"])
        result = {"messages": [AIMessage(content=cleaned)]}
        print(f"    [サブグラフ1: clean_data] 追加するメッセージ: {cleaned}")
        return result
    
    def validate_data(state: MessagesState) -> dict:
        """データの検証"""
        print("    [サブグラフ1: validate_data] 実行中...")
        print(f"    [サブグラフ1: validate_data] 現在のメッセージ数: {len(state['messages'])}")
        validated = validate(state["messages"])
        result = {"messages": [AIMessage(content=validated)]}
        print(f"    [サブグラフ1: validate_data] 追加するメッセージ: {validated}")
        return result
    
    subgraph.add_node("clean_data", clean_data)
    subgraph.add_node("validate_data", validate_data)
    subgraph.add_edge(START, "clean_data")
    subgraph.add_edge("clean_data", "validate_data")
    subgraph.add_edge("validate_data", END)
    
    return subgraph.compile()


# ============================================
# サブグラフ2: データ処理
# ============================================
def create_processing_subgraph():
    """処理サブグラフ"""
    subgraph = StateGraph(MessagesState)
    
    def process_data(state: MessagesState) -> dict:
        """データの処理"""
        print("    [サブグラフ2: process_data] 実行中...")
        print(f"    [サブグラフ2: process_data] 現在のメッセージ数: {len(state['messages'])}")
        processed = process(state["messages"])
        result = {"messages": [AIMessage(content=processed)]}
        print(f"    [サブグラフ2: process_data] 追加するメッセージ: {processed}")
        return result
    
    subgraph.add_node("process_data", process_data)
    subgraph.add_edge(START, "process_data")
    subgraph.add_edge("process_data", END)
    
    return subgraph.compile()


# ============================================
# 親グラフの構築（関数ノード内でサブグラフを呼び出す方法）
# ============================================
def create_main_graph():
    """メイングラフ（関数ノード内でサブグラフを呼び出す）"""
    # サブグラフを事前に作成
    preprocessing_subgraph = create_preprocessing_subgraph()
    processing_subgraph = create_processing_subgraph()
    
    main_graph = StateGraph(MessagesState)
    
    def preprocessing_node(state: MessagesState) -> dict:
        """前処理ノード（サブグラフ1を呼び出す）"""
        print("    [親グラフ: preprocessing_node] 実行中...")
        print(f"    [親グラフ: preprocessing_node] 現在のメッセージ数: {len(state['messages'])}")
        
        # サブグラフを呼び出す
        subgraph_result = preprocessing_subgraph.invoke(state)
        
        # サブグラフの実行結果から、新しく追加されたメッセージのみを取得
        # （重複を避けるため、サブグラフ実行前のメッセージ数より後のメッセージのみを返す）
        initial_count = len(state["messages"])
        new_messages = subgraph_result["messages"][initial_count:]
        
        print(f"    [親グラフ: preprocessing_node] サブグラフ実行後のメッセージ数: {len(subgraph_result['messages'])}")
        print(f"    [親グラフ: preprocessing_node] 新しく追加されたメッセージ数: {len(new_messages)}")
        
        # 新しく追加されたメッセージのみを返す（重複を避ける）
        return {"messages": new_messages}
    
    def processing_node(state: MessagesState) -> dict:
        """処理ノード（サブグラフ2を呼び出す）"""
        print("    [親グラフ: processing_node] 実行中...")
        print(f"    [親グラフ: processing_node] 現在のメッセージ数: {len(state['messages'])}")
        
        # サブグラフを呼び出す
        subgraph_result = processing_subgraph.invoke(state)
        
        # サブグラフの実行結果から、新しく追加されたメッセージのみを取得
        initial_count = len(state["messages"])
        new_messages = subgraph_result["messages"][initial_count:]
        
        print(f"    [親グラフ: processing_node] サブグラフ実行後のメッセージ数: {len(subgraph_result['messages'])}")
        print(f"    [親グラフ: processing_node] 新しく追加されたメッセージ数: {len(new_messages)}")
        
        # 新しく追加されたメッセージのみを返す（重複を避ける）
        return {"messages": new_messages}
    
    # 関数ノードを追加（サブグラフを直接追加するのではなく、関数ノードを追加）
    main_graph.add_node("preprocessing", preprocessing_node)
    main_graph.add_node("processing", processing_node)
    main_graph.add_node("postprocessing", postprocessing_function)
    
    # エッジの設定
    main_graph.add_edge(START, "preprocessing")
    main_graph.add_edge("preprocessing", "processing")
    main_graph.add_edge("processing", "postprocessing")
    main_graph.add_edge("postprocessing", END)
    
    return main_graph.compile()


# ============================================
# メイン実行
# ============================================
if __name__ == "__main__":
    print("="*60)
    print("LangGraph サブグラフの基本例（関数ノード内でサブグラフを呼び出す方法）")
    print("="*60)
    print()
    print("この方法では、サブグラフを関数ノード内で呼び出すことで、")
    print("メッセージの重複問題を回避できます。")
    print()
    
    # メイングラフの作成
    print("1. メイングラフを作成中...")
    main_agent = create_main_graph()
    print("   ✓ メイングラフの作成完了")
    print()
    
    # 実行
    print("2. グラフを実行中...")
    print("   入力: Process data")
    print()
    print("   [親グラフ: START] 初期メッセージを追加")
    print()
    
    result = main_agent.invoke({"messages": [HumanMessage(content="Process data")]})
    
    print()
    print("   [親グラフ: END] 実行完了")
    print()
    
    print("3. 実行結果:")
    print("-"*60)
    for i, message in enumerate(result["messages"], 1):
        print(f"  メッセージ {i}:")
        print(f"    タイプ: {type(message).__name__}")
        print(f"    内容: {message.content}")
        print()
    
    print("="*60)
    print("実行完了")
    print("="*60)
    print()
    print("【比較】")
    print("この方法では、メッセージの重複が発生しません。")
    print("サブグラフの実行結果から、新しく追加されたメッセージのみを")
    print("親グラフのステートに反映させることで、重複を回避しています。")
