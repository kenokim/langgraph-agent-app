import os
from langgraph_supervisor import create_supervisor
from langgraph.checkpoint.memory import MemorySaver
from langchain_google_genai import ChatGoogleGenerativeAI

from .grafana_mcp_agent import make_grafana_agent, make_grafana_renderer_agent
from .server_info_agent import make_server_info_agent
from dotenv import load_dotenv

load_dotenv()

# init LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-preview-04-17",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0
)

# Grafana 에이전트
grafana_agent = make_grafana_agent(llm)
grafana_renderer_agent = make_grafana_renderer_agent(llm)

# Server Info 에이전트
server_info_agent = make_server_info_agent(llm)

# Supervisor 그래프
supervisor_graph = create_supervisor(
    agents=[grafana_agent, grafana_renderer_agent, server_info_agent],
    model=llm,
    prompt=(
        "너는 명령을 듣고 답하는 에이전트야. 그라파나 대시보드를 보여달라고 요청받으면, grafana_renderer_agent에게 명령을 전달해줘. 그라파나 대시보드 관련 명령인데, 보여달라는 요청 외의 것은 grafana_agent에게 명령을 전달해줘."
    )
)

memory_saver = MemorySaver()

app_graph = supervisor_graph.compile()
