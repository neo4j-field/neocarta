"""Data models for evaluation samples."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class EvalSample:
    """
    Evaluation sample containing a question, ground truth, and results.

    This is the core data structure for the evaluation pipeline.
    """

    # Identity
    question_id: str
    archetype: str  # simple_lookup, implicit_join, business_term, etc.
    nl_question: str

    # Ground truth - gold SQL authored by engineers
    ground_truth_sql: str
    required_objects: dict[str, set[str]]  # {tables: set, columns: set, joins: set}

    # Per-condition results (populated at eval time)
    results_by_condition: dict[str, dict[str, Any]] = field(default_factory=lambda: {
        "semantic": {
            "retrieved_contexts": None,  # list[TableContext]
            "generated_sql": None,       # str
            "sql_parse": None,           # dict from sqlglot
            "structural": None,          # dict from score_structural_equivalence
            "execution": None,           # dict from score_execution_accuracy
            "tokens": None,              # dict from ContextTokenMeasurement
            "faithfulness": None,        # dict from score_schema_faithfulness
            "latency_ms": None,          # float - total time
            "mcp_latency_ms": None,      # float - MCP tool call time
            "llm_latency_ms": None,      # float - LLM inference time
            "llm": None,                 # str - model used
        },
        "full_schema": {
            "generated_sql": None,
            "sql_parse": None,
            "structural": None,
            "execution": None,
            "tokens": None,
            "latency_ms": None,          # float - total time
            "llm_latency_ms": None,      # float - LLM inference time
            "llm": None,                 # str - model used
        },
    })

    # Retrieval scores (semantic condition only)
    context_precision: float | None = None
    context_recall: float | None = None
    object_recall: float | None = None

    def __post_init__(self):
        """Validate archetype."""
        valid_archetypes = {
            "simple_lookup",
            "implicit_join",
            "business_term",
            "ambiguous_column",
            "cross_domain",
            "negative_space",
        }
        if self.archetype not in valid_archetypes:
            raise ValueError(
                f"Invalid archetype: {self.archetype}. "
                f"Must be one of {valid_archetypes}"
            )


# Archetype definitions for reference
ARCHETYPES = {
    "simple_lookup": "Single table, no joins",
    "implicit_join": "Requires schema graph traversal (joins)",
    "business_term": "Requires semantic annotation/business terms",
    "ambiguous_column": "Tests disambiguation logic (multiple columns with similar names)",
    "cross_domain": "Multiple subject areas/schemas",
    "negative_space": "MCP should NOT over-retrieve (irrelevant question)",
}
