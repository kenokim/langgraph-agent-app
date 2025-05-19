# LangGraph를 활용한 멀티 에이전트 시스템 구축 가이드

LangGraph와 `langgraph-supervisor`를 사용하면 ReAct 기반의 하위 에이전트와 이를 조정하는 상위 감독자로 구성된 멀티-에이전트 시스템을 비교적 간단하게 구축할 수 있습니다. 이 문서는 그 핵심 패턴과 확장 지점을 설명합니다.

## 기본 패턴: Supervisor와 ReAct 에이전트

가장 단순한 형태는 `create_react_agent`로 개별 전문 에이전트(하위 에이전트)를 정의하고, `langgraph_supervisor`의 `create_supervisor`를 사용하여 이들을 조정하는 중앙 조정자(상위 에이전트)를 만드는 것입니다.

### 1. 필요 패키지 설치 (2025년 5월 기준)

```bash
pip install -U "langgraph[openai]>=0.3" langgraph-supervisor langchain-openai
```

### 2. Python 코드 예제

```python
# 1) 필요한 모듈 임포트
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent  # ReAct 에이전트 생성을 위함
from langgraph_supervisor import create_supervisor # 멀티-에이전트 조정자 생성을 위함

# 2) 외부 도구(Tools) 정의 - 간단한 함수로도 충분합니다.
def book_hotel(hotel_name: str):
    """지정된 이름의 호텔을 예약합니다."""
    print(f"호텔 예약 시도: {hotel_name}")
    return f"{hotel_name} 호텔 예약이 완료되었습니다!"

def book_flight(origin: str, dest: str):
    """지정된 출발지와 도착지의 항공권을 예약합니다."""
    print(f"항공권 예약 시도: {origin} -> {dest}")
    return f"{origin}에서 {dest}로 가는 항공권 예약이 완료되었습니다!"

# 3) ReAct 기반 하위 에이전트 2개 생성
# 비행 예약 에이전트
flight_agent_runnable = create_react_agent(
    model="openai:gpt-4o",  # OpenAI의 Tool-calling을 지원하는 모델 지정
    tools=[book_flight],    # 이 에이전트가 사용할 도구 목록
    prompt="You are a specialized assistant for booking flights. Only handle flight booking tasks.",
    name="flight_agent",    # Supervisor가 이 에이전트를 식별할 때 사용할 이름
)

# 호텔 예약 에이전트
hotel_agent_runnable = create_react_agent(
    model="openai:gpt-4o",
    tools=[book_hotel],
    prompt="You are a specialized assistant for booking hotels. Only handle hotel booking tasks.",
    name="hotel_agent",
)

# 4) 중앙 조정자(Supervisor) 생성
# Supervisor는 여러 에이전트들을 관리하며, 작업 분배 및 결과 취합을 담당합니다.
supervisor_graph = create_supervisor(
    agents=[flight_agent_runnable, hotel_agent_runnable], # 관리할 에이전트 목록
    model=ChatOpenAI(model="gpt-4o"),  # "어떤 에이전트에게 먼저 작업을 맡길지" 판단하는 LLM
    prompt=(
        "You are a helpful assistant that manages a flight-booking agent and a hotel-booking agent. "
        "Based on the user's request, delegate subtasks to the appropriate agent. "
        "Once all tasks are complete, combine their results into a final response for the user."
    ),
).compile()  # 그래프 객체를 실행 가능하도록 컴파일

# 5) 시스템 실행 (스트리밍 방식)
# 사용자 요청을 담은 메시지를 전달하여 그래프 실행을 시작합니다.
user_request = "보스턴(BOS)에서 뉴욕(JFK)으로 가는 비행기를 예약하고, 뉴욕의 맥키트릭 호텔도 예약해주세요."

initial_messages = {
    "messages": [{
        "role": "user",
        "content": user_request
    }]
}

print(f"\n--- 사용자 요청: {user_request} ---")
for delta_event in supervisor_graph.stream(initial_messages):
    # delta_event는 {'messages': [...]} 형태의 증분 결과(델타)를 포함하며, 순차적으로 출력됩니다.
    # 각 델타는 시스템 내부의 상태 변화나 메시지 흐름을 나타냅니다.
    print(delta_event)

print("--- 실행 완료 ---")
```

