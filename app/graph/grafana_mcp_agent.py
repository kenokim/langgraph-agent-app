import os
from contextlib import asynccontextmanager

from langgraph.prebuilt import create_react_agent
from langchain_mcp_adapters.client import MultiServerMCPClient

from dotenv import load_dotenv

load_dotenv()

GRAFANA_MCP_URL = os.getenv("GRAFANA_MCP_URL")
GRAFANA_RENDERER_MCP_URL = os.getenv("GRAFANA_RENDERER_MCP_URL")

def get_grafana_mcp_client():
    """
    Get a MultiServerMCPClient instance for Grafana MCP servers.
    """
    return MultiServerMCPClient(
            {
                "grafana_mcp_client": {
                    "url": f"{GRAFANA_MCP_URL}/sse",
                    "transport": "sse"
                }
            }
        )

@asynccontextmanager
async def make_grafana_agent(llm):
    async with get_grafana_mcp_client() as client:
        yield create_react_agent(
            llm,
            client.get_tools(),
            ""
            )
    
def get_grafana_renderer_mcp_client():
    """
    Get a MultiServerMCPClient instance for Grafana MCP servers.
    """
    return MultiServerMCPClient(
            {
                "grafana_renderer_mcp_client": {
                    "url": f"{GRAFANA_RENDERER_MCP_URL}/sse",
                    "transport": "sse"
                }
            }
        )

@asynccontextmanager
async def make_grafana_renderer_agent(llm):
    async with get_grafana_renderer_mcp_client() as client:
        yield create_react_agent(
            llm,
            client.get_tools(),
            ""
            )