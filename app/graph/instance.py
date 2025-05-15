import operator
from typing import TypedDict, Annotated, Sequence, List, Dict, Any

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_google_vertexai import ChatVertexAI
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode

from langchain_google_genai import ChatGoogleGenerativeAI

from .tools import custom_tools
from ..core.config import settings

from dotenv import load_dotenv

load_dotenv()

# 1. 에이전트 상태 정의
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    input: str
    # tool_outputs: List[Dict[str, Any]] | None # 필요시 도구 결과 별도 추적

# 2. LLM 및 도구 초기화
# Initialize the Gemini model
gemini_model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-preview-04-17",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0
)
tool_node = ToolNode(custom_tools)

# 3. 그래프 노드: 모델 호출
def call_model(state: AgentState):
    """LLM을 호출하여 응답을 생성합니다."""
    messages = state["messages"]
    response = llm.invoke(messages)
    return {"messages": [response]} # 기존 메시지에 응답 추가

# 4. 조건부 엣지: 다음 단계 결정
def should_continue(state: AgentState) -> str:
    """LLM의 응답에 따라 도구 사용 여부 또는 종료를 결정합니다."""
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools" # 도구 사용 요청 시 "tools" 반환
    return END # 그렇지 않으면 종료

# 5. 그래프 구성
workflow = StateGraph(AgentState)

workflow.add_node("agent", call_model) # 에이전트 노드 (LLM 호출)
workflow.add_node("tools", tool_node)  # 도구 실행 노드

workflow.set_entry_point("agent") # 시작점은 에이전트 노드

workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "tools": "tools", # "tools" 문자열 반환 시 tools 노드로
        END: END,        # END 문자열 반환 시 종료
    },
)
workflow.add_edge("tools", "agent") # 도구 사용 후 다시 에이전트 노드로

# 6. 그래프 컴파일 (메모리 저장 기능 포함)
memory_saver = MemorySaver() # 대화 기록 저장을 위한 인메모리 체커
# "tools" 노드 실행 후에는 항상 "agent" 노드로 이동하는 엣지를 추가합니다.
# 이는 도구 실행 결과를 LLM이 다시 처리하도록 하기 위함입니다.
workflow.add_edge("tools", "agent")

# 6. MemorySaver를 사용하여 그래프 컴파일 (Compile the graph with MemorySaver)
# MemorySaver는 대화 기록과 상태를 인메모리에 저장하는 체크포인터입니다.
memory_saver = MemorySaver()

# 정의된 워크플로우를 컴파일하여 실행 가능한 'app_graph' 객체를 생성합니다.
# checkpointer를 지정하여 대화 상태를 저장하고 복원할 수 있게 합니다.
app_graph = workflow.compile(checkpointer=memory_saver) 