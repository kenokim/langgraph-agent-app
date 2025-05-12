# MCP 기반 ReAct 에이전트 시나리오 충족 전략

> MCP 서버에서 제공하는 다양한 **도구(Tool)** 를 **LangGraph**의 **프리빌트 ReAct 에이전트**에 연결했을 때, 복잡한 사용자 시나리오(검색→정리→계산 등)를 **정확·효율**적으로 해결하기 위한 전략을 정리합니다.

---

## 1. 시나리오 정의 & 목표 분해

1. **시나리오 명세**: 사용자 목표(예: "서울→파리 1주 여행 예산 플래너")를 구체적 단계로 서술
2. **작업 단위(Task) 식별**: 정보 검색, 환율 계산, 일정 최적화 등 세부 태스크 추출
3. **도구 매핑**: 각 태스크 ↔ MCP Tool 매핑

> _TIP: 시나리오 → 태스크 → Tool 매핑 테이블을 미리 작성하면 에이전트가 올바른 Tools를 호출하도록 안내하기 쉽습니다._

---

## 2. 전략별 구현 패턴

### 2.1 명시적 Tool 프라이밍

* **시스템 메시지**에 태스크별 필수·선택 도구를 명시
* 예)
  ```text
  When you need to translate currencies, you MUST call the `currency_converter` tool.
  ```
* ✅ 장점: 예측 가능성이 높고 오용 방지
* ⚠️ 단점: 툴 추가 시 프롬프트 동시 수정 필요

### 2.2 지식 기반 Tool 라우팅(ReRank)

* **Tool 메타데이터**(name, description)에 Embedding 생성 → Vector DB 저장
* 사용자 쿼리 임베딩 vs Tool 임베딩 유사도 기반 **Top-k Tool 후보** 결정
* ReAct 에이전트 시스템 메시지에 `available_tools` 변수를 동적으로 주입
* ✅ 장점: 유연·확장 / 신규 툴 자동 반영
* ⚠️ 단점: Vector DB 추가 비용·인프라 필요

### 2.3 Supervisor + Worker 조합

* **Supervisor ReAct 에이전트**가 시나리오를 분석해 하위 Worker에게 **Command** 로 할당
* Worker들은 MCP 도구를 직접 호출해 결과 반환 → Supervisor가 종합
* `fan-out / fan-in` 패턴 + `parallel_tool_calls=True` 로 속도 최적화

### 2.4 맵-리듀스(Map-Reduce) 브랜칭

* 대규모 리스트(예: 100개 도시) 처리 시 `map` 단계에서 **병렬**로 MCP 도구 호출
* `reduce` 단계에서 결과 집계
* LangGraph `send.MapReduce` or `branching` how-to 참고

### 2.5 히스토리 기반 Tool 선택(Memory)

* 과거 동일/유사 질문 → 어떤 Tool 콜이 성공적이었는지 **Memory** 에 저장
* 새 요청 시 히스토리 조회 → 우선순위 재조정
* `VectorStoreMemory` + LangGraph Checkpointer 활용

### 2.6 인간 검증 루프(HITL)

* **risk_level 높은 Tool**(예: 비용 청구, 이메일 발송) 호출 전 `interrupt()`
* 프론트엔드에서 툴 파라미터·예상 결과 확인 → `Command` 로 승인/수정

---

## 3. 품질·안정성 강화 기법

| 항목 | 기법 | LangGraph 기능 |
| --- | --- | --- |
| **오류 복구** | 재시도 정책, 대안 Tool 사용 | `node retry`, `fallback edges` |
| **보안** | Input validation, Output guardrail | `pydantic` schema, `tool call review` |
| **성능** | 동시성, 캐싱 | `parallel`, Redis cache |
| **관측성** | LangSmith 트레이스, Token 비용 추적 | `langsmith` 통합 |

---

## 4. 예시: 여행 예산 플래너 시나리오

1. 사용자 입력: "내년 5월 서울→파리 7일 여행, 항공+숙소+관광 예산 알려줘"
2. Supervisor가 태스크 분해 →
   * 항공편 검색 (`flight_search` MCP)
   * 호텔 검색 (`hotel_search` MCP)
   * 환율 변환 (`currency_converter` MCP)
3. 각 Worker가 병렬 실행, 결과 반환
4. Supervisor가 결과 합산, 총 예산 계산 → 최종 메시지 반환

---

## 5. 체크리스트

- [ ] 시나리오 → 태스크 → Tool 매핑 문서화
- [ ] Tool description에 **명확한 입력/출력** 명시
- [ ] `langsmith` 대시보드에서 Tool 호출 추적
- [ ] 실패율 높은 Tool에 **백업 Tool/재시도** 설정
- [ ] 신규 Tool 추가 시 자동 Embedding 인덱싱

> 위 기법들을 조합하여 MCP 도구를 활용한 ReAct 에이전트가 복잡한 사용자 시나리오를 높은 정확도와 안정성으로 해결하도록 설계하세요.

---

## 6. RAG 기반 시나리오 ↔ 도구 매핑 전략

> 시나리오별 도구 사용 지식을 **벡터 DB** 에 저장하고, 에이전트 실행 시 동적으로 검색·주입하는 **Retrieval-Augmented Generation** 패턴입니다.

### 6.1 데이터 모델링
```jsonc
{
  "scenario": "해외 여행 예산 플래너",
  "tasks": [
    { "intent": "항공권 검색", "tool": "flight_search", "example": "서울→파리 2025-05-10~17" },
    { "intent": "환율 계산", "tool": "currency_converter", "example": "EUR→KRW" }
  ],
  "workflow_tips": "When total budget exceeds $3000, suggest hostels instead of hotels."
}
```
1. 각 문서(시나리오) → Embedding 생성 후 VectorStore(Faiss, PGVector 등)에 저장
2. **tool name** / **intent** / **tips** 를 메타데이터로 함께 저장해 필터링 용이하게 구성

### 6.2 LangGraph 예시 파이프라인
```text
User ➜ Retriever Node ➜ Prompt Builder ➜ ReAct Agent ➜ MCP Tools
                    ▲
              VectorStore
```
1. **Retriever**: 사용자 질문 임베딩 → 시나리오 Top-k 조회
2. **Prompt Builder**: 조회된 문서에서
   * 사용해야 할 툴 목록(`available_tools`)
   * 태스크별 예시·가이드라인
   을 추출해 system/assistant 메시지로 구성
3. **ReAct Agent**: 동적으로 주입된 정보 기반 MCP Tool 호출

### 6.3 구현 팁
| 주제 | 방법 |
| --- | --- |
| Retriever | `ContextualCompressionRetriever` 로 요약 압축 가능 |
| Re-Ranking | LLM 평가로 2차 순위 조정 → 정확도 향상 |
| Metadata Filter | `score_threshold` + 실패율/성공률 메타데이터 활용 |
| Memory 연계 | Checkpointer + `VectorStoreMemory` 로 과거 성공 툴 기록 재사용 |

### 6.4 장점 & 주의점
* **장점**
  * 시나리오/툴 추가 시 "문서 + 임베딩" 만 갱신 → 코드 수정 최소화
  * 길어진 프롬프트 대신 필요한 정보만 선별 제공 → 컨텍스트 절약
* **주의**
  * 벡터 검색 Precision 이 낮으면 부적절한 툴 추천 위험 → 메타데이터 필터·LLM 검증 필요
  * 시나리오별 태스크가 많을 경우 prompt 길이 관리 필요

> RAG 패턴을 적용하면 시나리오가 증가해도 ReAct 에이전트는 항상 최신 Tool 워크플로 지식을 가져와 실행할 수 있습니다.
