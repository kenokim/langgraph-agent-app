# LangGraph 에이전트 FastAPI 백엔드

이 프로젝트는 사이드 프로젝트 및 쉬운 이해를 위해 설계된 LangGraph 기반 에이전트를 서빙하기 위한 FastAPI 백엔드를 제공합니다.

## 주요 기능

-   **LangGraph 에이전트**: LLM 호출 및 사용자 정의 도구 사용을 포함하여 `StateGraph`로 구축된 핵심 로직.
-   **FastAPI 서빙**: RESTful 및 WebSocket 엔드포인트를 통해 에이전트를 노출합니다.
-   **인메모리 상태**: 세션/스레드 관리를 위해 LangGraph의 `MemorySaver`를 사용합니다 (상태는 휘발성).
-   **Vertex AI 통합**: LLM 공급자로 Google의 Vertex AI (Gemini 모델)를 사용하도록 구성되었습니다.
-   **스트리밍**: 에이전트 응답 스트리밍을 위해 SSE (Server-Sent Events) 및 WebSocket을 지원합니다.
-   **기본 엔드포인트**:
    -   에이전트 호출 (동기)
    -   에이전트 스트리밍 (SSE & WebSocket)
    -   스레드 상태 조회
    -   헬스 체크

## 프로젝트 구조

```
app/
├── main.py             # FastAPI 앱, 라우터, 미들웨어
├── api/                # API 버전 관리 및 엔드포인트
│   └── v1/
│       ├── endpoints.py    # API 라우트
│       └── schemas.py      # Pydantic 모델
├── core/               # 핵심 설정 및 구성
│   └── config.py         # 애플리케이션 설정 (예: API 키)
└── graph/              # LangGraph 에이전트 로직
    ├── instance.py       # StateGraph 정의, LLM, 도구, 메모리
    └── tools.py          # 에이전트를 위한 사용자 정의 도구
requirements.txt        # Python 의존성 파일
README.md               # 이 파일
.env.example            # 환경 변수 예시 파일 (.env 파일로 복사하여 사용)
langgraph.json          # LangGraph Studio 설정
```

## 설정 방법

1.  **리포지토리 클론 (해당하는 경우)**

2.  **가상 환경 생성 (권장)**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # Windows: venv\Scripts\activate
    ```

3.  **의존성 설치**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **환경 변수 설정**:
    `.env.example` 파일을 `.env`라는 새 파일로 복사하고 필요한 값을 채웁니다.
    ```bash
    cp .env.example .env
    ```
    **`.env.example` / `.env` 파일 내용:**
    ```env
    # Vertex AI용 Google Cloud 프로젝트 ID
    # GOOGLE_CLOUD_PROJECT="your-gcp-project-id"

    # 선택 사항: Vertex AI에 특정 서비스 계정을 사용하는 경우, 
    # 시스템 환경에 GOOGLE_APPLICATION_CREDENTIALS 환경 변수가 설정되어 있는지 확인하세요.
    # 이는 보통 `gcloud auth application-default login` 명령으로 처리됩니다.
    # GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account-key.json"
    ```
    **Vertex AI 중요 사항**: Google Cloud에 인증되었는지 확인하세요. 일반적으로 다음 명령을 실행하여 인증할 수 있습니다:
    ```bash
    gcloud auth application-default login
    ```
    Vertex AI에 대한 특정 프로젝트 및 위치가 있는 경우 `.env` 파일 또는 시스템 환경에 `GOOGLE_CLOUD_PROJECT` 및 `GOOGLE_CLOUD_LOCATION`을 설정할 수 있으며, 이는 `app/core/config.py`에서 사용됩니다.

## 애플리케이션 실행

Uvicorn을 사용하여 FastAPI 애플리케이션을 실행합니다:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

-   `--reload`: 코드 변경 시 자동 리로딩을 활성화합니다 (개발에 유용).
-   애플리케이션은 `http://localhost:8000`에서 사용할 수 있습니다.
-   API 문서 (Swagger UI)는 `http://localhost:8000/docs`에서 확인할 수 있습니다.
-   대안 API 문서 (ReDoc)는 `http://localhost:8000/redoc`에서 확인할 수 있습니다.

## API 엔드포인트 개요

모든 엔드포인트는 `/api/v1` 접두사를 가집니다.

-   `POST /invocations`: 에이전트를 동기적으로 호출합니다.
    -   **요청 본문**: `{"input": {"input": "사용자 질문"}, "thread_id": "선택적_uuid"}`
    -   `input` 객체 내의 `input` 필드: 이 값은 그래프에 초기 `HumanMessage`로 전달되며 `state.input`도 채웁니다.
-   `POST /stream`: SSE (Server-Sent Events)를 사용하여 에이전트 응답을 스트리밍합니다.
    -   **요청 본문**: `/invocations`와 동일.
-   `WS /ws/stream`: WebSocket을 사용하여 에이전트 응답을 스트리밍합니다.
    -   **클라이언트 전송 JSON**: `{"input": {"input": "사용자 질문"}, "thread_id": "선택적_uuid"}`
-   `GET /threads/{thread_id}/state`: 지정된 스레드의 현재 상태를 가져옵니다.
-   `POST /threads/{thread_id}/interrupt`: (플레이스홀더) 스레드에 인터럽트 신호를 보내거나 명령을 전송하는 엔드포인트입니다.
-   `GET /health`: 서비스 헬스 체크.

## LangGraph Studio

LangGraph Studio로 그래프를 시각화하고 디버깅하려면:

1.  `langgraph-cli`가 설치되어 있는지 확인합니다 (`langgraph`와 함께 제공됨).
2.  CLI가 그래프를 찾을 수 있도록 `langgraph.json` 파일이 필요하거나 `pyproject.toml`을 구성해야 할 수 있습니다. `langgraph.json` 예시:
    ```json
    {
      "graphs": [
        {
          "file": "app.graph.instance:app_graph",
          "input": "app.api.v1.schemas:InvocationRequest", // 예시, 필요에 따라 조정
          "output": "app.api.v1.schemas:GraphOutput"      // 예시, 필요에 따라 조정
        }
      ]
    }
    ```
3.  LangGraph CLI를 사용하여 개발 서버를 실행합니다:
    ```bash
    langgraph dev
    ```
    이 명령은 일반적으로 FastAPI 앱과 LangGraph Studio UI를 시작하며, 종종 다른 포트에서 실행되거나 동일한 포트의 다른 경로를 통해 접근할 수 있습니다.
