"""Schema registry for managing persisted schema baselines."""

from pathlib import Path
import json
import sys




async def persist_bigquery_schema_from_mcp(
    project_id: str,
    dataset_id: str,
    output_path: Path | str,
) -> None:
    """
    Persist BigQuery schema to JSON using the BigQuery MCP tool.

    This creates the full_schema baseline.

    Parameters
    ----------
    project_id : str
        GCP project ID
    dataset_id : str
        BigQuery dataset ID
    output_path : Path | str
        Where to save the schema JSON file
    """
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    # Use the BigQuery MCP server
    server_params = StdioServerParameters(
        command="uvx",
        args=["mcp-server-bigquery"],
        env={
            "GCP_PROJECT_ID": project_id,
        }
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Get table info for the dataset
            result = await session.call_tool(
                "get_table_info",
                arguments={
                    "project_id": project_id,
                    "dataset_id": dataset_id,
                }
            )

            # Parse result
            schema_data = []
            for item in result.content:
                if hasattr(item, 'text'):
                    data = json.loads(item.text)
                    schema_data = data if isinstance(data, list) else [data]

            # Save to file
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w') as f:
                json.dump(schema_data, f, indent=2)

            print(f"✓ Persisted BigQuery schema to {output_path}")
            print(f"  Dataset: {project_id}.{dataset_id}")
            print(f"  Tables: {len(schema_data)}")


async def persist_graph_schema_from_mcp(
    server_script_path: str,
    output_path: Path | str,
) -> None:
    """
    Persist the full graph schema using the semantic layer MCP server.

    This captures the enriched metadata from the graph.

    Parameters
    ----------
    server_script_path : str
        Path to the semantic layer MCP server script
    output_path : Path | str
        Where to save the schema JSON file
    """
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    from mcp_server.models import TableContext

    server_params = StdioServerParameters(
        command="uv",
        args=["run", server_script_path],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Call get_full_metadata_schema
            result = await session.call_tool(
                "get_full_metadata_schema",
                arguments={}
            )

            # Parse result
            table_contexts = []
            for item in result.content:
                if hasattr(item, 'text'):
                    data = json.loads(item.text)
                    if isinstance(data, list):
                        table_contexts = [TableContext.model_validate(t) for t in data]
                    else:
                        table_contexts = [TableContext.model_validate(data)]

            # Save to file
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            schema_data = [ctx.model_dump() for ctx in table_contexts]

            with open(output_path, 'w') as f:
                json.dump(schema_data, f, indent=2)

            print(f"✓ Persisted graph schema to {output_path}")
            print(f"  Tables: {len(table_contexts)}")
            print(f"  Columns: {sum(len(t.columns) for t in table_contexts)}")


if __name__ == "__main__":
    """
    CLI for persisting schemas.

    Usage:
        python -m eval.datasets.schema_registry bigquery <project_id> <dataset_id> <output_path>
        python -m eval.datasets.schema_registry graph <server_script_path> <output_path>
    """
    import asyncio

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python -m eval.datasets.schema_registry bigquery <project_id> <dataset_id> <output_path>")
        print("  python -m eval.datasets.schema_registry graph <server_script_path> <output_path>")
        sys.exit(1)

    command = sys.argv[1]

    if command == "bigquery":
        if len(sys.argv) != 5:
            print("Usage: python -m eval.datasets.schema_registry bigquery <project_id> <dataset_id> <output_path>")
            sys.exit(1)

        project_id = sys.argv[2]
        dataset_id = sys.argv[3]
        output_path = sys.argv[4]

        asyncio.run(persist_bigquery_schema_from_mcp(project_id, dataset_id, output_path))

    elif command == "graph":
        if len(sys.argv) != 4:
            print("Usage: python -m eval.datasets.schema_registry graph <server_script_path> <output_path>")
            sys.exit(1)

        server_script_path = sys.argv[2]
        output_path = sys.argv[3]

        asyncio.run(persist_graph_schema_from_mcp(server_script_path, output_path))

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
