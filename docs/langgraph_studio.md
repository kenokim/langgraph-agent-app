# LangGraph Studio 활용 가이드

> LangGraph Studio는 LangGraph로 구축된 에이전트의 작동 방식을 **시각화, 디버깅, 검사**할 수 있도록 도와주는 강력한 웹 기반 개발 도구입니다. 이 문서는 Studio의 주요 기능과 사용법을 안내합니다.

---

## 1. LangGraph Studio란?

LangGraph Studio는 개발자가 에이전트의 내부 상태와 흐름을 쉽게 파악하도록 돕는 UI 인터페이스입니다. 복잡한 `StateGraph`의 구조를 시각적으로 표현하고, 에이전트 실행 과정을 실시간으로 추적하여 문제 해결 및 최적화에 기여합니다.

주요 역할:
*   **시각화**: 에이전트의 노드(Node)와 엣지(Edge) 연결 관계를 다이어그램으로 표시합니다.
*   **실행 추적**: 에이전트가 각 단계를 실행할 때 어떤 노드가 활성화되고 상태(State)가 어떻게 변경되는지 실시간으로 보여줍니다.
*   **상태 검사**: 각 노드 실행 후의 전체 상태 객체와 특정 값들을 상세히 확인할 수 있습니다.
*   **디버깅 지원**: 실행 중단, 단계별 진행 등 디버깅에 유용한 기능을 제공할 수 있습니다 (기능은 Studio 버전에 따라 다를 수 있음).

---

## 2. LangGraph Studio 시작하기

로컬 환경에서 LangGraph Studio를 사용하는 가장 일반적인 방법은 `langgraph-cli` (또는 `langgraph` 패키지에 포함된 CLI)를 이용하는 것입니다.

**단계별 가이드:**

1.  **LangGraph 프로젝트 준비**:
    *   `StateGraph`를 사용하여 에이전트 로직이 정의된 Python 파일(예: `app/graph.py`)이 있어야 합니다.
    *   필요한 의존성 패키지(`langgraph`, `fastapi`, `uvicorn` 등)가 설치되어 있어야 합니다.

2.  **`langgraph.json` (또는 `pyproject.toml`) 설정 (권장)**:
    *   프로젝트 루트에 `langgraph.json` 파일을 만들어 Studio가 어떤 그래프를 로드해야 할지 알려줄 수 있습니다. (또는 `pyproject.toml` 내 `[tool.langgraph]` 섹션 사용)
    *   **`langgraph.json` 예시**:
        ```json
        {
          "graphs": [
            {
              "file": "app.graph:graph", // 모듈 경로:그래프 객체명 또는 파일 경로:객체명
              // "file": "app/graph.py:graph_instance", // 다른 예시
              "input": "app.graph:input_schema", // (선택) 입력 스키마
              "output": "app.graph:output_schema" // (선택) 출력 스키마
            }
          ],
          "dependencies": ["requirements.txt"]
        }
        ```
        *   `file`: 그래프 객체가 정의된 위치를 지정합니다. `모듈경로:객체명` 형식을 따릅니다. 예를 들어 `app/graph.py` 파일에 `my_graph`라는 이름으로 그래프가 정의되어 있다면, `app.graph:my_graph`로 지정합니다.

3.  **CLI 명령어로 Studio 실행**:
    *   프로젝트 루트 디렉터리에서 터미널을 열고 다음 명령어를 실행합니다:
        ```bash
        langgraph dev
        ```
    *   이 명령어는 다음 작업들을 수행합니다:
        *   FastAPI 애플리케이션 (또는 LangGraph 서버)을 로컬에서 실행합니다.
        *   LangGraph Studio UI를 실행하고, 웹 브라우저에서 접속 가능한 주소(예: `http://127.0.0.1:8000` 또는 다른 포트)를 터미널에 표시합니다.
        *   `langgraph.json` (또는 `pyproject.toml`) 설정을 참조하여 정의된 그래프를 Studio에 로드합니다.

4.  **웹 브라우저에서 Studio 접속**:
    *   터미널에 표시된 주소로 웹 브라우저를 열어 LangGraph Studio에 접속합니다.

---

## 3. 주요 기능 활용

LangGraph Studio에 접속하면 다음과 같은 주요 기능들을 활용할 수 있습니다:

*   **Graph View (그래프 시각화)**:
    *   정의된 `StateGraph`의 노드와 엣지, 조건부 분기 등을 시각적으로 확인할 수 있습니다.
    *   복잡한 에이전트의 전체적인 흐름을 한눈에 파악하는 데 도움이 됩니다.

*   **Trace View / Run Inspector (실행 추적)**:
    *   에이전트를 실행시키면 (예: Studio 내에서 입력값을 넣어 테스트 실행), 각 노드가 어떤 순서로 실행되는지, 어떤 데이터가 오고 갔는지 실시간으로 보여줍니다.
    *   `thread_id` 별로 실행 기록을 구분하여 볼 수 있습니다.

*   **State Inspector (상태 검사)**:
    *   각 노드가 실행된 후의 전체 상태(State) 객체의 내용을 JSON 형태로 자세히 들여다볼 수 있습니다.
    *   LLM의 출력, 도구 사용 결과, 중간 계산값 등이 상태에 어떻게 반영되는지 확인할 수 있습니다.

*   **Streaming View (스트리밍 확인)**:
    *   에이전트가 `astream_events` 등을 통해 스트리밍 방식으로 응답을 생성하는 경우, 각 이벤트 청크(chunk)나 메시지를 실시간으로 확인할 수 있습니다.

*   **Input/Output (입력 및 출력)**:
    *   Studio UI 내에서 직접 에이전트에 입력값을 제공하고 실행 결과를 확인할 수 있는 인터페이스를 제공합니다.

---

## 4. LangGraph Studio 사용의 이점

*   **직관적인 이해**: 코드만으로는 파악하기 어려운 에이전트의 복잡한 로직과 데이터 흐름을 시각적으로 쉽게 이해할 수 있습니다.
*   **빠른 디버깅**: 문제 발생 시 어느 노드에서 어떤 상태로 문제가 생겼는지 빠르게 파악하고 원인을 분석하는 데 용이합니다.
*   **효율적인 개발**: 에이전트의 동작을 실시간으로 확인하며 개발할 수 있어 개발 사이클을 단축시킬 수 있습니다.
*   **팀 협업 용이**: 에이전트의 구조와 동작을 팀원들과 공유하고 논의하기에 효과적인 도구입니다.

> LangGraph Studio는 에이전트 개발의 생산성과 안정성을 크게 향상시키는 데 도움을 줄 수 있습니다. 특히 복잡한 멀티-스텝 또는 멀티-에이전트 시스템을 구축할 때 유용합니다.
