"""
Link BigQuery table columns to Dataplex Universal Catalog glossary terms
using the google-cloud-dataplex Python client.
"""

import uuid

from google.cloud import dataplex_v1


# ---------------------------------------------------------------------------
# Step 1: Find your BigQuery table entry
# ---------------------------------------------------------------------------
def find_bq_table_entry(
    project_id: str,
    dataset_id: str,
    table_id: str,
) -> dataplex_v1.SearchEntriesResult:
    """Search for a BigQuery table entry in Dataplex Universal Catalog."""
    with dataplex_v1.CatalogServiceClient() as client:
        request = dataplex_v1.SearchEntriesRequest(
            name=f"projects/{project_id}/locations/global",
            query=f"{dataset_id} {table_id}",
        )
        for result in client.search_entries(request=request):
            fqn = result.dataplex_entry.fully_qualified_name
            if fqn == f"bigquery:{project_id}.{dataset_id}.{table_id}":
                return result.dataplex_entry
    raise ValueError(f"Entry not found for {project_id}.{dataset_id}.{table_id}")


# ---------------------------------------------------------------------------
# Step 2: Find your glossary term entry
# ---------------------------------------------------------------------------
def find_glossary_term_entry(
    project_id: str,
    glossary_id: str,
    term_id: str,
    glossary_location: str = "us",
) -> str:
    """
    Search for a glossary term entry name.
    Alternatively, you can construct it directly if you know the format.
    """
    with dataplex_v1.CatalogServiceClient() as client:
        request = dataplex_v1.SearchEntriesRequest(
            name=f"projects/{project_id}/locations/global",
            query=f"{term_id}",
        )
        for result in client.search_entries(request=request):
            entry_type = result.dataplex_entry.entry_type
            if "glossary-term" in entry_type:
                print(f"Found term: {result.dataplex_entry.name}")
                return result.dataplex_entry.name

    raise ValueError(f"Glossary term '{term_id}' not found")


# ---------------------------------------------------------------------------
# Step 3: Create the entry link (column <-> glossary term)
# ---------------------------------------------------------------------------
def link_column_to_glossary_term(
    project_number: str,
    bq_location: str,
    table_entry_name: str,
    column_path: str,
    glossary_term_entry_name: str,
    entry_link_id: str | None = None,
) -> dataplex_v1.EntryLink:
    """
    Creates a 'definition' entry link between a glossary term and a
    BigQuery table column.

    Parameters
    ----------
    project_number: str
        Your GCP project NUMBER (numeric).
    bq_location: str
        Location of the @bigquery entry group (e.g. "us").
    table_entry_name: str
        Full entry name for the BigQuery table, e.g.
        "projects/<PROJECT_NUMBER>/locations/us/entryGroups/@bigquery/entries/bigquery.googleapis.com/projects/<PROJECT_ID>/datasets/<DATASET_ID>/tables/<TABLE_ID>"
    column_path: str
        The column name in the table schema (e.g. "user_id").
    glossary_term_entry_name: str
        Full entry name for the glossary term, e.g.
        "projects/<PROJECT_NUMBER>/locations/us/entryGroups/@dataplex/entries/projects/<PROJECT_NUMBER>/locations/us/glossaries/<GLOSSARY_ID>/terms/<TERM_ID>"
    entry_link_id: str | None
        Optional custom ID. If not provided, a UUID is generated.
    """
    if entry_link_id is None:
        entry_link_id = f"el-{uuid.uuid4().hex[:12]}"

    with dataplex_v1.CatalogServiceClient() as client:
        # The entry link is created in the @bigquery entry group
        parent = f"projects/{project_number}/locations/{bq_location}/entryGroups/@bigquery"

        entry_link = dataplex_v1.EntryLink(
            entry_link_type="projects/dataplex-types/locations/global/entryLinkTypes/definition",
            entry_references=[
                dataplex_v1.EntryLink.EntryReference(
                    name=glossary_term_entry_name,
                    type_=dataplex_v1.EntryLink.EntryReference.Type.TARGET,
                ),
                dataplex_v1.EntryLink.EntryReference(
                    name=table_entry_name,
                    path=f"Schema.{column_path}",  # targets a specific column
                    type_=dataplex_v1.EntryLink.EntryReference.Type.SOURCE,
                ),
            ],
        )

        request = dataplex_v1.CreateEntryLinkRequest(
            parent=parent,
            entry_link=entry_link,
            entry_link_id=entry_link_id,
        )

        return client.create_entry_link(request=request)


# ---------------------------------------------------------------------------
# Example usage
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import os

    from dotenv import load_dotenv

    load_dotenv()

    PROJECT_ID = os.getenv("GCP_PROJECT_ID")
    PROJECT_NUMBER = os.getenv("GCP_PROJECT_NUMBER")
    DATASET_ID = os.getenv("BIGQUERY_DATASET_ID")
    BQ_LOCATION = os.getenv("BIGQUERY_LOCATION")

    GLOSSARY_LOCATION = os.getenv("DATAPLEX_LOCATION")
    GLOSSARY_ID = os.getenv("DATAPLEX_GLOSSARY_ID")

    config = {
        # "customers": {
        #     "customer_id": "customer-id",
        # },
        "products": {
            "product_id": "product-id",
        },
        "orders": {
            "order_id": "order-id",
            "customer_id": "customer-id",
        },
        "order_items": {
            "order_item_id": "order-item-id",
            "order_id": "order-id",
            "product_id": "product-id",
        },
    }

    for table_id, columns in config.items():
        # --- Step 1: Find your table entry ---
        table_entry = find_bq_table_entry(
            project_id=PROJECT_ID,
            dataset_id=DATASET_ID,
            table_id=table_id,
        )
        print(f"Table entry: {table_entry.name}")

        for col_name, term_id in columns.items():
            term_entry_name = (
                f"projects/{PROJECT_NUMBER}/locations/{GLOSSARY_LOCATION}/"
                f"entryGroups/@dataplex/entries/"
                f"projects/{PROJECT_NUMBER}/locations/{GLOSSARY_LOCATION}/"
                f"glossaries/{GLOSSARY_ID}/terms/{term_id}"
            )
            link = link_column_to_glossary_term(
                project_number=PROJECT_NUMBER,
                bq_location=BQ_LOCATION,
                table_entry_name=table_entry.name,
                column_path=col_name,
                glossary_term_entry_name=term_entry_name,
            )
            print(f"Linked column '{col_name}' -> term '{term_id}': {link.name}")
