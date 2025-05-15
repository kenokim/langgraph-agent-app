from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import router as api_v1_router

app = FastAPI(
    title="LangGraph Agent API",
    version="0.1.0",
    description="API for serving a LangGraph agent."
)

# CORS Middleware (optional, useful for web frontends on different origins)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for simplicity, adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1_router, prefix="/api/v1")

@app.get("/")
async def read_root():
    return {"message": "Welcome to the LangGraph Agent API. Visit /docs for API documentation."}

# If you want to run this directly using `python app/main.py` for simple testing (though uvicorn is better)
# import uvicorn
# if __name__ == "__main__":
# uvicorn.run(app, host="0.0.0.0", port=8000) 