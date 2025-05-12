# LangGraph 관련 주요 라이브러리 정리

> **LangGraph** 생태계에서 확장·통합 기능을 담당하는 두 가지 대표 라이브러리 **LangGraph Supervisor** 와 **LangGraph MCP Adapters** 를 소개합니다. 각 라이브러리의 특징, 사용 방법, 코드 예시를 한 눈에 파악할 수 있도록 구조화했습니다.

---

## 1. LangGraph Supervisor

계층형(Hierarchical)·네트워크형 멀티 에이전트 시스템을 **간편하게 설계·관리** 할 수 있게 해주는 Python 라이브러리입니다.

### 1.1 주요 특징

| 기능 | 설명 |
| --- | --- |
| **계층형 멀티 에이전트** | Supervisor → Worker/Sub-Agent 구조로 역할 분담 및 제어 |
| **그래프 기반 워크플로** | `StateGraph` 로 노드(에이전트)와 작업 흐름(엣지)을 정의 |
| **함수형 파이프라인** | 에이전트를 함수형으로 선언해 데이터 흐름을 직관적으로 표현 |
| **서브그래프 지원** | 각 에이전트를 **SubGraph** 로 캡슐화 → 복잡한 계층도 손쉽게 모델링 |

### 1.2 핵심 구성 요소

| 구성 요소 | 역할 |
| --- | --- |
| **Supervisor Agent** | 전체 작업 흐름 관리, Worker 선정, 종료 조건 판단 |
| **Worker / Sub-Agent** | 실제 작업 수행(검색, 코딩, 수학 계산 등), 각자 도구 보유 |
| **StateGraph** | 에이전트와 데이터 흐름 정의, 조건·병렬 실행·분기 지원 |

### 1.3 코드 예시 (요약)
```python
from langgraph_supervisor import create_supervisor
from langgraph.prebuilt.chat_agent_executor import create_react_agent
from langchain_community.chat_models import ChatOpenAI

model = ChatOpenAI()

# 서브에이전트 생성
researcher = create_react_agent(name="researcher", model=model, tools=[web_search])
math_agent = create_react_agent(name="math_expert", model=model, tools=[add, multiply])

# Supervisor 구성
supervisor = create_supervisor(
    agents=[researcher, math_agent],
    model=model,
    prompt="You are a team supervisor managing a research expert and a math expert.",
    parallel_tool_calls=True,
    output_mode="last_message",
)

graph = supervisor.compile()
result = graph.invoke({"messages": [{"content": "FAANG 회사들의 2024년 총 직원 수는?"}]})
```

### 1.4 장점

* **확장성**: 에이전트 수가 늘어날수록 Supervisor 아키텍처의 효율성이 극대화.
* **유연성**: 각 에이전트는 독립 개발·테스트 가능, Supervisor 레이어에서 손쉽게 재구성.
* **재사용성**: 함수형 스타일 + `partial` 활용으로 노드 생성 및 파이프라인 재사용 용이.

### 1.5 주요 API

| 함수/메서드 | 설명 |
| --- | --- |
| `create_supervisor` | Supervisor 에이전트 생성, 하위 에이전트 등록 |
| `create_react_agent` | Tool-calling SubGraph(Worker) 생성 |
| `StateGraph` | 그래프 정의, 노드·엣지 추가 |
| `.compile()` | `StateGraph` → 실행 가능한 `CompiledGraph` 변환 |

### 1.6 요약

LangGraph Supervisor는 복잡한 멀티 에이전트 시스템을 **계층적** 또는 **네트워크형** 으로 쉽게 구축할 수 있도록 돕는 라이브러리입니다. 그래프 기반 파이프라인과 함수형 설계로 **유연성·확장성·유지보수성**을 모두 확보할 수 있습니다.

---

## 2. LangGraph MCP Adapters

Anthropic의 **Model Context Protocol(MCP)** 을 사용하는 외부 도구(서버)를 LangChain/LangGraph 에이전트에 **손쉽게 연결** 해주는 경량 래퍼 라이브러리입니다.

### 2.1 주요 특징

* MCP 서버의 **Tool** 을 자동 감지·래핑해 LangChain/LangGraph 호환 객체로 변환
* **복수 MCP 서버** 동시 연결 및 도구 **동적 로딩** 지원
* `stdio`, **SSE** 등 다양한 통신 방식 + **실시간 스트리밍** 대응
* 도구 추가/삭제를 런타임에 처리하여 **유연한 확장** 가능

### 2.2 설치
```bash
pip install langchain-mcp-adapters  # + (필요 시) pip install mcp
```

### 2.3 사용법

#### 2.3.1 MCP 서버 구현 예시
```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Math")

@mcp.tool()
def add(a: int, b: int) -> int:
    return a + b

@mcp.tool()
def multiply(a: int, b: int) -> int:
    return a * b

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

#### 2.3.2 LangGraph 에이전트에서 MCP 도구 사용
```python
from langchain_mcp_adapters.tools import load_mcp_tools
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langgraph.prebuilt import create_react_agent

server_params = StdioServerParameters(
    command="python",
    args=["/path/to/math_server.py"],
)

async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        tools = await load_mcp_tools(session)
        agent = create_react_agent("google:gemini-1.0-pro", tools)
        answer = await agent.ainvoke({"messages": "what's (3 + 5) x 12?"})
```

#### 2.3.3 복수 MCP 서버 연결 예시
```python
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

async with MultiServerMCPClient(
    {
        "math": {
            "command": "python",
            "args": ["/path/to/math_server.py"],
            "transport": "stdio",
        },
        "weather": {
            "url": "http://localhost:8000/sse",
            "transport": "sse",
        },
    }
) as client:
    agent = create_react_agent("anthropic:claude-3-sonnet", client.get_tools())
    math_resp = await agent.ainvoke({"messages": "(3 + 5) x 12?"})
    weather_resp = await agent.ainvoke({"messages": "weather in NYC?"})
```

### 2.4 장점

* **외부 시스템 통합**: RAG, 검색, 멀티모달 분석 등 외부 도구를 손쉽게 연결
* **실시간 스트리밍**: SSE·WebSocket 기반 서버와 연동 시 즉시 응답 스트림 처리
* **표준 프로토콜**: MCP 준수로 언어·플랫폼 상관없이 상호운용성 확보

### 2.5 요약

LangGraph MCP Adapters는 MCP 도구를 **LangGraph/ LangChain** 에이전트 생태계로 편리하게 가져오는 **오픈소스** 라이브러리입니다. 여러 MCP 서버·다양한 통신 방식·스트리밍 지원으로 **확장성**과 **유연성**을 대폭 향상시켜 줍니다.

---

## 3. 결론

두 라이브러리는 **LangGraph** 기반 멀티 에이전트 시스템의 설계·확장·도구 통합을 간소화합니다.

| 라이브러리 | 핵심 역할 | 언제 사용하나? |
| --- | --- | --- |
| **LangGraph Supervisor** | 계층형/네트워크형 멀티 에이전트 **조율·관리** | 팀·파이프라인 기반 작업 분할/집계가 필요한 경우 |
| **LangGraph MCP Adapters** | 외부 **MCP 도구**를 LangGraph/LC 에이전트에 통합 | 검색·RAG·멀티모달·계산 등 외부 기능을 도구 형태로 호출할 때 |

> 추가적인 예제나 심화 가이드는 공식 레포지토리 및 `how-to` 문서를 참고하세요.