from agent.agent import create_text2sql_agent
from mcp.client.stdio import stdio_client
import asyncio
from dotenv import load_dotenv
import os
from mcp import StdioServerParameters
from langchain_mcp_adapters.tools import load_mcp_tools
from mcp import ClientSession

load_dotenv()

mcp_params = StdioServerParameters(
    command="uv",
    args=["run", "mcp_server/src/server.py"],
    env={
        "NEO4J_URI": os.getenv("NEO4J_URI"),
        "NEO4J_USERNAME": os.getenv("NEO4J_USERNAME"),
        "NEO4J_PASSWORD": os.getenv("NEO4J_PASSWORD"),
        "NEO4J_DATABASE": os.getenv("NEO4J_DATABASE"),
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "EMBEDDING_MODEL": "text-embedding-3-small",
        "EMBEDDING_DIMENSIONS": "768",
    },
)

CONFIG = {"configurable": {"thread_id": "1"}}


# run the agent with MCP server using stdio transport
async def main():
    async with stdio_client(mcp_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()

            # Get tools
            mcp_tools = await load_mcp_tools(session)

            agent = create_text2sql_agent(mcp_tools)

            # conversation loop
            print(
                "\n===================================== Chat =====================================\n"
            )

            while True:
                user_input = input("> ")
                if user_input.lower() in {"exit", "quit", "q"}:
                    break

                # await print_astream(
                #     agent.astream({"messages": user_input}, config=CONFIG, stream_mode="updates")
                # )

                async for chunk in agent.astream({
                    "messages": [{"role": "user", "content": user_input}]
                }, stream_mode="values", config=CONFIG):
                    # Each chunk contains the full state at that point
                    latest_message = chunk["messages"][-1]
                    if latest_message.content:
                        print(f"Agent: {latest_message.content}")
                    elif latest_message.tool_calls:
                        print(f"Calling tools: {[tc['name'] for tc in latest_message.tool_calls]}")

if __name__ == "__main__":
    asyncio.run(main())