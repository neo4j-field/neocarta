.PHONY: help agent create-graph create-graph-no-embeddings clean

help:
	@echo "Available commands:"
	@echo "  make install ................. Install all dependencies"
	@echo "  make install-metadata-graph .. Install dependencies for the metadata graph"
	@echo "  make install-mcp-server ...... Install dependencies for the mcp server"
	@echo "  make install-agent ........... Install dependencies for the agent"
	@echo "  .............................."
	@echo "  make load-ecommerce-dataset .. Load the ecommerce dataset into BigQuery"
	@echo "  make agent ................... Run the Text2SQL agent"
	@echo "  make create-graph ............ Extract BigQuery metadata and load into Neo4j with embeddings"
	@echo "  make create-graph-no-embeddings  Extract BigQuery metadata (skip embeddings)"
	@echo "  .............................."
	@echo "  make clean ................... Remove Python cache files and temporary directories"
	@echo "  make fmt ..................... Format the code with Ruff"
	@echo "  make lint .................... Lint the code with Ruff"

agent:
	uv run run_agent.py

create-graph:
	uv run run_create_graph.py

create-graph-no-embeddings:
	uv run run_create_graph.py --skip-embeddings

load-ecommerce-dataset:
	uv run datasets/ecommerce_bigquery.py

fmt:
	uvx ruff format .

lint:
	uvx ruff check .

install:
	uv sync --all-groups

install-metadata-graph:
	uv sync --group metadata-graph

install-mcp-server:
	uv sync --group mcp-server

install-agent:
	uv sync --group agent

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
