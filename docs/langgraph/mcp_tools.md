# LangGraph에서 `langchain-mcp-adapters`로 여러 MCP 서버 연동하기

이 문서는 `langchain-mcp-adapters` 라이브러리를 사용하여 여러 MCP (Multi-Context Platform) 서버에 연결하고, 각 서버에서 제공하는 도구들을 단일 LangGraph 에이전트 내에서 통합적으로 활용하는 방법을 안내합니다.

## 목차

1.  [개요](#개요)
2.  [사전 준비 사항](#사전-준비-사항)
3.  [핵심 개념: MCP Multi-Server Toolkit](#핵심-개념-mcp-multi-server-toolkit)
4.  [설정 단계](#설정-단계)
    *   [MCP 서버 연결 정보 정의](#mcp-서버-연결-정보-정의)
    *   [MCP Toolkit 초기화](#mcp-toolkit-초기화)
5.  [LangGraph 에이전트에서 MCP 도구 사용](#langgraph-에이전트에서-mcp-도구-사용)
    *   [통합 도구 목록 가져오기](#통합-도구-목록-가져오기)
    *   [`ToolNode` 생성 및 그래프 연동](#toolnode-생성-및-그래프-연동)
6.  [코드 예시](#코드-예시)
7.  [고려 사항](#고려-사항)
    *   [도구 이름 충돌](#도구-이름-충돌)
    *   [오류 처리 및 개별 서버 상태](#오류-처리-및-개별-서버-상태)
    *   [인증 관리](#인증-관리)
8.  [결론](#결론)

## 개요

`langchain-mcp-adapters`는 LangGraph 에이전트가 외부 MCP 서버들과 상호작용할 수 있도록 설계된 라이브러리입니다. 여러 MCP 서버를 사용하는 주된 이유는 각 서버가 특정 도메인에 특화된 도구나 데이터 소스, 또는 서로 다른 환경(개발, 스테이징, 프로덕션)에 대한 접근을 제공할 수 있기 때문입니다. 이 가이드는 여러 MCP 서버의 도구들을 하나의 에이전트에서 원활하게 사용하는 방법을 설명합니다.

## 사전 준비 사항

*   **LangGraph**: LangGraph 라이브러리가 설치되어 있어야 합니다.
*   **`langchain-mcp-adapters`**: `pip install langchain-mcp-adapters` 명령을 통해 라이브러리가 설치되어 있어야 합니다.
*   **MCP 서버 접속 정보**: 연동할 각 MCP 서버의 URL, 필요한 경우 API 키 또는 인증 토큰 등의 접속 정보가 준비되어 있어야 합니다.
*   각 MCP 서버는 정상적으로 실행 중이어야 합니다.

## 핵심 개념: MCP Multi-Server Toolkit

여러 MCP 서버를 연동하기 위해 `langchain-mcp-adapters`는 일반적으로 각 서버에 대한 클라이언트 설정을 관리하고, 이들로부터 도구들을 수집하여 LangGraph 에이전트에 제공하는 메커니즘을 가집니다. (라이브러리의 실제 구현에 따라 `MCPMultiServerToolkit`, `MCPRegistry` 또는 유사한 이름의 클래스나 팩토리 함수를 사용할 수 있습니다.)

이 "Toolkit" 또는 레지스트리는 다음과 같은 역할을 합니다:

*   여러 MCP 서버의 연결 설정을 등록하고 관리합니다.
*   등록된 모든 서버로부터 사용 가능한 도구 목록을 수집합니다.
*   수집된 도구들을 LangGraph 에이전트가 사용할 수 있는 형태로 변환하여 제공합니다 (예: Langchain `Tool` 객체 리스트).
*   에이전트가 특정 도구를 호출하면, 해당 도구를 제공하는 올바른 MCP 서버로 요청을 라우팅합니다.

## 설정 단계

### MCP 서버 연결 정보 정의

먼저, 연동할 각 MCP 서버에 대한 연결 정보를 정의해야 합니다. 이는 일반적으로 Python 딕셔너리나 객체의 리스트 형태로 구성됩니다. 각 서버 설정에는 고유 식별 이름, 서버 URL, 그리고 필요한 인증 정보(API 키 등)가 포함되어야 합니다.

**예시 (Python 리스트와 딕셔너리 사용):**

```python
mcp_server_configs = [
    {
        "name": "mcp_server_alpha", # 이 서버를 식별하기 위한 고유 이름
        "url": "http://mcp-alpha.example.com/api",
        "api_key": "YOUR_ALPHA_SERVER_API_KEY",
        "description": "Alpha MCP 서버 - 일반적인 유틸리티 도구 제공"
    },
    {
        "name": "mcp_server_beta_analytics",
        "url": "https://mcp-beta.example.com/v1",
        "auth_token": "YOUR_BETA_SERVER_AUTH_TOKEN",
        "description": "Beta MCP 서버 - 데이터 분석 및 리포팅 도구 제공"
    },
    # 필요에 따라 더 많은 서버 설정 추가
]
```

### MCP Toolkit 초기화

정의된 서버 연결 정보 리스트를 사용하여 `MCPMultiServerToolkit` (또는 유사한 기능을 하는 어댑터 클래스)를 초기화합니다.

```python
# from langchain_mcp_adapters import MCPMultiServerToolkit # 실제 클래스명은 라이브러리 문서를 따름

# 가정: MCPMultiServerToolkit 클래스가 존재한다고 가정
# mcp_toolkit = MCPMultiServerToolkit(server_configs=mcp_server_configs)

# 만약 개별 어댑터를 생성하고 수동으로 관리해야 한다면:
# from langchain_mcp_adapters import MCPClientAdapter # 또는 MCPTools, MCPToolbelt 등

# mcp_tools_list = []
# for config in mcp_server_configs:
#     adapter = MCPClientAdapter(name=config['name'], url=config['url'], api_key=config.get('api_key'), auth_token=config.get('auth_token'))
#     # 가정: adapter.get_tools()가 Langchain Tool 객체 리스트를 반환
#     # 또는 adapter.get_langchain_tools() 등 실제 메소드명 사용
#     server_specific_tools = adapter.get_tools() 
#     mcp_tools_list.extend(server_specific_tools)
```

*참고: `langchain-mcp-adapters` 라이브러리의 정확한 클래스 및 메소드 이름은 공식 문서를 참조해야 합니다. 위 코드는 일반적인 패턴을 예시로 보여줍니다.*

## LangGraph 에이전트에서 MCP 도구 사용

### 통합 도구 목록 가져오기

Toolkit (또는 수동으로 구성한 도구 리스트)으로부터 LangGraph 에이전트가 사용할 수 있는 모든 MCP 도구의 통합된 리스트를 가져옵니다.

```python
# MCPMultiServerToolkit 사용 시 (가정)
# all_mcp_tools = mcp_toolkit.get_all_tools()

# 수동으로 리스트를 구성한 경우
# all_mcp_tools = mcp_tools_list # 위에서 생성한 mcp_tools_list
```

이 `all_mcp_tools`는 Langchain `Tool` 객체들의 리스트여야 합니다.

### `ToolNode` 생성 및 그래프 연동

가져온 도구 목록을 사용하여 LangGraph의 `ToolNode`를 생성하고, 이를 에이전트의 상태 그래프에 추가합니다.

```python
from langgraph.prebuilt import ToolNode

# all_mcp_tools 가 Langchain Tool 객체들의 리스트라고 가정
tool_node = ToolNode(all_mcp_tools)

# LangGraph 상태 그래프 정의 (예시)
# from langgraph.graph import StateGraph, END
# workflow = StateGraph(AgentState) # AgentState는 사전에 정의 필요
# workflow.add_node("tools", tool_node)
# ... 기타 노드 및 엣지 설정 ...
```

## 코드 예시

다음은 여러 MCP 서버의 도구를 LangGraph 에이전트에 통합하는 간소화된 전체 흐름 예시입니다.
여기서는 Grafana MCP와 Grafana Renderer MCP를 연동하는 상황을 가정합니다.

```python
import os
from typing import TypedDict, Annotated, Sequence
import operator
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool
# from langchain_openai import ChatOpenAI # 또는 다른 LLM 사용. 예시에서는 LLM 직접 호출 생략.
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode, tools_condition

# from langchain_mcp_adapters import MCPMultiServerToolkit, MCPClientAdapter # 실제 라이브러리 경로 및 클래스명 확인 필요

# --- 1. MCP 서버 설정 정의 (환경 변수에서 로드) ---
# .env 파일 예시:
# GRAFANA_MCP_URL=http://localhost:8091/api
# GRAFANA_MCP_API_KEY=your_grafana_mcp_api_key_here
# GRAFANA_RENDERER_MCP_URL=http://localhost:8090/api 
# GRAFANA_RENDERER_MCP_API_KEY=your_grafana_renderer_mcp_api_key_here
# OPENAI_API_KEY=your_openai_api_key_here (LLM 사용 시)

mcp_server_configs = [
    {
        "name": "grafana_mcp_server",
        "url": os.getenv("GRAFANA_MCP_URL", "http://localhost:8091/api"), # mcp/grafana/docker-compose.yml 참조
        "api_key": os.getenv("GRAFANA_MCP_API_KEY"),
        "description": "Grafana MCP - 대시보드 목록 조회, 관리 등"
    },
    {
        "name": "grafana_renderer_mcp_server",
        "url": os.getenv("GRAFANA_RENDERER_MCP_URL", "http://localhost:8090/api"), # mcp/grafana/docker-compose.yml 참조
        "api_key": os.getenv("GRAFANA_RENDERER_MCP_API_KEY"), # 렌더러도 API 키가 필요할 수 있음
        "description": "Grafana Renderer MCP - 대시보드 패널 이미지 렌더링"
    }
]

# --- 2. MCP 도구 준비 ---
# 이 부분은 langchain-mcp-adapters 라이브러리의 실제 API에 따라 달라집니다.
# 여기서는 각 서버에 대해 MCPClientAdapter를 만들고 도구를 수동으로 모으는 방식을 가정합니다.

all_mcp_tools = []
# for config in mcp_server_configs:
#     try:
#         print(f"Initializing adapter for {config['name']} at {config['url']}")
#         # 실제 어댑터 클래스 및 초기화 방식은 라이브러리 문서를 따라야 합니다.
#         # adapter = MCPClientAdapter(
#         #     name=config['name'],
#         #     url=config['url'],
#         #     api_key=config.get('api_key') 
#         # )
#         # server_tools = adapter.get_langchain_tools() # 또는 get_tools()
#         # print(f"Found tools for {config['name']}: {[tool.name for tool in server_tools]}")
#         # all_mcp_tools.extend(server_tools)
#     except Exception as e:
#         print(f"Error initializing adapter for {config['name']}: {e}")

# 임시: 실제 어댑터가 없으므로 Grafana 관련 예시 도구 직접 생성
# 실제 어댑터 사용 시 이 @tool 데코레이터로 정의된 함수들은 제거하고,
# 어댑터를 통해 가져온 Tool 객체들을 all_mcp_tools 리스트에 추가합니다.

@tool
def list_grafana_dashboards() -> list[dict]:
    \"\"\"Grafana MCP 서버에서 사용 가능한 모든 대시보드 목록을 가져옵니다. (grafana_mcp_server 제공)\"\"\"
    print(f"Mock call to grafana_mcp_server: list_grafana_dashboards (URL: {os.getenv('GRAFANA_MCP_URL')})")
    # 실제 API 호출 대신 모의 데이터 반환
    return [
        {"uid": "sales_overview_01", "title": "Sales Overview Dashboard"},
        {"uid": "system_health_prod", "title": "Production System Health"}
    ]

@tool
def render_grafana_dashboard_panel(dashboard_uid: str, panel_id: int, width: int = 800, height: int = 400) -> str:
    \"\"\"Grafana Renderer MCP 서버를 사용하여 특정 대시보드의 특정 패널을 이미지 URL 형태로 렌더링합니다. (grafana_renderer_mcp_server 제공)\"\"\"
    print(f"Mock call to grafana_renderer_mcp_server: render_grafana_dashboard_panel (URL: {os.getenv('GRAFANA_RENDERER_MCP_URL')})")
    print(f"Params: dashboard_uid={dashboard_uid}, panel_id={panel_id}, width={width}, height={height}")
    # 실제 API 호출 대신 모의 이미지 URL 반환
    return f"http://mock.renderer.example.com/render/d-solo/{dashboard_uid}/?panelId={panel_id}&width={width}&height={height}&orgId=1&theme=light"

if not all_mcp_tools: # 실제 어댑터에서 도구를 가져오지 못한 경우, 모의 도구 사용
    print("Warning: No MCP tools loaded via adapters. Using dummy Grafana tools for graph construction.")
    all_mcp_tools = [list_grafana_dashboards, render_grafana_dashboard_panel]

# --- 3. LangGraph 에이전트 상태 정의 ---
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]

# --- 4. LLM 및 그래프 구성 ---
# LLM 초기화 (예시에서는 LLM 직접 호출 생략, 실제 사용 시 API 키 필요)
# llm = ChatOpenAI(model="gpt-4o", api_key=os.getenv("OPENAI_API_KEY"))

def agent_node(state: AgentState): # llm_model 인자 제거 (예시 단순화)
    last_message = state["messages"][-1]
    if not isinstance(last_message, HumanMessage): # 마지막 메시지가 HumanMessage가 아니면 응답하지 않음
        return {"messages": []} # 또는 특정 메시지 반환

    content = last_message.content.lower()
    tool_calls = []

    if "대시보드 목록" in content or "list dashboards" in content:
        tool_calls.append({"name": "list_grafana_dashboards", "args": {}, "id": "tool_list_dashboards"})
    
    if "패널 렌더링" in content or "render panel" in content:
        # 실제 에이전트는 메시지에서 dashboard_uid와 panel_id를 추출해야 합니다.
        # 여기서는 예시로 고정된 값을 사용합니다.
        args = {"dashboard_uid": "sales_overview_01", "panel_id": 2}
        if "시스템 상태" in content or "system health" in content :
             args = {"dashboard_uid": "system_health_prod", "panel_id": 1}

        tool_calls.append({"name": "render_grafana_dashboard_panel", "args": args, "id": "tool_render_panel"})

    if tool_calls:
        return {"messages": [AIMessage(content="요청하신 작업을 위해 다음 도구를 사용합니다.", tool_calls=tool_calls)]}
    
    return {"messages": [AIMessage(content="안녕하세요! Grafana 대시보드 목록 조회 또는 패널 렌더링을 요청할 수 있습니다.")]}

tool_node = ToolNode(all_mcp_tools)

# 그래프 정의
workflow = StateGraph(AgentState)
workflow.add_node("agent", agent_node)
workflow.add_node("tools", tool_node)

workflow.set_entry_point("agent")
workflow.add_conditional_edges(
    "agent",
    tools_condition,
    {"tools": "tools", END: END}
)
workflow.add_edge("tools", "agent")

app = workflow.compile()

# --- 5. 에이전트 실행 (예시) ---
def run_agent_example(input_message: str):
    print(f"\\n--- Running agent with input: '{input_message}' ---")
    initial_input = {"messages": [HumanMessage(content=input_message)]}
    for event in app.stream(initial_input, {"recursion_limit": 10}):
        for key, value in event.items():
            if key == "messages":
                for msg in value:
                    if isinstance(msg, AIMessage) and msg.tool_calls:
                        print(f"Event: {key}, Value: AIMessage with tool_calls: {msg.tool_calls}")
                    elif isinstance(msg, ToolMessage):
                         print(f"Event: {key}, Value: ToolMessage (id: {msg.tool_call_id}, content: {msg.content[:100]})") # 너무 길면 잘라서 출력
                    else:
                        print(f"Event: {key}, Value: {msg}")
            else:
                 print(f"Event: {key}, Value: {value}")
        print("----")

print("LangGraph app with Grafana MCP tools compiled successfully.")
print(f"Loaded tools: {[tool.name for tool in all_mcp_tools]}")
print("Please ensure environment variables (e.g., GRAFANA_MCP_URL, GRAFANA_RENDERER_MCP_URL) are set.")

# 실행 예시 (주석 해제하여 테스트)
# run_agent_example("대시보드 목록 보여줘.")
# run_agent_example("sales_overview_01 대시보드의 2번 패널 렌더링 해줘.") # agent_node가 이 입력을 직접 파싱하진 않음. "패널 렌더링" 키워드로 동작.
# run_agent_example("시스템 상태 대시보드 패널 렌더링 해줘.")

## 고려 사항

### 도구 이름 충돌

서로 다른 MCP 서버에서 제공하는 도구의 이름이 동일할 경우 충돌이 발생할 수 있습니다. `langchain-mcp-adapters` 라이브러리가 이를 자동으로 처리하는 방법(예: 서버 이름으로 접두사 추가 `mcp_server_alpha_calculator`)을 제공하거나, 사용자가 직접 도구 이름을 관리하거나 호출 시 명시적으로 서버를 지정해야 할 수 있습니다. 라이브러리 문서를 확인하여 이름 충돌 해결 전략을 파악해야 합니다.

### 오류 처리 및 개별 서버 상태

여러 서버 중 하나의 서버가 응답하지 않거나 오류를 반환하는 경우에 대한 에이전트의 오류 처리 로직을 견고하게 설계해야 합니다. Toolkit이나 어댑터가 개별 서버의 상태를 모니터링하거나, 특정 서버의 도구 호출 실패 시 대체 동작을 정의할 수 있는지 확인합니다.

### 인증 관리

각 MCP 서버가 서로 다른 인증 방식(API 키, OAuth 토큰 등)을 사용할 수 있습니다. 이러한 인증 정보들을 안전하게 저장하고 각 서버에 대한 요청 시 올바르게 사용하도록 구성해야 합니다. 환경 변수, 비밀 관리 시스템(예: HashiCorp Vault, GCP Secret Manager) 등을 활용하는 것이 좋습니다.

## 결론

`langchain-mcp-adapters`를 활용하여 여러 MCP 서버의 도구들을 LangGraph 에이전트에 통합하면, 더욱 강력하고 다양한 기능을 갖춘 지능형 애플리케이션을 구축할 수 있습니다. 각 MCP 서버의 전문화된 기능을 활용하여 에이전트의 문제 해결 능력을 극대화할 수 있습니다.

항상 `langchain-mcp-adapters`의 공식 문서를 참조하여 최신 정보와 정확한 API 사용법을 확인하는 것이 중요합니다.
