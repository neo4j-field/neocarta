"""Reporting and analysis for evaluation results."""

from statistics import mean, stdev
from collections import defaultdict
from typing import Any
from eval.datasets.models import EvalSample


# Configuration - adjust per project
TARGET_TOKEN_REDUCTION = 0.50  # 50% token reduction target
OBJECT_RECALL_FLOOR = 0.90     # 90% object recall minimum
MIN_ACCURACY_TOLERANCE = -0.05 # Allow semantic to be up to 5% worse than full schema
                               # (negative delta means semantic < full_schema)


def build_delta_report(samples: list[EvalSample]) -> dict[str, Any]:
    """
    Build comprehensive delta report comparing semantic vs full_schema conditions.

    Parameters
    ----------
    samples : list[EvalSample]
        Evaluated samples

    Returns
    -------
    dict
        Report with summary and per-archetype breakdowns
    """
    def safe_mean(vals):
        vals = [v for v in vals if v is not None]
        return mean(vals) if vals else None

    def safe_stdev(vals):
        vals = [v for v in vals if v is not None and not isinstance(v, bool)]
        return stdev(vals) if len(vals) > 1 else 0.0

    def get_nested(sample, condition, *keys):
        """Safely get nested value from results."""
        try:
            d = sample.results_by_condition.get(condition, {})
            for k in keys:
                if d is None:
                    return None
                d = d.get(k) if isinstance(d, dict) else None
            return d
        except:
            return None

    # Overall metrics
    sem_exec_vals = [
        get_nested(s, "semantic", "execution", "execution_match")
        for s in samples
    ]
    fs_exec_vals = [
        get_nested(s, "full_schema", "execution", "execution_match")
        for s in samples
    ]

    # Convert bools to floats for averaging
    sem_exec_vals = [1.0 if v else 0.0 for v in sem_exec_vals if v is not None]
    fs_exec_vals = [1.0 if v else 0.0 for v in fs_exec_vals if v is not None]

    sem_exec_mean = safe_mean(sem_exec_vals)
    fs_exec_mean = safe_mean(fs_exec_vals)

    # Token metrics
    token_reduction_vals = [
        get_nested(s, "semantic", "tokens", "token_reduction_pct")
        for s in samples
    ]
    token_reduction_mean = safe_mean(token_reduction_vals)

    # Retrieval metrics
    recall_vals = [s.object_recall for s in samples if s.object_recall is not None]
    precision_vals = [s.context_precision for s in samples if s.context_precision is not None]

    recall_mean = safe_mean(recall_vals)
    precision_mean = safe_mean(precision_vals)

    # Accuracy delta (semantic - full_schema)
    # Positive delta = semantic is better
    # Negative delta = semantic is worse
    sql_accuracy_delta = None
    if sem_exec_mean is not None and fs_exec_mean is not None:
        sql_accuracy_delta = sem_exec_mean - fs_exec_mean

    # Success gates
    token_reduction_meets_target = (token_reduction_mean or 0) >= TARGET_TOKEN_REDUCTION
    recall_meets_floor = (recall_mean or 0) >= OBJECT_RECALL_FLOOR

    # Semantic must be at least as good as full schema (within tolerance)
    # Success if: semantic >= full_schema - tolerance
    # Equivalent to: (semantic - full_schema) >= -tolerance
    accuracy_meets_baseline = (sql_accuracy_delta if sql_accuracy_delta is not None else -1.0) >= MIN_ACCURACY_TOLERANCE

    # Bonus: semantic outperforms full schema
    semantic_outperforms = (sql_accuracy_delta if sql_accuracy_delta is not None else -1.0) > 0

    summary = {
        "total_samples": len(samples),
        "semantic_execution_match": sem_exec_mean,
        "full_schema_execution_match": fs_exec_mean,
        "sql_accuracy_delta": sql_accuracy_delta,
        "token_reduction_pct": token_reduction_mean,
        "token_reduction_stdev": safe_stdev(token_reduction_vals),
        "object_recall_mean": recall_mean,
        "object_recall_stdev": safe_stdev(recall_vals),
        "object_precision_mean": precision_mean,
        "object_precision_stdev": safe_stdev(precision_vals),
        # Success gates
        "token_reduction_meets_target": token_reduction_meets_target,
        "recall_meets_floor": recall_meets_floor,
        "accuracy_meets_baseline": accuracy_meets_baseline,
        "semantic_outperforms": semantic_outperforms,
        "all_gates_pass": all([
            token_reduction_meets_target,
            recall_meets_floor,
            accuracy_meets_baseline,
        ]),
        # Targets (for reference)
        "target_token_reduction": TARGET_TOKEN_REDUCTION,
        "object_recall_floor": OBJECT_RECALL_FLOOR,
        "min_accuracy_tolerance": MIN_ACCURACY_TOLERANCE,
    }

    # Per-archetype breakdown
    archetypes = set(s.archetype for s in samples)
    by_archetype = {}

    for arch in archetypes:
        group = [s for s in samples if s.archetype == arch]

        sem_exec = [1.0 if get_nested(s, "semantic", "execution", "execution_match") else 0.0 for s in group]
        fs_exec = [1.0 if get_nested(s, "full_schema", "execution", "execution_match") else 0.0 for s in group]
        sem_struct = [1.0 if get_nested(s, "semantic", "structural", "structural_match") else 0.0 for s in group]
        fs_struct = [1.0 if get_nested(s, "full_schema", "structural", "structural_match") else 0.0 for s in group]

        tok_red = [get_nested(s, "semantic", "tokens", "token_reduction_pct") for s in group]
        obj_recall = [s.object_recall for s in group if s.object_recall is not None]

        # Collect hallucinations
        all_halluc_tables = []
        all_halluc_cols = []
        for s in group:
            faith = get_nested(s, "semantic", "faithfulness")
            if faith:
                all_halluc_tables.extend(faith.get("hallucinated_tables", []))
                all_halluc_cols.extend(faith.get("hallucinated_columns", []))

        by_archetype[arch] = {
            "n": len(group),
            "execution_match": {
                "semantic": safe_mean(sem_exec),
                "full_schema": safe_mean(fs_exec),
                "delta": safe_mean(sem_exec) - safe_mean(fs_exec) if sem_exec and fs_exec else None,
            },
            "structural_match": {
                "semantic": safe_mean(sem_struct),
                "full_schema": safe_mean(fs_struct),
            },
            "token_reduction_pct": safe_mean(tok_red),
            "object_recall": safe_mean(obj_recall),
            "hallucinated_tables": list(set(all_halluc_tables)),
            "hallucinated_columns": list(set(all_halluc_cols)),
        }

    return {
        "summary": summary,
        "by_archetype": by_archetype,
    }