### 3. 동작 흐름

1.  **요청 분석 및 순서 결정:** Supervisor LLM이 전체 사용자 요청을 분석하여, 예를 들어 "항공권 예약 → 호텔 예약"과 같이 작업 순서를 결정합니다.
2.  **하위 에이전트 작업 수행:** 각 하위 에이전트(여기서는 `flight_agent`와 `hotel_agent`)는 ReAct 루프(생각 → 도구 호출 → 관찰)를 통해 자신의 전문 분야 작업을 수행합니다.
3.  **결과 취합 및 최종 응답:** 모든 하위 작업이 완료되면, 해당 메시지들이 Supervisor에게 전달됩니다. Supervisor는 이 결과들을 바탕으로 최종 응답을 작성하여 사용자에게 스트림 형태로 반환합니다.

*   **참고:** 시스템 내부의 상세한 토큰 사용량 기록이나 에이전트 간 핸드오프(작업 전달) 세부 메시지는 [LangSmith](https://smith.langchain.com/)와 같은 트레이싱 도구를 통해 확인할 수 있습니다.

## 패턴 확장 포인트

이 기본 패턴을 확장할 수 있는 몇 가지 주요 지점은 다음과 같습니다.

| 필요 사항                     | 코드 내 관련 위치                                  | 간단 팁                                                                                                |
| :---------------------------- | :------------------------------------------------- | :----------------------------------------------------------------------------------------------------- |
| **툴(Tool) 추가/변경**        | `tools=[...]` (in `create_react_agent`)            | 간단한 함수, 클래스 메서드, 또는 LangChain `Tool` 객체 등 다양한 형태의 툴을 사용할 수 있습니다.                               |
| **다단계 의사결정 로직 강화** | `prompt=` (in `create_supervisor`)                 | Supervisor의 프롬프트에 "1단계: 전체 계획 수립 후, 2단계: 각 계획 실행"과 같이 명시하여 더 복잡한 작업 흐름을 유도할 수 있습니다. |
| **에이전트 간 직접 핸드오프** | `langgraph-swarm` (별도 라이브러리 또는 직접 구현) | `langgraph_supervisor` 대신 `langgraph-swarm`의 `create_handoff_tool()` 등을 사용하거나, `Command` 객체를 반환하는 커스텀 툴을 만들어 특정 에이전트에게 직접 제어를 넘길 수 있습니다. (샘플은 아래 참고) |
| **대화형 세션 기억/관리**   | `checkpointer=` (Graph 컴파일 시)                    | `InMemorySaver` (간단한 테스트용), 또는 `RedisSaver`, `SqliteSaver`, `MongoSaver` 등 외부 저장소를 사용하는 체크포인터를 주입하여 대화 상태를 지속시킬 수 있습니다. |
| **애플리케이션 서버로 배포**  | `langserve`                                        | 생성된 `supervisor_graph` (컴파일된 그래프)를 [LangServe](https://python.langchain.com/docs/langserve)를 사용하여 FastAPI 엔드포인트로 쉽게 노출할 수 있습니다. |

## 에이전트 간 직접 핸드오프가 필요한 경우

Supervisor 패턴 대신, 여러 에이전트가 서로 직접적으로 제어를 주고받는 **Swarm 아키텍처**를 고려할 수 있습니다. 이 경우, 한 에이전트가 특정 조건에 따라 다른 에이전트에게 작업을 명시적으로 전달할 수 있습니다.

핵심 아이디어는 "전달용 툴(Handoff Tool)"을 만들어, 이 툴이 실행될 때 `Command(goto="다음노드이름", graph=Command.PARENT)`와 같은 특별한 객체를 반환하도록 하는 것입니다. `goto`는 다음으로 실행될 노드(에이전트)의 이름을 지정하고, `graph=Command.PARENT`는 현재 서브그래프(만약 있다면)를 벗어나 상위 그래프 레벨에서 라우팅하도록 지시합니다.

자세한 구현 방법과 전체 예제는 LangGraph 공식 문서의 **Agent Handoffs** 또는 Swarm 관련 섹션을 참고하는 것이 좋습니다.

*관련 문서 링크 (예시): [LangGraph Multi-agent Systems](https://langchain-ai.github.io/langgraph/concepts/multi_agent/)*