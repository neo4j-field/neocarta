set -e

# Load environment variables
source .env

PROJECT_ID=${GCP_PROJECT_ID}
LOCATION=us
GLOSSARY=retail-business-glossary

# 1. Create the glossary
gcloud dataplex glossaries create ${GLOSSARY} \
    --project=${PROJECT_ID} \
    --location=${LOCATION} \
    --display-name="Retail Business Glossary" \
    --description="Business glossary for the retail ecommerce dataset"

# 2. Create categories
gcloud dataplex glossaries categories create sales-metrics \
    --glossary=${GLOSSARY} \
    --project=${PROJECT_ID} \
    --location=${LOCATION} \
    --display-name="Sales Metrics" \
    --description="Key performance metrics for sales and revenue tracking" \
    --parent="projects/${PROJECT_ID}/locations/${LOCATION}/glossaries/${GLOSSARY}"

gcloud dataplex glossaries categories create entity-identifiers \
    --glossary=${GLOSSARY} \
    --project=${PROJECT_ID} \
    --location=${LOCATION} \
    --display-name="Entity Identifiers" \
    --description="Unique identifiers for core business entities" \
    --parent="projects/${PROJECT_ID}/locations/${LOCATION}/glossaries/${GLOSSARY}"

# 3. Create the Sales Metrics term
gcloud dataplex glossaries terms create gross-merchandise-value \
    --glossary=${GLOSSARY} \
    --project=${PROJECT_ID} \
    --location=${LOCATION} \
    --display-name="Gross Merchandise Value" \
    --description="Total sales revenue before deductions. Calculated as the sum of total_amount across all orders." \
    --parent="projects/${PROJECT_ID}/locations/${LOCATION}/glossaries/${GLOSSARY}/categories/sales-metrics"

# 4. Create Entity Identifier terms (one per ID field in the dataset)
gcloud dataplex glossaries terms create customer-id \
    --glossary=${GLOSSARY} \
    --project=${PROJECT_ID} \
    --location=${LOCATION} \
    --display-name="Customer ID" \
    --description="Unique integer identifier for a customer." \
    --parent="projects/${PROJECT_ID}/locations/${LOCATION}/glossaries/${GLOSSARY}/categories/entity-identifiers"

gcloud dataplex glossaries terms create product-id \
    --glossary=${GLOSSARY} \
    --project=${PROJECT_ID} \
    --location=${LOCATION} \
    --display-name="Product ID" \
    --description="Unique integer identifier for a product." \
    --parent="projects/${PROJECT_ID}/locations/${LOCATION}/glossaries/${GLOSSARY}/categories/entity-identifiers"

gcloud dataplex glossaries terms create order-id \
    --glossary=${GLOSSARY} \
    --project=${PROJECT_ID} \
    --location=${LOCATION} \
    --display-name="Order ID" \
    --description="Unique integer identifier for a customer order." \
    --parent="projects/${PROJECT_ID}/locations/${LOCATION}/glossaries/${GLOSSARY}/categories/entity-identifiers"

gcloud dataplex glossaries terms create order-item-id \
    --glossary=${GLOSSARY} \
    --project=${PROJECT_ID} \
    --location=${LOCATION} \
    --display-name="Order Item ID" \
    --description="Unique integer identifier for a line item within an order." \
    --parent="projects/${PROJECT_ID}/locations/${LOCATION}/glossaries/${GLOSSARY}/categories/entity-identifiers"