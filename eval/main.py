"""Main entry point for running semantic layer evaluation."""

import asyncio
import os
import random
import argparse
from pathlib import Path
from dotenv import load_dotenv
from google.cloud import bigquery
from openai import AsyncOpenAI

from eval import (
    get_ecommerce_eval_samples,
    get_github_eval_samples,
    EvalRunner,
    build_delta_report,
    print_report,
    export_results_to_json,
    BigQuerySchemaRetriever,
)


async def main():
    """Run semantic layer evaluation."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Run semantic layer evaluation")
    parser.add_argument(
        "--dataset",
        type=str,
        default="ecommerce",
        choices=["ecommerce", "github"],
        help="Dataset to evaluate (default: ecommerce)",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=None,
        help="Number of samples to randomly select (default: all)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for sampling (default: 42)",
    )
    args = parser.parse_args()

    # Load environment
    load_dotenv()

    print("="*80)
    print("SEMANTIC LAYER EVALUATION")
    print("="*80)

    # Configuration
    PROJECT_ROOT = Path(__file__).parent.parent
    SEMANTIC_MCP_SERVER = str(PROJECT_ROOT / "mcp_server" / "src" / "server.py")

    # Dataset-specific schema path
    if args.dataset == "ecommerce":
        schema_filename = "demo_ecommerce_schema.json"
    elif args.dataset == "github":
        schema_filename = "github_schema.json"
    else:
        raise ValueError(f"Unknown dataset: {args.dataset}")

    FULL_SCHEMA_PATH = PROJECT_ROOT / "eval" / "datasets" / "schemas" / schema_filename

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

    # Load evaluation samples based on dataset
    print(f"\n📋 Loading evaluation samples for dataset: {args.dataset}")
    if args.dataset == "ecommerce":
        samples = get_ecommerce_eval_samples()
    elif args.dataset == "github":
        samples = get_github_eval_samples()
    else:
        raise ValueError(f"Unknown dataset: {args.dataset}")

    print(f"   Total samples available: {len(samples)}")

    # Apply sampling if requested
    if args.sample_size is not None and args.sample_size < len(samples):
        random.seed(args.seed)
        samples = random.sample(samples, args.sample_size)
        print(f"   Randomly sampled: {len(samples)} (seed={args.seed})")

    print(f"   Samples to evaluate: {len(samples)}")

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

    # Include dataset and sample size in filename
    suffix = f"_{args.dataset}"
    if args.sample_size is not None:
        suffix += f"_n{args.sample_size}"
    results_path = output_dir / f"eval_results{suffix}.json"
    export_results_to_json(results, str(results_path))
    print(f"\n💾 Results exported to {results_path}")

    # Summary
    summary = report["summary"]
    if summary["all_gates_pass"]:
        print("\n✅ All success gates passed!")
    else:
        print("\n⚠️  Some success gates failed. See report above for details.")


if __name__ == "__main__":
    asyncio.run(main())
