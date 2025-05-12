# LangGraph 애플리케이션 프로젝트 구조 설계

> 이 문서는 **FastAPI**로 서빙되는 LangGraph 애플리케이션의 기본 디렉터리/파일 구조와 필수 의존 패키지를 제안합니다. 실제 사용 목적(챗봇, 워크플로 자동화, RAG 등)에 맞게 일부 디렉터리/파일은 추가·변경할 수 있습니다.

---

## 1. 최상위 디렉터리 트리(예시)

```
my-langgraph-app/
├── app/                    # ✨ FastAPI & LangGraph 코드
│   ├── __init__.py
│   ├── main.py             # FastAPI 진입점 (Uvicorn 실행 대상)
│   ├── graph.py            # 최초(또는 루트) LangGraph 정의
│   ├── subgraphs/          # 재사용 가능한 서브그래프 모음
│   │   └── __init__.py
│   ├── memory.py           # 커스텀 메모리/스토어 구현(Optional)
│   ├── callbacks.py        # 로깅/모니터링 콜백
│   └── schemas.py          # pydantic 모델 정의
│
├── langgraph.json          # 📁 LangGraph 플랫폼/CLI 설정
├── requirements.txt        # Python 의존성 명세
├── README.md               # 사용법, 아키텍처 설명
├── .env                    # 환경 변수 (API 키 등)
├── Dockerfile              # 컨테이너 배포(Optional)
├── tests/                  # pytest 테스트 모음
│   └── test_graph.py
└── docs/                   # 문서 (이 디렉터리)
    ├── langgraph_components.md
    └── project_structure.md
```

### 핵심 포인트
1. **app/** 폴더는 FastAPI & LangGraph 코드만 포함하고, 비즈니스 로직과 인프라(배포) 코드를 분리합니다.
2. **langgraph.json** 파일은 CLI/서버 배포·그래프 메타데이터·환경 변수 매핑 등을 정의합니다.
3. 테스트는 **pytest** 기반으로 `tests/` 디렉터리에 배치해 그래프 동작을 검증합니다.

---

## 2. 주요 파일 상세

| 파일 | 설명 |
| --- | --- |
| `app/main.py` | FastAPI 객체 생성, 라우터 등록, LangGraph 그래프를 주입하고 REST/WS 엔드포인트 구현. |
| `app/graph.py` | `StateGraph` 또는 Functional API(@entrypoint)로 작성된 루트 그래프 정의. 필요 시 그래프 컴파일 후 export. |
| `app/subgraphs/` | 복잡한 시스템에서 재사용할 모듈형 서브그래프를 보관. |
| `app/memory.py` | 커스텀 `InMemoryStore`, `VectorStoreMemory` 등 장·단기 메모리 구현. |
| `app/callbacks.py` | LangSmith, OpenTelemetry, 프롬프트/토큰 로깅 등을 위한 콜백. |
| `app/schemas.py` | 입력·출력 스키마를 **pydantic** 모델로 정의하여 API 문서 자동화 및 타입 안전성 확보. |
| `langgraph.json` | 예시:
|  | ```json
|  | {
|  |   "graphs": [
|  |     {
|  |       "file": "app/graph.py",
|  |       "export": "graph"
|  |     }
|  |   ],
|  |   "dependencies": ["requirements.txt"],
|  |   "env_file": ".env"
|  | }
|  | ``` |
| `requirements.txt` | 의존 패키지 버전 고정. 아래 3절 참조. |
| `Dockerfile` | 서버 배포용 컨테이너 이미지 정의(Optional). |
| `.env` | `GEMINI_API_KEY`, DB 접속 정보 등 민감 값 저장(버전 관리 제외). |
| `tests/` | `pytest` / `asyncio` 기반 유닛·통합 테스트. 그래프 로직, API 응답, 상태 업데이트 검증. |

---

## 3. 필수/권장 Python 패키지

`scripts/requirements.txt` (예시)
```
# --- Core ---
langgraph>=0.1.0          # 그래프 라이브러리
fastapi>=0.110.0          # ASGI 프레임워크
uvicorn[standard]>=0.27.0 # ASGI 서버

# --- LLM Provider ---
google-generativeai>=0.3.0 # Gemini(Generative AI) SDK
langchain-google-vertexai>=0.0.2 # LangChain ↔ Gemini 래퍼(선택)

# --- Data / Memory ---
faiss-cpu>=1.8            # RAG용 Vector DB (Optional)
redis>=5.0.0              # LangGraph Server 백엔드 or 캐시(Optional)

# --- Utilities ---
pydantic>=2.6.0           # 데이터 검증 / 스키마
python-dotenv>=1.0.0      # .env 로드
httpx>=0.27.0             # 비동기 HTTP 호출
loguru>=0.7.0             # 로깅 편의성(Optional)

# --- Dev / Test ---
pytest>=8.0.0             # 테스트
pytest-asyncio>=0.23.0    # async 테스트 지원

# --- Observability ---
langsmith>=0.1.22          # 관측성(Log/Trace) 플랫폼

``` 
※ 모델·DB·VectorStore에 따라 추가 패키지를 조정하세요 (e.g., `psycopg2-binary`, `motor`, `qdrant-client`).

---

## 4. FastAPI & LangGraph 통합 패턴

1. **그래프 싱글턴**: `app.main` 모듈에서 그래프 인스턴스를 전역으로 생성해 재사용(Cold Start 비용 최소화).
2. **스트리밍**: `StreamingResponse` + `graph.stream(state)` 사용. WebSocket 로드가 높으면 **Server-Sent Events(SSE)** 권장.
3. **중단점**: 휴먼-인-더-루프가 필요한 노드에서는 `interrupt()` → 클라이언트 저장 → 승인 시 `Command` 전송.
4. **메모리 공유**: `InMemoryStore` 또는 `VectorStoreMemory`를 DI(Dependency Injection) 방식으로 그래프에 주입.

---

## 5. 배포 & 운영 시 고려 사항

1. **로컬 개발**: `langgraph dev` ↔ LangGraph Studio 연결을 통해 그래프 시각화/디버깅.
2. **테스트**: CI 파이프라인에서 `pytest -q` 실행, 그래프 경로 커버리지 확보.
3. **컨테이너**: `Dockerfile`에 `pip install -r requirements.txt` → `uvicorn app.main:app --host 0.0.0.0 --port 8000` CMD.
4. **LangGraph Platform**: 
   - 배포 타입: Development(싱글 컨테이너) / Production(오토스케일)
   - Auto-Scaling, Cron, Webhook, Assistants, Monitoring 등을 원클릭 활성화.
5. **관측성**: **LangSmith**(LLM 트레이스·토큰 소비·오류 분석), Prometheus, OpenTelemetry, Loguru 등을 조합해 모니터링.

---

## 6. 시작 명령어 (Makefile 예시)

```Makefile
.PHONY: dev test lint

dev:
	uvicorn app.main:app --reload --port 8000

test:
	pytest -q

lint:
	ruff check app tests
```

---

## 7. 다음 단계

1. **docs/langgraph_components.md** 내용을 참고해 노드·메모리·스트리밍 구성을 결정.
2. 유즈케이스별 **subgraphs/** 디렉터리에 기능 모듈화 → 재사용성 향상.
3. 필요하면 `scripts/` 폴더를 만들어 데이터 마이그레이션·백필 작업 스크립트를 관리.

> 위 구조는 베스트 프랙티스에 기반한 템플릿이며, 팀의 코드 스타일·CI/CD·클라우드 환경에 맞춰 자유롭게 수정하세요.