def print_report(report: dict[str, Any]) -> None:
    """
    Print formatted evaluation report.

    Parameters
    ----------
    report : dict
        Report from build_delta_report
    """
    summary = report["summary"]

    print("\n" + "="*80)
    print("SEMANTIC LAYER EVALUATION REPORT")
    print("="*80)

    print(f"\nTotal Samples: {summary['total_samples']}")

    print("\n" + "-"*80)
    print("OVERALL METRICS")
    print("-"*80)

    print(f"\nSQL Accuracy (Execution Match):")
    print(f"  Semantic:     {summary['semantic_execution_match']:.1%}")
    print(f"  Full Schema:  {summary['full_schema_execution_match']:.1%}")
    delta = summary['sql_accuracy_delta']
    delta_str = f"{delta:+.1%}"
    if delta > 0:
        delta_str += " (semantic outperforms ✓)"
    elif delta < summary['min_accuracy_tolerance']:
        delta_str += " (below tolerance ✗)"
    else:
        delta_str += " (within tolerance)"
    print(f"  Delta:        {delta_str}")

    print(f"\nToken Efficiency:")
    print(f"  Reduction:    {summary['token_reduction_pct']:.1%} (± {summary['token_reduction_stdev']:.1%})")
    print(f"  Target:       {summary['target_token_reduction']:.1%}")

    print(f"\nRetrieval Quality:")
    print(f"  Object Recall:    {summary['object_recall_mean']:.1%} (± {summary['object_recall_stdev']:.1%})")
    print(f"  Object Precision: {summary['object_precision_mean']:.1%} (± {summary['object_precision_stdev']:.1%})")
    print(f"  Recall Floor:     {summary['object_recall_floor']:.1%}")

    print("\n" + "-"*80)
    print("SUCCESS GATES")
    print("-"*80)

    def status(passed):
        return "✓ PASS" if passed else "✗ FAIL"

    tolerance_pct = abs(summary['min_accuracy_tolerance'])
    print(f"\n  Token Reduction >= {summary['target_token_reduction']:.0%}:        {status(summary['token_reduction_meets_target'])}")
    print(f"  Object Recall >= {summary['object_recall_floor']:.0%}:            {status(summary['recall_meets_floor'])}")
    print(f"  Semantic >= Full Schema - {tolerance_pct:.0%}:  {status(summary['accuracy_meets_baseline'])}")
    if summary['semantic_outperforms']:
        print(f"  🌟 Semantic Outperforms Full Schema:   ✓ YES")
    print(f"\n  OVERALL:                                {status(summary['all_gates_pass'])}")

    print("\n" + "-"*80)
    print("BY ARCHETYPE")
    print("-"*80)

    for arch, metrics in report["by_archetype"].items():
        print(f"\n{arch.upper()} (n={metrics['n']})")
        print(f"  Execution Match:  Semantic {metrics['execution_match']['semantic']:.1%}  |  Full Schema {metrics['execution_match']['full_schema']:.1%}  |  Delta {metrics['execution_match']['delta']:+.1%}")
        print(f"  Token Reduction:  {metrics['token_reduction_pct']:.1%}")
        print(f"  Object Recall:    {metrics['object_recall']:.1%}")

        if metrics['hallucinated_tables'] or metrics['hallucinated_columns']:
            print(f"  Hallucinations:")
            if metrics['hallucinated_tables']:
                print(f"    Tables: {', '.join(metrics['hallucinated_tables'])}")
            if metrics['hallucinated_columns']:
                print(f"    Columns: {', '.join(metrics['hallucinated_columns'])}")

    print("\n" + "="*80)


def export_results_to_json(samples: list[EvalSample], output_path: str) -> None:
    """
    Export evaluation results to JSON file.

    Parameters
    ----------
    samples : list[EvalSample]
        Evaluated samples
    output_path : str
        Path to output JSON file
    """
    import json
    from pathlib import Path

    results = []
    for sample in samples:
        results.append({
            "question_id": sample.question_id,
            "archetype": sample.archetype,
            "nl_question": sample.nl_question,
            "ground_truth_sql": sample.ground_truth_sql,
            "semantic": sample.results_by_condition["semantic"],
            "full_schema": sample.results_by_condition["full_schema"],
            "context_precision": sample.context_precision,
            "context_recall": sample.context_recall,
            "object_recall": sample.object_recall,
        })

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n✓ Exported results to {output_path}")
