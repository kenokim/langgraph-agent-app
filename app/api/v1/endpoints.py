import asyncio
import json
import uuid
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Body
from fastapi.responses import StreamingResponse
from typing import Dict, Any, AsyncGenerator
from starlette.websockets import WebSocketState

from langchain_core.messages import HumanMessage

from app.graph import app_graph
from .schemas import (
    InvocationRequest,
    StreamRequest,
    ThreadStateResponse,
    GraphOutput,
    HealthResponse,
    MessageModel
)

router = APIRouter()

def _get_thread_id(request_thread_id: str | None) -> str:
    return request_thread_id or str(uuid.uuid4())

def _prepare_graph_input(api_input: Dict[str, Any]) -> Dict[str, Any]:
    if "messages" in api_input:
        return api_input
    elif "input" in api_input and isinstance(api_input["input"], str):
        return {"messages": [HumanMessage(content=api_input["input"])], "input": api_input["input"]}
    elif "input" in api_input: # if input is not a string but some other dict.
        input_str = str(api_input["input"])
        return {"messages": [HumanMessage(content=input_str)], "input": input_str}
    raise HTTPException(status_code=400, detail="Invalid input. Must contain 'messages' or 'input' field.")


@router.post("/invocations", response_model=GraphOutput)
async def invoke_agent(request: InvocationRequest):
    thread_id = _get_thread_id(request.thread_id)
    config = {"configurable": {"thread_id": thread_id}}
    graph_input = _prepare_graph_input(request.input)
    try:
        result = await app_graph.ainvoke(graph_input, config=config)
        return GraphOutput(final_state=result)
    except Exception as e:
        print(f"Error during agent invocation for thread {thread_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stream") # SSE Streaming
async def stream_agent_sse(request: StreamRequest):
    thread_id = _get_thread_id(request.thread_id)
    config = {"configurable": {"thread_id": thread_id}}
    graph_input = _prepare_graph_input(request.input)

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            async for event in app_graph.astream_events(graph_input, config=config, version="v1"):
                yield f"event: {event['event']}\ndata: {json.dumps(event['data'])}\n\n"
                await asyncio.sleep(0.01)
        except Exception as e:
            print(f"Error during SSE streaming for thread {thread_id}: {e}")
            error_event = {"event": "error", "data": {"detail": str(e)}}
            yield f"event: {error_event['event']}\ndata: {json.dumps(error_event['data'])}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.websocket("/ws/stream")
async def websocket_stream_agent(websocket: WebSocket):
    await websocket.accept()
    ws_thread_id: str | None = None

    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            
            api_input = payload.get("input", {})
            request_thread_id = payload.get("thread_id")

            if ws_thread_id is None:
                ws_thread_id = _get_thread_id(request_thread_id)
            elif request_thread_id and request_thread_id != ws_thread_id:
                await websocket.send_json({"event": "error", "data": {"detail": "Thread ID cannot be changed mid-session."}})
                continue
            
            current_config = {"configurable": {"thread_id": ws_thread_id}}
            graph_input = _prepare_graph_input(api_input)

            async for event in app_graph.astream_events(graph_input, config=current_config, version="v1"):
                await websocket.send_json(event)

    except WebSocketDisconnect:
        print(f"WebSocket disconnected for thread_id: {ws_thread_id}")
    except Exception as e:
        print(f"WebSocket error for thread_id: {ws_thread_id}: {e}")
        if websocket.client_state == WebSocketState.CONNECTED:
            await websocket.send_json({"event": "error", "data": {"detail": str(e)}})
    finally:
        if websocket.client_state == WebSocketState.CONNECTED:
             await websocket.close()

@router.get("/threads/{thread_id_path}/state", response_model=ThreadStateResponse)
async def get_thread_state(thread_id_path: str):
    config = {"configurable": {"thread_id": thread_id_path}}
    try:
        graph_state = await app_graph.aget_state(config)
        if graph_state is None:
             raise HTTPException(status_code=404, detail=f"Thread '{thread_id_path}' not found.")
        return ThreadStateResponse(thread_id=thread_id_path, values=graph_state.values)
    except Exception as e:
        print(f"Error getting state for thread {thread_id_path}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/threads/{thread_id_path}/interrupt")
async def interrupt_thread(thread_id_path: str, command_data: Dict[str, Any] = Body(...)):
    print(f"Received interrupt for thread_id: {thread_id_path} with command: {command_data}")
    return {"thread_id": thread_id_path, "status": "interrupt_received", "detail": "Interrupt handling is a placeholder."}

@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="ok") 