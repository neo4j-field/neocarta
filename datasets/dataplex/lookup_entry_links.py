"""
Test the projects.locations:lookupEntryLinks REST API endpoint.

The Python SDK (google-cloud-dataplex v2.16.0) does not yet expose this method,
so we call it directly via the REST API using Application Default Credentials.

Usage:
    python datasets/dataplex/lookup_entry_links.py

Required env vars (same as the connector):
    GCP_PROJECT_ID, GCP_PROJECT_NUMBER, DATAPLEX_LOCATION,
    BIGQUERY_DATASET_ID, BIGQUERY_LOCATION, DATAPLEX_GLOSSARY_ID
"""

import json
import os

import google.auth
import google.auth.transport.requests
import requests
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.environ["GCP_PROJECT_ID"]
PROJECT_NUMBER = os.environ["GCP_PROJECT_NUMBER"]
DATAPLEX_LOCATION = os.environ["DATAPLEX_LOCATION"]
BQ_LOCATION = os.environ.get("BIGQUERY_LOCATION", DATAPLEX_LOCATION)
DATASET_ID = os.environ["BIGQUERY_DATASET_ID"]
GLOSSARY_ID = os.environ["DATAPLEX_GLOSSARY_ID"]

DEFINITION_LINK_TYPE = "projects/dataplex-types/locations/global/entryLinkTypes/definition"
BASE_URL = "https://dataplex.googleapis.com/v1"


def get_auth_session() -> requests.Session:
    creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    session = google.auth.transport.requests.AuthorizedSession(creds)
    return session


def lookup_entry_links(
    session: requests.Session,
    entry: str,
    entry_link_types: list[str] | None = None,
    entry_mode: str | None = None,
    page_size: int = 10,
) -> list[dict]:
    """
    Call projects.locations:lookupEntryLinks and page through all results.

    Parameters
    ----------
    session : AuthorizedSession
    entry : str
        Full resource name of the entry to look up links for.
    entry_link_types : list[str] | None
        Filter by link type resource names. None returns all types.
    entry_mode : str | None
        "SOURCE", "TARGET", or None for both directions.
    page_size : int
        Results per page (max 10 per API limits).

    Returns
    -------
    List of EntryLink dicts from the API response.
    """
    url = f"{BASE_URL}/projects/{PROJECT_ID}/locations/{DATAPLEX_LOCATION}:lookupEntryLinks"

    params: dict = {"entry": entry, "pageSize": page_size}
    if entry_link_types:
        params["entryLinkTypes"] = entry_link_types
    if entry_mode:
        params["entryMode"] = entry_mode

    all_links: list[dict] = []
    while True:
        response = session.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        all_links.extend(data.get("entryLinks", []))

        next_token = data.get("nextPageToken")
        if not next_token:
            break
        params["pageToken"] = next_token

    return all_links


def glossary_term_entry_name(term_id: str) -> str:
    return (
        f"projects/{PROJECT_NUMBER}/locations/{DATAPLEX_LOCATION}"
        f"/entryGroups/@dataplex/entries/"
        f"projects/{PROJECT_NUMBER}/locations/{DATAPLEX_LOCATION}"
        f"/glossaries/{GLOSSARY_ID}/terms/{term_id}"
    )


def bq_table_entry_name(table_id: str) -> str:
    return (
        f"projects/{PROJECT_NUMBER}/locations/{BQ_LOCATION}"
        f"/entryGroups/@bigquery/entries/"
        f"bigquery.googleapis.com/projects/{PROJECT_ID}"
        f"/datasets/{DATASET_ID}/tables/{table_id}"
    )


if __name__ == "__main__":
    session = get_auth_session()

    # ------------------------------------------------------------------
    # Test 1: Look up all definition links for the whole glossary entry
    # to discover which terms are linked to columns.
    # ------------------------------------------------------------------
    print("=" * 60)
    print("Test 1: List all glossary terms in the glossary")
    print("=" * 60)

    from google.cloud import dataplex_v1

    glossary_client = dataplex_v1.BusinessGlossaryServiceClient()
    parent = f"projects/{PROJECT_ID}/locations/{DATAPLEX_LOCATION}/glossaries/{GLOSSARY_ID}"
    terms = list(glossary_client.list_glossary_terms(parent=parent))
    print(f"Found {len(terms)} terms in glossary '{GLOSSARY_ID}'")
    for term in terms[:5]:
        print(f"  - {term.name.split('/')[-1]}: {term.display_name}")
    if len(terms) > 5:
        print(f"  ... and {len(terms) - 5} more")

    # ------------------------------------------------------------------
    # Test 2: Look up definition links for the first term
    # ------------------------------------------------------------------
    if not terms:
        print("\nNo terms found — cannot run Test 2.")
    else:
        term = terms[0]
        term_id = term.name.split("/")[-1]
        term_entry = glossary_term_entry_name(term_id)

        print(f"\n{'=' * 60}")
        print(f"Test 2: lookupEntryLinks for term '{term_id}'")
        print(f"Entry: {term_entry}")
        print("=" * 60)

        links = lookup_entry_links(
            session=session,
            entry=term_entry,
            entry_link_types=[DEFINITION_LINK_TYPE],
        )

        if not links:
            print("No entry links found for this term.")
            print("(Either no columns are tagged with it, or the term entry name format is wrong.)")
        else:
            print(f"Found {len(links)} entry link(s):")
            for link in links:
                print(f"\n  Link name: {link['name']}")
                for ref in link.get("entryReferences", []):
                    mode = ref.get("type", "?")
                    path = ref.get("path", "")
                    entry_name = ref.get("name", "")
                    path_str = f" (path: {path})" if path else ""
                    print(f"    [{mode}] {entry_name}{path_str}")

    # ------------------------------------------------------------------
    # Test 3: Verify using raw JSON dump of a single link
    # ------------------------------------------------------------------
    print(f"\n{'=' * 60}")
    print("Test 3: Raw response for first term (entry_mode=TARGET)")
    print("=" * 60)

    if terms:
        term_id = terms[0].name.split("/")[-1]
        term_entry = glossary_term_entry_name(term_id)

        url = f"{BASE_URL}/projects/{PROJECT_ID}/locations/{DATAPLEX_LOCATION}:lookupEntryLinks"
        response = session.get(
            url,
            params={
                "entry": term_entry,
                "entryLinkTypes": DEFINITION_LINK_TYPE,
                "entryMode": "TARGET",
                "pageSize": 10,
            },
        )
        print(f"HTTP status: {response.status_code}")
        print(json.dumps(response.json(), indent=2))
