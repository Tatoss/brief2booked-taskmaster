#!/usr/bin/env bash
set -euo pipefail

: "${GOOGLE_CLOUD_PROJECT:?Set GOOGLE_CLOUD_PROJECT first}"
REGION="${GOOGLE_CLOUD_REGION:-africa-south1}"
SERVICE="${CLOUD_RUN_SERVICE:-brief2booked-agent}"

gcloud services enable run.googleapis.com aiplatform.googleapis.com firestore.googleapis.com pubsub.googleapis.com gmail.googleapis.com calendar-json.googleapis.com drive.googleapis.com
gcloud builds submit --tag "${REGION}-docker.pkg.dev/${GOOGLE_CLOUD_PROJECT}/brief2booked/agent:latest" backend
gcloud run deploy "${SERVICE}" \
  --image "${REGION}-docker.pkg.dev/${GOOGLE_CLOUD_PROJECT}/brief2booked/agent:latest" \
  --region "${REGION}" \
  --platform managed \
  --no-allow-unauthenticated \
  --set-env-vars "GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT},GOOGLE_CLOUD_LOCATION=global,GOOGLE_GENAI_USE_VERTEXAI=true,GEMINI_MODEL=gemini-3.5-flash,DEMO_MODE=false"
