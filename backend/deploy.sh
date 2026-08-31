#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-brief2booked}"
PROJECT_NUMBER="${GOOGLE_CLOUD_PROJECT_NUMBER:-147279859950}"
REGION="${GOOGLE_CLOUD_REGION:-africa-south1}"
SERVICE="${CLOUD_RUN_SERVICE:-brief2booked-agent}"
TOPIC="${PUBSUB_TOPIC:-brief2booked-enquiries}"
SERVICE_ACCOUNT_NAME="${AGENT_SERVICE_ACCOUNT:-brief2booked-agent}"
SERVICE_ACCOUNT="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Deploying Brief2Booked to project ${PROJECT_ID} (${PROJECT_NUMBER})..."
gcloud config set project "${PROJECT_ID}"

gcloud services enable \
  aiplatform.googleapis.com \
  artifactregistry.googleapis.com \
  calendar-json.googleapis.com \
  cloudbuild.googleapis.com \
  drive.googleapis.com \
  firestore.googleapis.com \
  gmail.googleapis.com \
  pubsub.googleapis.com \
  run.googleapis.com

if ! gcloud firestore databases describe --database="(default)" >/dev/null 2>&1; then
  gcloud firestore databases create \
    --database="(default)" \
    --location="${REGION}" \
    --type=firestore-native
fi

if ! gcloud pubsub topics describe "${TOPIC}" >/dev/null 2>&1; then
  gcloud pubsub topics create "${TOPIC}"
fi

if ! gcloud iam service-accounts describe "${SERVICE_ACCOUNT}" >/dev/null 2>&1; then
  gcloud iam service-accounts create "${SERVICE_ACCOUNT_NAME}" \
    --display-name="Brief2Booked Agent"
fi

gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/aiplatform.user" \
  --condition=None >/dev/null

gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/datastore.user" \
  --condition=None >/dev/null

gcloud run deploy "${SERVICE}" \
  --source="${SCRIPT_DIR}" \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --platform=managed \
  --service-account="${SERVICE_ACCOUNT}" \
  --allow-unauthenticated \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_LOCATION=global,GOOGLE_GENAI_USE_VERTEXAI=true,GEMINI_MODEL=gemini-3.5-flash,DEMO_MODE=true"

SERVICE_URL="$(gcloud run services describe "${SERVICE}" --region="${REGION}" --format='value(status.url)')"
echo
echo "Deployment complete."
echo "Health: ${SERVICE_URL}/health"
echo "Demo:   ${SERVICE_URL}/v1/demo"
echo "Topic:  projects/${PROJECT_ID}/topics/${TOPIC}"
