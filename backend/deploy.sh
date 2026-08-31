#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-brief2booked}"
PROJECT_NUMBER="${GOOGLE_CLOUD_PROJECT_NUMBER:-147279859950}"
REGION="${GOOGLE_CLOUD_REGION:-africa-south1}"
SERVICE="${CLOUD_RUN_SERVICE:-brief2booked-agent}"
TOPIC="${PUBSUB_TOPIC:-brief2booked-enquiries}"
SERVICE_ACCOUNT_NAME="${AGENT_SERVICE_ACCOUNT:-brief2booked-agent}"
SERVICE_ACCOUNT="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
PUSH_SERVICE_ACCOUNT_NAME="${PUSH_SERVICE_ACCOUNT_NAME:-brief2booked-pubsub}"
PUSH_SERVICE_ACCOUNT="${PUSH_SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
SUBSCRIPTION="${PUBSUB_SUBSCRIPTION:-brief2booked-gmail-push}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "Deploying Brief2Booked to project ${PROJECT_ID} (${PROJECT_NUMBER})..."
gcloud config set project "${PROJECT_ID}"

gcloud services enable \
  aiplatform.googleapis.com \
  artifactregistry.googleapis.com \
  calendar-json.googleapis.com \
  cloudbuild.googleapis.com \
  cloudscheduler.googleapis.com \
  drive.googleapis.com \
  docs.googleapis.com \
  firestore.googleapis.com \
  gmail.googleapis.com \
  pubsub.googleapis.com \
  run.googleapis.com \
  secretmanager.googleapis.com

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

if ! gcloud iam service-accounts describe "${PUSH_SERVICE_ACCOUNT}" >/dev/null 2>&1; then
  gcloud iam service-accounts create "${PUSH_SERVICE_ACCOUNT_NAME}" \
    --display-name="Brief2Booked Pub/Sub Push"
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
  --source="${REPO_ROOT}" \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --platform=managed \
  --service-account="${SERVICE_ACCOUNT}" \
  --allow-unauthenticated \
  --cpu=1 \
  --memory=1Gi \
  --concurrency=20 \
  --timeout=300 \
  --min-instances=0 \
  --max-instances=3 \
  --labels="app=brief2booked,track=taskmaster" \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_LOCATION=global,GOOGLE_GENAI_USE_VERTEXAI=true,GEMINI_MODEL=gemini-3.5-flash,DEMO_MODE=true"

SERVICE_URL="$(gcloud run services describe "${SERVICE}" --region="${REGION}" --format='value(status.url)')"

gcloud iam service-accounts add-iam-policy-binding "${PUSH_SERVICE_ACCOUNT}" \
  --member="serviceAccount:service-${PROJECT_NUMBER}@gcp-sa-pubsub.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountTokenCreator" >/dev/null

gcloud pubsub topics add-iam-policy-binding "${TOPIC}" \
  --member="serviceAccount:gmail-api-push@system.gserviceaccount.com" \
  --role="roles/pubsub.publisher" >/dev/null

if ! gcloud pubsub subscriptions describe "${SUBSCRIPTION}" >/dev/null 2>&1; then
  gcloud pubsub subscriptions create "${SUBSCRIPTION}" \
    --topic="${TOPIC}" \
    --push-endpoint="${SERVICE_URL}/events/gmail" \
    --push-auth-service-account="${PUSH_SERVICE_ACCOUNT}" \
    --push-auth-token-audience="${SERVICE_URL}"
fi

gcloud run services update "${SERVICE}" \
  --region="${REGION}" \
  --update-env-vars="PUBSUB_PUSH_AUDIENCE=${SERVICE_URL},PUBSUB_PUSH_SERVICE_ACCOUNT=${PUSH_SERVICE_ACCOUNT}" >/dev/null

echo
echo "Deployment complete."
echo "Dashboard: ${SERVICE_URL}"
echo "Health: ${SERVICE_URL}/health"
echo "Demo:   ${SERVICE_URL}/v1/demo"
echo "Topic:  projects/${PROJECT_ID}/topics/${TOPIC}"
echo "Push:   projects/${PROJECT_ID}/subscriptions/${SUBSCRIPTION}"
