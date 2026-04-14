"""Entry point for running the Text2SQL agent with MCP server."""

import asyncio
import os

import httpx
from dotenv import load_dotenv
from google.auth import default
from google.auth.transport.requests import Request
from langchain_mcp_adapters.client import MultiServerMCPClient

from agent.agent import create_text2sql_agent

load_dotenv()


# Custom auth class for Google Cloud
class GoogleAuth(httpx.Auth):
    """Custom httpx auth handler that injects Google Cloud bearer tokens."""

    def __init__(self) -> None:
        """Initialize credentials using the application default credentials."""
        self.credentials, _ = default()

    def auth_flow(self, request):  # noqa: ANN001, ANN201
        """Refresh the token and inject it into the request."""
        self.credentials.refresh(Request())
        request.headers["Authorization"] = f"Bearer {self.credentials.token}"
        yield request


sql_metadata_graph_mcp_params = {
    "transport": "stdio",
    "command": "uv",
    "args": ["--directory", "mcp_server/", "run", "mcp-server"],
    "env": {
        "NEO4J_URI": os.getenv("NEO4J_URI"),
        "NEO4J_USERNAME": os.getenv("NEO4J_USERNAME"),
        "NEO4J_PASSWORD": os.getenv("NEO4J_PASSWORD"),
        "NEO4J_DATABASE": os.getenv("NEO4J_DATABASE"),
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "EMBEDDING_MODEL": "text-embedding-3-small",
        "EMBEDDING_DIMENSIONS": "768",
    },
}

bigquery_mcp_params = {
    "transport": "http",
    "url": "https://bigquery.googleapis.com/mcp",
    "auth": GoogleAuth(),
}

client = MultiServerMCPClient(
    {
        "sql_metadata_graph": sql_metadata_graph_mcp_params,
        "bigquery": bigquery_mcp_params,
    }
)

CONFIG = {"configurable": {"thread_id": "1"}}


# run the agent with MCP server using stdio transport
async def main() -> None:
    """Connect to MCP servers, build the agent, and run an interactive chat loop."""
    # Get tools
    mcp_tools = await client.get_tools()

    tool_names = {
        # From SQL Metadata Graph MCP Server
        "list_schemas",
        "list_tables_by_schema",
        "get_metadata_schema_by_column_semantic_similarity",
        "get_metadata_schema_by_schema_and_table_semantic_similarity",
        "get_full_metadata_schema",
        # From BigQuery MCP Server
        "execute_sql",
    }

    allowed_tools = [tool for tool in mcp_tools if tool.name in tool_names]

    agent = create_text2sql_agent(allowed_tools)

    # conversation loop
    print("\n===================================== Chat =====================================\n")

    while True:
        user_input = input("> ")  # noqa: ASYNC250
        if user_input.lower() in {"exit", "quit", "q"}:
            break

        async for chunk in agent.astream(
            {"messages": [{"role": "user", "content": user_input}]},
            stream_mode="values",
            config=CONFIG,
        ):
            # Each chunk contains the full state at that point
            latest_message = chunk["messages"][-1]
            if latest_message.content:
                print(f"Agent: {latest_message.content}")
            elif latest_message.tool_calls:
                print(f"Calling tools: {[tc['name'] for tc in latest_message.tool_calls]}")


if __name__ == "__main__":
    asyncio.run(main())
