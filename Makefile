.PHONY: help agent create-graph clean

help:
	@echo "Available commands:"
	@echo "  make load-ecommerce-dataset .. Load the ecommerce dataset into BigQuery"
	@echo "  make agent ................... Run the Text2SQL agent"
	@echo "  make create-graph ............ Extract BigQuery metadata and load into Neo4j with embeddings"
	@echo "  make clean ................... Remove Python cache files and temporary directories"
	@echo "  make fmt ..................... Format the code with Ruff"
	@echo "  make lint .................... Lint the code with Ruff"

agent:
	uv run run_agent.py

create-graph:
	uv run run_create_graph.py

load-ecommerce-dataset:
	uv run datasets/ecommerce_bigquery.py

fmt:
	uvx ruff format .

lint:
	uvx ruff check .

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
