from langchain.agents import create_agent

from langgraph.graph.state import CompiledStateGraph
from langchain.tools import BaseTool


SYSTEM_PROMPT = """You are a Text2SQL agent and are tasked with answering 
questions about our BigQuery dataset on ecommerce. 
Always ensure that tables are qualified with project and dataset names."""

def create_text2sql_agent(mcp_tools: list[BaseTool]) -> CompiledStateGraph:
    return create_agent(
        model="openai:gpt-4o-mini",
        tools=mcp_tools,
        system_prompt=SYSTEM_PROMPT,
    )
