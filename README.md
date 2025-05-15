# LangGraph Agent FastAPI Backend

This project provides a FastAPI backend for serving a LangGraph-based agent, designed for side projects and easy understanding.

## Features

-   **LangGraph Agent**: Core logic built with `StateGraph` including LLM calls and custom tool usage.
-   **FastAPI Serving**: Exposes the agent via RESTful and WebSocket endpoints.
-   **In-Memory State**: Uses LangGraph's `MemorySaver` for session/thread management (state is volatile).
-   **Vertex AI Integration**: Configured to use Google's Vertex AI (Gemini models) as the LLM provider.
-   **Streaming**: Supports Server-Sent Events (SSE) and WebSockets for streaming agent responses.
-   **Basic Endpoints**:
    -   Invoke agent (synchronous)
    -   Stream agent (SSE & WebSocket)
    -   Get thread state
    -   Health check

## Project Structure

```
app/
├── main.py             # FastAPI app, router, middleware
├── api/                # API versioning and endpoints
│   └── v1/
│       ├── endpoints.py    # API routes
│       └── schemas.py      # Pydantic models
├── core/               # Core settings and configurations
│   └── config.py         # Application settings (e.g., API keys)
└── graph/              # LangGraph agent logic
    ├── instance.py       # StateGraph definition, LLM, tools, memory
    └── tools.py          # Custom tools for the agent
requirements.txt        # Python dependencies
README.md               # This file
.env.example            # Example environment variables (copy to .env)
```

## Setup

1.  **Clone the repository (if applicable)**

2.  **Create a virtual environment (recommended)**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up Environment Variables**:
    Copy `.env.example` to a new file named `.env` and fill in the necessary values.
    ```bash
    cp .env.example .env
    ```
    **Contents of `.env.example` / `.env`:**
    ```env
    # Google Cloud Project ID for Vertex AI
    # GOOGLE_CLOUD_PROJECT="your-gcp-project-id"

    # Optional: If using specific service accounts for Vertex AI, 
    # ensure GOOGLE_APPLICATION_CREDENTIALS environment variable is set in your system environment.
    # This is often handled by `gcloud auth application-default login`.
    # GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account-key.json"
    ```
    **Important for Vertex AI**: Ensure you have authenticated with Google Cloud. You can typically do this by running:
    ```bash
    gcloud auth application-default login
    ```
    If you have a specific project and location for Vertex AI, you can set `GOOGLE_CLOUD_PROJECT` and `GOOGLE_CLOUD_LOCATION` in your `.env` file or system environment, and they will be picked up by `app/core/config.py`.

## Running the Application

Use Uvicorn to run the FastAPI application:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

-   `--reload`: Enables auto-reloading when code changes (useful for development).
-   The application will be available at `http://localhost:8000`.
-   API documentation (Swagger UI) will be at `http://localhost:8000/docs`.
-   Alternative API documentation (ReDoc) will be at `http://localhost:8000/redoc`.

## API Endpoints Overview

All endpoints are prefixed with `/api/v1`.

-   `POST /invocations`: Synchronously invoke the agent.
    -   **Request Body**: `{"input": {"input": "Your query"}, "thread_id": "optional_uuid"}`
    -   `input` within `input`: This is passed to the graph as initial `HumanMessage` and also populates `state.input`.
-   `POST /stream`: Stream agent responses using Server-Sent Events (SSE).
    -   **Request Body**: Same as `/invocations`.
-   `WS /ws/stream`: Stream agent responses using WebSockets.
    -   **Client sends JSON**: `{"input": {"input": "Your query"}, "thread_id": "optional_uuid"}`
-   `GET /threads/{thread_id}/state`: Get the current state of a given thread.
-   `POST /threads/{thread_id}/interrupt`: (Placeholder) Endpoint to signal an interrupt or send a command to a thread.
-   `GET /health`: Health check for the service.

## LangGraph Studio

To visualize and debug your graph with LangGraph Studio:

1.  Ensure `langgraph-cli` is installed (it comes with `langgraph`).
2.  You might need a `langgraph.json` or configure `pyproject.toml` for the CLI to discover your graph. Example `langgraph.json`:
    ```json
    {
      "graphs": [
        {
          "file": "app.graph.instance:app_graph",
          "input": "app.api.v1.schemas:InvocationRequest", // Example, adjust if needed
          "output": "app.api.v1.schemas:GraphOutput"      // Example, adjust if needed
        }
      ]
    }
    ```
3.  Run the development server using the LangGraph CLI:
    ```bash
    langgraph dev
    ```
    This will typically start your FastAPI app and the LangGraph Studio UI, often on different ports or accessible via the same port with different paths.
