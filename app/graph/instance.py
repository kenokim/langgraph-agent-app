import operator
from typing import TypedDict, Annotated, Sequence, List, Dict, Any

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_google_vertexai import ChatVertexAI
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode

from .tools import custom_tools
from ..core.config import settings

# 1. Define Agent State
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    input: str
    # If you want to track raw tool outputs separately
    # tool_outputs: List[Dict[str, Any]] | None 

# 2. Initialize LLM and Tools
# Ensure GOOGLE_APPLICATION_CREDENTIALS is set in your environment for Vertex AI
# or gcloud auth application-default login has been run.
llm = ChatVertexAI(
    model_name="gemini-pro", # Or another Gemini model
    project=settings.google_cloud_project,
    location=settings.google_cloud_location,
    # streaming=True, # Enable if you want streaming from LLM
    convert_system_message_to_human=True # Gemini API typically doesn't use system messages directly
)

tool_node = ToolNode(custom_tools)

# 3. Define Graph Nodes

def call_model(state: AgentState):
    """Invokes the LLM with the current state messages."""
    messages = state["messages"]
    # The Gemini API works best if the last message is from a human user for a turn.
    # If the last message is an AIMessage with tool_calls, that's fine for the ToolNode.
    # If the last message is a ToolMessage, the LLM needs to process it.
    
    response = llm.invoke(messages)
    # We return a list, because this will get added to the existing list
    return {"messages": [response]}

# 4. Define Conditional Edge Logic
def should_continue(state: AgentState) -> str:
    """Determines whether to continue to tools or end."""
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return END

# 5. Define the Graph
workflow = StateGraph(AgentState)

workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)

workflow.set_entry_point("agent")

workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "tools": "tools",
        END: END,
    },
)

workflow.add_edge("tools", "agent")

# 6. Compile the graph with MemorySaver
# MemorySaver provides an in-memory checkpointer
memory_saver = MemorySaver()

app_graph = workflow.compile(checkpointer=memory_saver) 