# LangGraph ReAct 에이전트 프롬프트 커스터마이징

LangGraph의 prebuilt ReAct 에이전트를 사용할 때 프롬프트를 손쉽게 커스터마이징할 수 있습니다. `create_react_agent` 함수를 호출할 때 `prompt` 파라미터를 사용하여 원하는 시스템 프롬프트를 전달하면 됩니다.

예를 들어, 특정 역할을 수행하거나 특정 방식으로 응답하도록 에이전트에게 지시하는 커스텀 프롬프트를 제공할 수 있습니다.

```python
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

# 모델 설정
llm = ChatOpenAI(model="gpt-4o")

# 커스텀 프롬프트 정의
custom_prompt_template = """너는 매우 친절하고 상세하게 답변하는 AI 비서야. 사용자의 질문에 최대한 자세하고 친절하게 답해줘.

도구 사용이 필요하면 사용 가능한 도구를 활용해서 답변을 생성해."""

# create_react_agent 호출 시 prompt 파라미터에 커스텀 프롬프트 전달
# 실제 사용 시에는 tools 리스트에 사용할 도구들을 포함해야 합니다.
# agent_executor = create_react_agent(llm, tools, prompt=ChatPromptTemplate.from_template(custom_prompt_template)) 
```

위 예시처럼 `prompt` 파라미터에 `ChatPromptTemplate.from_template()` 등으로 생성한 프롬프트 객체를 전달하여 ReAct 에이전트의 기본 행동을 변경할 수 있습니다.
