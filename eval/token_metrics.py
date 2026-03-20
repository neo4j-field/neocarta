"""Token counting utilities for measuring context efficiency."""

import tiktoken
from typing import Any


class ContextTokenMeasurement:
    """
    Measure token counts for semantic layer vs full schema context.

    Uses the LLM provider's tokenizer (tiktoken for OpenAI-compatible models).
    """

    def __init__(self, model: str = "gpt-4o"):
        """
        Initialize token counter.

        Parameters
        ----------
        model : str
            Model name for tokenizer (default: gpt-4o)
        """
        try:
            self.enc = tiktoken.encoding_for_model(model)
        except KeyError:
            # Fallback to cl100k_base encoding (GPT-4, GPT-3.5-turbo)
            self.enc = tiktoken.get_encoding("cl100k_base")

    def measure(
        self,
        mcp_chunks: list[str],
        full_schema_str: str,
        few_shot_examples: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Measure token counts for both conditions.

        Parameters
        ----------
        mcp_chunks : list[str]
            Semantic layer MCP chunks
        full_schema_str : str
            Full BigQuery schema as JSON string
        few_shot_examples : list[str], optional
            Few-shot examples (if used in prompt)

        Returns
        -------
        dict
            Token measurements:
            - mcp_schema_tokens: tokens in MCP chunks only
            - full_schema_tokens: tokens in full schema only
            - few_shot_tokens: tokens in few-shot examples
            - mcp_total_context_tokens: MCP + few-shot
            - full_schema_total_tokens: full schema + few-shot
            - token_reduction_absolute: absolute reduction
            - token_reduction_pct: percentage reduction (0.0 to 1.0)
        """
        mcp_tokens = sum(len(self.enc.encode(c)) for c in mcp_chunks)
        full_schema_tokens = len(self.enc.encode(full_schema_str))
        fewshot_tokens = sum(len(self.enc.encode(e)) for e in (few_shot_examples or []))

        token_reduction_absolute = full_schema_tokens - mcp_tokens
        token_reduction_pct = 1 - (mcp_tokens / max(full_schema_tokens, 1))

        return {
            "mcp_schema_tokens": mcp_tokens,
            "full_schema_tokens": full_schema_tokens,
            "few_shot_tokens": fewshot_tokens,
            "mcp_total_context_tokens": mcp_tokens + fewshot_tokens,
            "full_schema_total_tokens": full_schema_tokens + fewshot_tokens,
            "token_reduction_absolute": token_reduction_absolute,
            "token_reduction_pct": token_reduction_pct,
        }

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in a text string.

        Parameters
        ----------
        text : str
            Text to count tokens for

        Returns
        -------
        int
            Number of tokens
        """
        return len(self.enc.encode(text))
