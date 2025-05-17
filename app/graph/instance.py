import operator
from typing import TypedDict, Annotated, Sequence
import os

from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from langchain_google_genai import ChatGoogleGenerativeAI

from .grafana_mcp_agent import make_grafana_agent

from dotenv import load_dotenv

load_dotenv()

# 1. 에이전트 상태 정의
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    input: str
    # tool_outputs: List[Dict[str, Any]] | None # 필요시 도구 결과 별도 추적

# 2. LLM 및 도구 초기화
# Initialize the Gemini model
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-preview-04-17",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0
)

# 3. 그래프 노드: 에이전트 로직 (기존 call_model 대체)
async def agent_node(state: AgentState):
    async with make_grafana_agent(llm) as agent:
        return await agent.ainvoke(state["messages"])

# 4. 조건부 엣지: 다음 단계 결정
def should_continue(state: AgentState) -> str:
    """LLM의 응답에 따라 도구 사용 여부 또는 종료를 결정합니다."""
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools" # 도구 사용 요청 시 "tools" 반환
    return END # 그렇지 않으면 종료

# 5. 그래프 구성
workflow = StateGraph(AgentState)

workflow.add_node("agent", agent_node) # agent_node로 변경

workflow.set_entry_point("agent") # 시작점은 에이전트 노드

# 6. 그래프 컴파일 (메모리 저장 기능 포함)
memory_saver = MemorySaver() # 대화 기록 저장을 위한 인메모리 체커


# 정의된 워크플로우를 컴파일하여 실행 가능한 'app_graph' 객체를 생성합니다.
# LangGraph API/플랫폼이 자체적으로 체크포인터를 관리합니다.
app_graph = workflow.compile() 

print("Graph compiled successfully with MCP tool loading logic.") 