# LangGraph 핵심 컴포넌트 정리

> 이 문서는 LangGraph를 사용하여 에이전트(Agent) 기반 애플리케이션을 개발‧운영할 때 알아두어야 할 핵심 컴포넌트와 개념을 정리한 것입니다. 아래 내용을 바탕으로 FastAPI 애플리케이션 안에서 LangGraph 워크플로를 손쉽게 서빙할 수 있습니다.

---

## 1. 그래프 정의(Definition) 계층

| 컴포넌트 | 설명 |
| --- | --- |
| **StateGraph API** | 노드(Node)와 에지(Edge)를 명시적으로 연결해 멀티-스텝 LLM 워크플로를 그래프로 정의하는 저수준(high-control) API. 복잡한 분기, 조건, 반복 로직에 유리합니다. |
| **Functional API (@entrypoint / @task)** | 기존 파이썬 함수에 간단히 데코레이터만 붙여 LangGraph 기능(상태 관리, 휴먼-인-더-루프, 병렬 실행 등)을 끌어올 수 있는 고수준 API. 빠르게 기존 코드를 그래프화할 때 적합합니다. |
| **Subgraph** | 그래프 내부에서 재사용 가능한 하위 그래프. 복잡한 시스템을 모듈화해 유지보수를 단순화합니다. |

## 2. 실행(Runtime) 계층

| 컴포넌트 | 설명 |
| --- | --- |
| **Pregel Runtime** | LangGraph 내부 실행 엔진으로, `Plan → Execute → Update` 3-단계로 그래프를 평가합니다. 병렬성·에러 복구·중단점(checkpoint) 등을 담당합니다. |
| **Node / Task** | 그래프의 최소 실행 단위. 함수·LLM 호출·외부 API 호출 등 임의의 파이썬 로직을 담을 수 있습니다. |
| **Edge** | 노드 간 데이터・흐름을 연결하며, 조건부 분기(Guard), 반복(Loop) 등을 표현합니다. |

## 3. 상태(State) & 메모리 계층

| 컴포넌트 | 설명 |
| --- | --- |
| **Thread-Scoped Memory** | 단일 대화/플로우 동안 유지되는 짧은 메모리. 채팅 히스토리, 직전 단계 결과 등을 저장합니다. |
| **Long-Term Memory (Store)** | 여러 스레드에 걸쳐 재사용되는 데이터(브레인)을 위한 영속 스토어. RAG 문서 요약, 사용자 프로필 등. |
| **Checkpointer** | 각 노드 실행 후 스냅샷을 저장해 재실행, 포크(Fork), 시간 여행(Time-Travel) 디버깅을 가능하게 합니다. |

## 4. 사용자 개입(Human-in-the-Loop)

| 컴포넌트 | 설명 |
| --- | --- |
| **Interrupt / Command** | 특정 지점에서 `interrupt()`로 실행을 일시 정지한 뒤, 외부(사람) 입력을 `Command` 객체로 받아 그래프 실행을 재개할 수 있습니다. 승인이 필요한 리뷰/RAIL 정책 적용 시 활용합니다. |

## 5. 스트리밍(Streaming)

| 모드 | 주요 사용처 |
| --- | --- |
| **values** | 단계별 최종 값을 실시간으로 전송. REST·WebSocket 양쪽 지원. |
| **updates** | 노드 단위 중간 산출물을 지속 스트림. |
| **messages / events / debug** | 대화 메시지, 사용자 정의 상태, 낮은 수준 디버그 로그 스트림. |

## 6. 플랫폼(Deployment & Ops)

| 컴포넌트 | 설명 |
| --- | --- |
| **LangGraph Server** | 그래프를 API 서버로 노출하는 런타임. 스레드, 런, 백그라운드 작업, Cron, Webhook, 모니터링 등을 제공. |
| **LangGraph Studio** | 그래프 시각화·인스펙션 UI. 노드별 상태, 메모리, 스트림을 실시간으로 확인 & 수정 가능합니다. |
| **LangGraph CLI** | `langgraph dev`, `langgraph up`, `langgraph build` 등 로컬-서버 실행, Dockerfile 빌드, 핫 리로딩 지원. |
| **LangGraph SDK (Python/JS)** | 원격(Server/Cloud) 그래프 실행·관리용 API 클라이언트. 동기/비동기 버전 제공. |
| **LangGraph Platform (Cloud/Self-Hosted)** | 수 분만에 자동 스케일링 배포. Redis+Postgres 백엔드, 모니터링, 버스티 트래픽 처리, SLA, IP 화이트리스트 지원. |

## 7. 어시스턴트(Assistants)

LangGraph Platform 전용 기능으로, 그래프 로직을 수정하지 않고도 **프롬프트·모델·파라미터** 와 같은 에이전트 설정을 버전 관리하며 변경할 수 있습니다.

## 8. FastAPI 연동 가이드

```python
# app/main.py
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, JSONResponse
from langgraph import StateGraph
from langgraph.runtime import serve

# 1) 그래프 정의 (예시는 간단한 Echo 노드)
async def echo_node(state):
    user_input = state["input"]
    return {"output": f"Echo: {user_input}"}

graph = StateGraph()
_ = graph.set_entrypoint("echo", echo_node)

# 2) FastAPI 애플리케이션 생성
app = FastAPI()

# 3) REST 엔드포인트: 동기 실행
@app.post("/run")
async def run_graph(request: Request):
    body = await request.json()
    state = {"input": body.get("message")}
    result = await graph.invoke(state)
    return JSONResponse(result)

# 4) WebSocket or Server-Sent Events를 활용한 스트리밍 예시
@app.post("/stream")
async def stream_graph(request: Request):
    body = await request.json()
    state = {"input": body.get("message")}

    async def event_generator():
        async for chunk in graph.stream(state, mode="values"):
            yield chunk  # 필요 시 JSON 직렬화

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# 5) Uvicorn 실행 예시 (CLI)
# uvicorn app.main:app --host 0.0.0.0 --port 8000
```

> FastAPI에서 LangGraph를 사용할 때는 그래프 객체를 애플리케이션 전역(singleton)으로 생성하여 재사용하고, 각 요청마다 상태(State)만 분리하면 됩니다. 스트리밍은 `StreamingResponse` + `graph.stream()` 조합으로 간단히 구현할 수 있습니다.

---

## 9. 참고 링크

- 공식 개념 문서: <https://langchain-ai.github.io/langgraph/concepts/>
- Functional API: <https://langchain-ai.github.io/langgraph/concepts/functional_api/>
- LangGraph Server: <https://langchain-ai.github.io/langgraph/concepts/langgraph_server/>
- Human-in-the-Loop: <https://langchain-ai.github.io/langgraph/concepts/human_in_the_loop/>
- Streaming 설명: <https://langchain-ai.github.io/langgraph/concepts/streaming/>
- Template Apps: <https://langchain-ai.github.io/langgraph/concepts/template_applications/>

---

### 요약
1. **그래프 정의 → 실행 → 상태 관리** 세 층을 이해하면 LangGraph 마스터.
2. **스트리밍 & 휴먼-인-더-루프**를 통한 실시간 반응형·안전한 워크플로 구현.
3. FastAPI와의 통합은 `graph.invoke()` / `graph.stream()` 두 가지 메서드로 충분.
4. LangGraph Server/Platform을 통해 배포·모니터링·스케일링까지 원-스톱으로 해결 가능.
