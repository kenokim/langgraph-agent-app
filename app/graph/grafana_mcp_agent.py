import os
from typing import List, Dict, Any
from contextlib import asynccontextmanager

from langchain_core.tools import BaseTool
from langgraph.prebuilt import create_react_agent
from langchain_mcp_adapters.client import MultiServerMCPClient

GRAFANA_MCP_URL = os.getenv("GRAFANA_MCP_URL")
GRAFANA_RENDERER_MCP_URL = os.getenv("GRAFANA_RENDERER_MCP_URL")

def get_grafana_mcp_client():
    """
    Get a MultiServerMCPClient instance for Grafana MCP servers.
    """
    return MultiServerMCPClient(
            {
                "grafana_mcp_client": {
                    "url": GRAFANA_MCP_URL,
                    "transport": "sse"
                },
                                "grafana_renderer_mcp_client": {
                    "url": GRAFANA_RENDERER_MCP_URL,
                    "transport": "sse"
                }
            }
        )

@asynccontextmanager
async def make_grafana_agent(llm):
    async with get_grafana_mcp_client() as client:
        yield create_react_agent(llm, client.get_tools())
    