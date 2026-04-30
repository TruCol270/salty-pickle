#!/bin/bash
set -e

PROJECT_ID="${GCP_PROJECT_ID:-salty-pickle}"
REGION="us-central1"

echo "Building and deploying to GCP..."

docker build -t gcr.io/$PROJECT_ID/salty-pickle-api .
docker build -t gcr.io/$PROJECT_ID/salty-pickle-frontend ./frontend

docker push gcr.io/$PROJECT_ID/salty-pickle-api:latest
docker push gcr.io/$PROJECT_ID/salty-pickle-frontend:latest

gcloud run deploy salty-pickle-api \
  --image gcr.io/$PROJECT_ID/salty-pickle-api:latest \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10

gcloud run deploy salty-pickle-frontend \
  --image gcr.io/$PROJECT_ID/salty-pickle-frontend:latest \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --memory 256Mi

echo "Deployment complete!"
