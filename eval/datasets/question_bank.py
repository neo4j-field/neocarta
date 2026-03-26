"""Question bank with evaluation samples for the ecommerce dataset."""

import yaml
import hashlib
from pathlib import Path
from eval.datasets.models import EvalSample
from eval.sql_parser import extract_required_objects


def _generate_question_id(nl_question: str, ground_truth_sql: str) -> str:
    """
    Generate a deterministic question ID from question text and SQL.

    Uses SHA256 hash to ensure uniqueness across thousands of samples.
    """
    content = f"{nl_question.strip()}\n{ground_truth_sql.strip()}"
    return hashlib.sha256(content.encode()).hexdigest()


def _load_samples_from_yaml(yaml_filename: str) -> list[EvalSample]:
    """
    Load evaluation samples from a YAML configuration file.

    Parameters
    ----------
    yaml_filename : str
        Name of the YAML file in the datasets directory

    Returns
    -------
    list[EvalSample]
        List of evaluation samples loaded from YAML
    """
    # Load YAML config
    config_path = Path(__file__).parent / yaml_filename
    with open(config_path) as f:
        config = yaml.safe_load(f)

    # Convert YAML to EvalSample objects
    samples = []
    for sample_data in config["samples"]:
        nl_question = sample_data["nl_question"]
        ground_truth_sql = sample_data["ground_truth_sql"].strip()

        # Auto-generate question ID from content hash
        question_id = _generate_question_id(nl_question, ground_truth_sql)

        # Auto-extract required objects from ground truth SQL
        required_objects = extract_required_objects(ground_truth_sql)

        sample = EvalSample(
            question_id=question_id,
            archetype=sample_data["archetype"],
            nl_question=nl_question,
            ground_truth_sql=ground_truth_sql,
            required_objects=required_objects,
        )
        samples.append(sample)

    return samples


def get_ecommerce_eval_samples() -> list[EvalSample]:
    """
    Load evaluation samples from YAML configuration.

    Based on the demo_ecommerce dataset with tables:
    - customers (customer_id, customer_name, email, created_at)
    - products (product_id, product_name, category, price)
    - orders (order_id, customer_id, order_date, total_amount)
    - order_items (order_item_id, order_id, product_id, quantity, price)

    Returns
    -------
    list[EvalSample]
        List of evaluation samples loaded from ecommerce_samples.yaml
    """
    return _load_samples_from_yaml("ecommerce_samples.yaml")


def get_github_eval_samples() -> list[EvalSample]:
    """
    Load evaluation samples from YAML configuration.

    Based on the GitHub dataset with tables:
    - sample_repo (repo_name, watch_count, fork, has_wiki, created_at, ...)
    - languages (repo_name, language, bytes)
    - licenses (repo_name, license.name, license.key, license.url)
    - sample_commits (commit, repo_name, subject, message, author.name, author.email, author.date, ...)
    - sample_files (repo_name, path, name, commit)

    Returns
    -------
    list[EvalSample]
        List of evaluation samples loaded from github_samples.yaml
    """
    return _load_samples_from_yaml("github_samples.yaml")


if __name__ == "__main__":
    """Print summary of evaluation samples."""
    samples = get_ecommerce_eval_samples()

    print(f"Total samples: {len(samples)}\n")

    # Count by archetype
    from collections import Counter
    archetypes = Counter(s.archetype for s in samples)

    print("Distribution by archetype:")
    for archetype, count in archetypes.items():
        print(f"  {archetype}: {count}")

    print("\n" + "="*60)
    print("Sample questions:")
    print("="*60)

    for sample in samples:
        print(f"\n[{sample.question_id}] {sample.archetype}")
        print(f"Q: {sample.nl_question}")
        print(f"Tables: {', '.join(sorted(sample.required_objects['tables']))}")
        print(f"Columns: {', '.join(sorted(sample.required_objects['columns']))}")
