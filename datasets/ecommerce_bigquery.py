from google.cloud import bigquery


def load_ecommerce_dataset_to_bigquery(
    client: bigquery.Client, project_id: str, dataset_id: str
) -> None:
    """
    Load the ecommerce dataset to BigQuery.

    Parameters
    ----------
    client: bigquery.Client
        The BigQuery client.
    project_id: str
    dataset_id: str
    """

    with open("datasets/create-ecommerce-dataset.sql", "r") as f:
        sql = f.read()

    job = client.query(sql)
    job.result()


if __name__ == "__main__":
    import os

    client = bigquery.Client(project=os.getenv("BIGQUERY_PROJECT_ID"))
    load_ecommerce_dataset_to_bigquery(
        client, os.getenv("BIGQUERY_PROJECT_ID"), os.getenv("BIGQUERY_DATASET_ID")
    )
