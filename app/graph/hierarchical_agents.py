import operator
import os
from typing import TypedDict, Annotated, Sequence, Literal

from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.tools import tool # Changed from commented out
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import create_react_agent # Added import

from langchain_google_genai import ChatGoogleGenerativeAI

from .grafana_mcp_agent import make_grafana_agent

load_dotenv()

# 1. 에이전트 상태 정의
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    input: str
    next_agent: Literal["grafana", "renderer", "END"]


# 2. LLM 초기화
llm = ChatGoogleGenerativeAI(
    model=os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash-latest"),
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0,
    convert_system_message_to_human=True
)

# --- Tools for Orchestrator ReAct Agent ---
@tool
async def delegate_to_grafana_agent(user_query: str) -> str:
    """Use this to delegate tasks or queries specifically related to Grafana,
    such as data lookups, dashboard interactions, or alert status.
    The user_query should be the original user's request or the relevant part of it."""
    return f"Decision: Delegate to Grafana Agent for query: {user_query}"

@tool
async def delegate_to_renderer_agent(user_query: str) -> str:
    """Use this to delegate tasks related to rendering Grafana panels or dashboards
    as images, PDFs, or other visual outputs.
    The user_query should be the original user's request or the relevant part of it."""
    return f"Decision: Delegate to Renderer Agent for query: {user_query}"

orchestrator_react_tools = [delegate_to_grafana_agent, delegate_to_renderer_agent]

# --- Create Orchestrator ReAct Agent Runnable (once at module level) ---
# A system prompt can be beneficial to guide the orchestrator's behavior.
orchestrator_system_prompt = """You are an orchestrator agent. Your primary role is to analyze the user's request and decide the best course of action.
You have the following options:
1. If the query is about Grafana data, dashboards, or alerts, use the 'delegate_to_grafana_agent' tool.
2. If the query is about rendering Grafana visuals (images, PDFs), use the 'delegate_to_renderer_agent' tool.
3. If the query is general or you can answer it directly, respond without using any tools.
Ensure you pass the original user query or its relevant part to the 'user_query' argument of the tools when delegating."""

# Note: The 'messages_modifier' or a 'prompt' argument in create_react_agent can be used for system prompts.
# For simplicity, if create_react_agent doesn't directly take a system prompt string,
# one would typically ensure the first message in the `messages` list passed to its invoke is a SystemMessage.
# However, create_react_agent is often used with ChatPromptTemplate.
# Let's assume for now that it can be passed via a prompt argument or that the llm + tools are smart enough.
# If `create_react_agent` doesn't accept a simple system message string, we would typically
# prepend a SystemMessage to the `messages` list before calling `orchestrator_runnable.ainvoke`.
# For now, we'll try creating it simply. A more robust way is to use a ChatPromptTemplate.
orchestrator_runnable = create_react_agent(
    llm,
    orchestrator_react_tools,
    # Example of how a system prompt might be integrated if modifying messages directly:
    # messages_modifier=orchestrator_system_prompt # This is a hypothetical param; check create_react_agent docs
    # A common way is to construct a ChatPromptTemplate and pass it to `create_react_agent`
    # For now, we rely on the LLM's ability to use tool descriptions.
    # If needed, we can make a custom prompt and combine it.
)


# --- 하위 에이전트(Grafana, Renderer) 노드 ---
async def sub_agent_node(
    state: AgentState,
    agent_id: str,
    agent_creation_func: callable,
    agent_specific_config: dict | None = None
):
    print(f"--- Executing Sub-Agent: {agent_id} ---")
    # Pass the entire message history to the sub-agent for full context.
    input_for_sub_agent = {"messages": state["messages"]}

    async with agent_creation_func(llm, agent_specific_config) as agent_runnable:
        response_dict = await agent_runnable.ainvoke(input_for_sub_agent)

    new_ai_messages = response_dict.get("messages", [])
    if not isinstance(new_ai_messages, list) or not all(isinstance(m, BaseMessage) for m in new_ai_messages):
        print(f"Warning: {agent_id} returned unexpected format: {new_ai_messages}")
        content_to_add = f"[{agent_id} Error] Unexpected response format."
        if isinstance(new_ai_messages, dict) and "content" in new_ai_messages:
            content_to_add = str(new_ai_messages.get("content", content_to_add))
        elif isinstance(new_ai_messages, str):
            content_to_add = new_ai_messages
        final_new_messages = [AIMessage(content=content_to_add)]
    else:
        final_new_messages = new_ai_messages
        
    updated_messages = list(state["messages"]) + final_new_messages
    return {"messages": updated_messages, "next_agent": "END"}


async def grafana_node(state: AgentState):
    return await sub_agent_node(state, "Grafana Agent", make_grafana_agent)


async def renderer_node(state: AgentState):
    return await sub_agent_node(state, "Renderer Agent", make_grafana_agent)


