from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from langchain_core.messages import BaseMessage

# Pydantic model for BaseMessage to allow serialization
class MessageModel(BaseModel):
    type: str
    content: str
    # Add other common fields if needed, e.g., name for ToolMessage, tool_calls for AIMessage
    name: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None 
    tool_call_id: Optional[str] = None # For ToolMessage

    @classmethod
    def from_core_message(cls, message: BaseMessage) -> "MessageModel":
        # A more robust conversion might be needed depending on message types
        return cls(
            type=message.type,
            content=str(message.content),
            name=getattr(message, 'name', None),
            tool_calls=getattr(message, 'tool_calls', None),
            tool_call_id=getattr(message, 'tool_call_id', None)
        )

class InvocationRequest(BaseModel):
    input: Dict[str, Any] # Typically expects {"messages": [HumanMessage(...)]} or {"input": "user query"}
    thread_id: Optional[str] = None

class StreamRequest(InvocationRequest):
    pass

class ThreadStateResponse(BaseModel):
    thread_id: str
    values: Dict[str, Any] # The full state dictionary
    # It's better to explicitly define the structure of 'values' if known
    # For AgentState, it would be messages, input etc.
    # Example: messages: List[MessageModel]

class GraphOutput(BaseModel):
    # This will depend on what your graph's final output is.
    # If it's the full state, it's similar to ThreadStateResponse.values
    # If it's just the last message, then perhaps:
    # last_message: MessageModel
    final_state: Dict[str, Any]

class HealthResponse(BaseModel):
    status: str 