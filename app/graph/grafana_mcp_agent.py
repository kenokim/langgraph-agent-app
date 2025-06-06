import os

from langgraph.prebuilt import create_react_agent
from langchain_mcp_adapters.client import MultiServerMCPClient

from dotenv import load_dotenv

load_dotenv()

GRAFANA_MCP_URL = os.getenv("GRAFANA_MCP_URL")

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

def make_grafana_agent(llm):
    return create_react_agent(
        name="grafana_agent",
        model=llm,
        tools=get_grafana_mcp_client().get_tools(),
        prompt=(
            ""
        )
    )
