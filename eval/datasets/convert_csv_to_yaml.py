#!/usr/bin/env python3
"""Convert github_eval_set.csv to github_samples.yaml."""

import csv
import yaml
import re
from pathlib import Path


def map_category_to_archetype(category: str, difficulty: str) -> str:
    """
    Map CSV category to archetype.

    Mapping:
    - aggregation/filter (single table) -> simple_lookup
    - join/multi_join -> implicit_join
    - nested_struct -> simple_lookup (with complex column access)
    - business_language -> business_term
    """
    category_map = {
        "aggregation": "simple_lookup",
        "filter": "simple_lookup",
        "join": "implicit_join",
        "multi_join": "implicit_join",
        "nested_struct": "simple_lookup",
        "business_language": "business_term",
    }
    return category_map.get(category, "simple_lookup")


def clean_sql(sql: str) -> str:
    """
    Remove project prefix from table names.

    Converts `ai-field-alex-g.github.table_name` to `github.table_name`
    """
    # Replace the full project.dataset.table pattern with just dataset.table
    sql = re.sub(r'`ai-field-alex-g\.github\.', r'`github.', sql)
    return sql.strip()


def convert_csv_to_yaml(csv_path: Path, yaml_path: Path) -> None:
    """Convert CSV to YAML format."""

    # Read CSV
    samples = []
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            archetype = map_category_to_archetype(row['category'], row['difficulty'])

            sample = {
                'archetype': archetype,
                'difficulty': row['difficulty'],
                'nl_question': row['question'],
                'ground_truth_sql': clean_sql(row['expected_sql']),
            }
            samples.append(sample)

    # Create YAML structure
    yaml_data = {
        'samples': samples
    }

    # Write YAML with proper formatting
    with open(yaml_path, 'w') as f:
        # Write header comments
        f.write("# Evaluation samples for the GitHub dataset\n")
        f.write("# Each sample tests the semantic layer's ability to retrieve relevant schema\n")
        f.write("# and generate correct SQL queries\n")
        f.write("#\n")
        f.write("# Notes:\n")
        f.write("# - question_id: auto-generated from hash of nl_question + ground_truth_sql\n")
        f.write("# - required_objects: auto-extracted from ground_truth_sql using sqlglot\n")
        f.write("#\n")
        f.write("# Archetype mapping from categories:\n")
        f.write("#   - aggregation/filter (single table) -> simple_lookup\n")
        f.write("#   - join/multi_join -> implicit_join\n")
        f.write("#   - nested_struct -> simple_lookup (with complex column access)\n")
        f.write("#   - business_language -> business_term\n\n")

        # Write YAML data with literal style for SQL
        yaml.dump(
            yaml_data,
            f,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
            width=120,
        )

    print(f"✓ Converted {len(samples)} samples from CSV to YAML")
    print(f"  Input:  {csv_path}")
    print(f"  Output: {yaml_path}")


if __name__ == "__main__":
    datasets_dir = Path(__file__).parent
    csv_path = datasets_dir / "github_eval_set.csv"
    yaml_path = datasets_dir / "github_samples.yaml"

    convert_csv_to_yaml(csv_path, yaml_path)
