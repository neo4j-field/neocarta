#!/bin/bash

# Setup script for GCP Dataplex
# This script will:
# 1. Enable Dataplex API
# 2. Create a Dataplex Lake
# 3. Create a Zone
# 4. Attach BigQuery dataset to Dataplex

set -e

# Load environment variables
source .env

PROJECT_ID=${BIGQUERY_PROJECT_ID}
DATASET_ID=${BIGQUERY_DATASET_ID}
LOCATION="us-central1"  # Change if needed
LAKE_ID="ecommerce-lake"
ZONE_ID="ecommerce-zone"

echo "Setting up Dataplex for project: ${PROJECT_ID}"
echo "================================================"

# Enable Dataplex API
echo "1. Enabling Dataplex API..."
gcloud services enable dataplex.googleapis.com --project=${PROJECT_ID}

# Create Dataplex Lake
echo "2. Creating Dataplex Lake: ${LAKE_ID}..."
gcloud dataplex lakes create ${LAKE_ID} \
    --location=${LOCATION} \
    --display-name="Ecommerce Data Lake" \
    --description="Lake for ecommerce BigQuery dataset" \
    --project=${PROJECT_ID} || echo "Lake may already exist"

# Create Dataplex Zone (for raw data)
echo "3. Creating Dataplex Zone: ${ZONE_ID}..."
gcloud dataplex zones create ${ZONE_ID} \
    --location=${LOCATION} \
    --lake=${LAKE_ID} \
    --type=RAW \
    --resource-location-type=SINGLE_REGION \
    --display-name="Ecommerce Zone" \
    --description="Zone for ecommerce BigQuery tables" \
    --project=${PROJECT_ID} || echo "Zone may already exist"

# Create Dataplex Asset to attach BigQuery dataset
echo "4. Creating Dataplex Asset for BigQuery dataset..."
gcloud dataplex assets create ecommerce-bigquery-asset \
    --location=${LOCATION} \
    --lake=${LAKE_ID} \
    --zone=${ZONE_ID} \
    --resource-type=BIGQUERY_DATASET \
    --resource-name=projects/${PROJECT_ID}/datasets/${DATASET_ID} \
    --discovery-enabled \
    --display-name="Ecommerce BigQuery Dataset" \
    --project=${PROJECT_ID} || echo "Asset may already exist"

echo ""
echo "================================================"
echo "Dataplex setup complete!"
echo ""
echo "You can view your Dataplex resources at:"
echo "https://console.cloud.google.com/dataplex/lakes?project=${PROJECT_ID}"
echo ""
echo "Wait a few minutes for Dataplex to discover and catalog the BigQuery tables."
