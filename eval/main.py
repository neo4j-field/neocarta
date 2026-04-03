"""Main entry point for running semantic layer evaluation."""

import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from google.cloud import bigquery
from openai import AsyncOpenAI

from eval import (
    get_ecommerce_eval_samples,
    EvalRunner,
    build_delta_report,
    print_report,
    export_results_to_json,
    BigQuerySchemaRetriever,
)


async def main():
    """Run semantic layer evaluation."""
    # Load environment
    load_dotenv()

    print("="*80)
    print("SEMANTIC LAYER EVALUATION")
    print("="*80)

    # Configuration
    PROJECT_ROOT = Path(__file__).parent.parent
    SEMANTIC_MCP_SERVER = "mcp-server"
    FULL_SCHEMA_PATH = PROJECT_ROOT / "eval" / "datasets" / "schemas" / "demo_ecommerce_schema.json"

    # Persist schema if it doesn't exist
    if not FULL_SCHEMA_PATH.exists():
        print(f"\n📥 Schema file not found. Persisting from MCP server...")
        print(f"   Source: {SEMANTIC_MCP_SERVER}")
        print(f"   Target: {FULL_SCHEMA_PATH}")

        from eval.datasets.schema_registry import persist_graph_schema_from_mcp
        await persist_graph_schema_from_mcp(SEMANTIC_MCP_SERVER, FULL_SCHEMA_PATH)
        print(f"   ✓ Schema persisted successfully")

    # Initialize clients
    bq_client = bigquery.Client(project=os.getenv("GCP_PROJECT_ID"))
    llm_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Load schema baseline
    print(f"\n📁 Loading schema baseline from {FULL_SCHEMA_PATH}")
    full_schema_retriever = BigQuerySchemaRetriever(FULL_SCHEMA_PATH)
    print(f"   Tables: {full_schema_retriever.get_num_tables()}")
    print(f"   Columns: {full_schema_retriever.get_num_columns()}")

    # Load evaluation samples
    print("\n📋 Loading evaluation samples...")
    samples = get_ecommerce_eval_samples()
    print(f"   Total samples: {len(samples)}")

    # Count by archetype
    from collections import Counter
    archetypes = Counter(s.archetype for s in samples)
    print("   Distribution:")
    for arch, count in archetypes.items():
        print(f"     - {arch}: {count}")

    # Initialize runner
    print(f"\n🚀 Initializing evaluation runner...")
    print(f"   MCP Server: {SEMANTIC_MCP_SERVER}")
    print(f"   LLM Model: gpt-4o")

    runner = EvalRunner(
        semantic_mcp_server_path=SEMANTIC_MCP_SERVER,
        full_schema_retriever=full_schema_retriever,
        bq_client=bq_client,
        llm_client=llm_client,
        llm="gpt-4o",
        dialect="bigquery",
    )

    # Run evaluation
    print("\n" + "="*80)
    print("RUNNING EVALUATION")
    print("="*80)

    results = await runner.run_eval(samples)

    # Build report
    print("\n" + "="*80)
    print("BUILDING REPORT")
    print("="*80)

    report = build_delta_report(results)
    print_report(report)

    # Export results
    output_dir = PROJECT_ROOT / "eval" / "results"
    output_dir.mkdir(exist_ok=True)

    results_path = output_dir / "eval_results.json"
    export_results_to_json(results, str(results_path))

    # Summary
    summary = report["summary"]
    if summary["all_gates_pass"]:
        print("\n✅ All success gates passed!")
    else:
        print("\n⚠️  Some success gates failed. See report above for details.")


if __name__ == "__main__":
    asyncio.run(main())
