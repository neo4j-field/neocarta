"""BigQuery dataset creation scripts."""

import argparse
import os
from pathlib import Path

from dotenv import load_dotenv
from google.cloud import bigquery


def load_ecommerce_dataset_to_bigquery(client: bigquery.Client) -> None:
    """
    Load the ecommerce dataset to BigQuery.

    Parameters
    ----------
    client: bigquery.Client
        The BigQuery client.
    """
    with Path("datasets/create-ecommerce-dataset.sql").open() as f:
        sql = f.read()

    job = client.query(sql)
    job.result()


def load_acme_dataset_to_bigquery(client: bigquery.Client) -> None:
    """
    Load the acme dataset to BigQuery.

    Parameters
    ----------
    client: bigquery.Client
        The BigQuery client.
    """
    with Path("datasets/acme-dataset.sql").open() as f:
        sql = f.read()

    job = client.query(sql)
    job.result()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load a dataset into BigQuery.")
    parser.add_argument(
        "--dataset",
        choices=["ecommerce", "acme"],
        required=True,
        help="Dataset to load: 'ecommerce' or 'acme'",
    )
    args = parser.parse_args()

    load_dotenv()
    client = bigquery.Client(project=os.getenv("GCP_PROJECT_ID"))

    match args.dataset.lower().strip():
        case "ecommerce":
            load_ecommerce_dataset_to_bigquery(client)
        case "acme":
            load_acme_dataset_to_bigquery(client)
        case _:
            raise ValueError(f"Invalid dataset argument: {args.dataset}")