# --- Orchestrator ReAct 에이전트 노드 ---
async def orchestrator_node(state: AgentState):
    print("--- Executing ReAct Orchestrator ---")

    # Prepend system message if not handled by create_react_agent's prompt argument
    # This ensures the orchestrator LLM knows its role.
    current_messages = state["messages"]
    # A common pattern is to ensure the first message is a system prompt if the agent expects it.
    # For this example, we'll rely on the `create_react_agent` to be configured with a prompt
    # that includes system instructions, or that the LLM infers role from tool descriptions.
    # If using a system prompt directly, it would be:
    # system_message = SystemMessage(content=orchestrator_system_prompt)
    # agent_input = {"messages": [system_message] + current_messages}
    # However, create_react_agent usually encapsulates the prompt logic.
    
    agent_input = {"messages": current_messages}
    
    # orchestrator_runnable is defined at the module level
    orchestrator_output_dict = await orchestrator_runnable.ainvoke(agent_input)

    updated_messages = orchestrator_output_dict.get("messages", current_messages)
    next_node_decision = "END" 

    if updated_messages and isinstance(updated_messages[-1], AIMessage):
        last_ai_message = updated_messages[-1]
        if last_ai_message.tool_calls:
            called_tool_name = last_ai_message.tool_calls[0].name
            print(f"Orchestrator ReAct agent called tool: {called_tool_name}")
            if called_tool_name == delegate_to_grafana_agent.__name__:
                next_node_decision = "grafana"
            elif called_tool_name == delegate_to_renderer_agent.__name__:
                next_node_decision = "renderer"
            else:
                print(f"Warning: Orchestrator called unknown tool: {called_tool_name}")
                next_node_decision = "END" # Fallback
        else:
            print("Orchestrator ReAct agent answered directly.")
            next_node_decision = "END"
    else:
        print("Warning: Orchestrator output did not end with an AIMessage or was not in expected format.")
        updated_messages = list(current_messages) + [AIMessage(content="[Orchestrator Error] Could not process the request.")]
        next_node_decision = "END"
        
    return {"messages": updated_messages, "next_agent": next_node_decision}


# --- 조건부 엣지: Orchestrator 이후 라우팅 ---
def route_after_orchestrator(state: AgentState) -> str:
    decision = state.get("next_agent")
    print(f"--- Routing after Orchestrator, next_agent: {decision} ---")
    if decision == "grafana":
        return "grafana_node"
    elif decision == "renderer":
        return "renderer_node"
    else:
        return END


# --- 그래프 구성 ---
workflow = StateGraph(AgentState)
workflow.add_node("orchestrator", orchestrator_node)
workflow.add_node("grafana_node", grafana_node)
workflow.add_node("renderer_node", renderer_node)
workflow.set_entry_point("orchestrator")
workflow.add_conditional_edges(
    "orchestrator",
    route_after_orchestrator,
    {
        "grafana_node": "grafana_node",
        "renderer_node": "renderer_node",
        END: END,
    },
)
workflow.add_edge("grafana_node", END)
workflow.add_edge("renderer_node", END)

memory = MemorySaver()
app_graph = workflow.compile(checkpointer=memory)

print("Hierarchical ReAct-based agent graph (Orchestrator, Grafana, Renderer) compiled successfully into 'app_graph'.")

# Test code (commented out)
# async def run_graph_hierarchical(user_input: str, thread_id: str):
#     config = {"configurable": {"thread_id": thread_id}}
#     initial_messages = [HumanMessage(content=user_input)]
#     # input field in AgentState is for the initial user query, if needed elsewhere.
#     # messages field will accumulate the conversation.
#     current_state_input = {"messages": initial_messages, "input": user_input} 
#
#     print(f"\n--- Running graph for input: '{user_input}' (Thread: {thread_id}) ---")
#     async for event in app_graph.astream(current_state_input, config=config):
#         print(f"\n--- Event ---")
#         for node_name, output_data in event.items():
#             print(f"Output from node '{node_name}':")
#             if isinstance(output_data, dict) and "messages" in output_data:
#                 print("  Messages:")
#                 for msg in output_data["messages"][-3:]: # Print last 3 messages for brevity
#                     print(f"    - {msg.type.upper()}: {msg.content[:200]}...") # Truncate long messages
#                     if hasattr(msg, 'tool_calls') and msg.tool_calls:
#                         print(f"      Tool Calls: {msg.tool_calls}")
#                 if "next_agent" in output_data:
#                      print(f"  Next agent decided: {output_data['next_agent']}")
#             else:
#                 print(f"  Raw output: {output_data}")
#     print("\n--- End of run ---")
#
# if __name__ == "__main__":
#     import asyncio
#     asyncio.run(run_graph_hierarchical("Grafana에서 지난 1시간 CPU 사용량 보여줘", "thread-react-grafana"))
#     # asyncio.run(run_graph_hierarchical("CPU 사용량 패널을 이미지로 만들어줘", "thread-react-renderer"))
#     # asyncio.run(run_graph_hierarchical("오늘 날씨 어때?", "thread-react-general")) 