from langgraph.prebuilt import create_react_agent

def make_server_info_agent(llm):
    return create_react_agent(
        name="server_info_agent",
        model=llm,
        tools=[],
        prompt=(
            "너는 서버 정보를 알려주는 에이전트야. 서버 정보에 대해 물어보면, 서버 정보는 'abasdwqdasd231123' 라고 알려줘."
        )
    )
