#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-brief2booked}"
REGION="${GOOGLE_CLOUD_REGION:-africa-south1}"
SERVICE="${CLOUD_RUN_SERVICE:-brief2booked-agent}"
SERVICE_ACCOUNT_NAME="${AGENT_SERVICE_ACCOUNT:-brief2booked-agent}"
SERVICE_ACCOUNT="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
SECRET_NAME="${WORKSPACE_SECRET_NAME:-brief2booked-workspace-credentials}"
JOB="${GMAIL_WATCH_JOB:-brief2booked-gmail-watch}"
CREDENTIALS_FILE="${1:?Usage: GOOGLE_WORKSPACE_USER=you@domain.com bash backend/configure_workspace.sh /path/to/delegated-service-account.json}"
: "${GOOGLE_WORKSPACE_USER:?Set GOOGLE_WORKSPACE_USER to the delegated mailbox}"

if [[ ! -f "${CREDENTIALS_FILE}" ]]; then
  echo "Credentials file not found: ${CREDENTIALS_FILE}" >&2
  exit 1
fi

gcloud config set project "${PROJECT_ID}"
if ! gcloud secrets describe "${SECRET_NAME}" >/dev/null 2>&1; then
  gcloud secrets create "${SECRET_NAME}" --replication-policy=automatic
fi
gcloud secrets versions add "${SECRET_NAME}" --data-file="${CREDENTIALS_FILE}"
gcloud secrets add-iam-policy-binding "${SECRET_NAME}" \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/secretmanager.secretAccessor" >/dev/null

ENV_VARS="DEMO_MODE=false,GOOGLE_WORKSPACE_USER=${GOOGLE_WORKSPACE_USER}"
if [[ -n "${DRIVE_PROPOSALS_FOLDER_ID:-}" ]]; then
  ENV_VARS="${ENV_VARS},DRIVE_PROPOSALS_FOLDER_ID=${DRIVE_PROPOSALS_FOLDER_ID}"
fi

gcloud run services update "${SERVICE}" \
  --region="${REGION}" \
  --update-env-vars="${ENV_VARS},GOOGLE_APPLICATION_CREDENTIALS=/secrets/workspace.json" \
  --set-secrets="/secrets/workspace.json=${SECRET_NAME}:latest"

IMAGE="$(gcloud run services describe "${SERVICE}" --region="${REGION}" --format='value(spec.template.spec.containers[0].image)')"
gcloud run jobs deploy "${JOB}" \
  --region="${REGION}" \
  --image="${IMAGE}" \
  --service-account="${SERVICE_ACCOUNT}" \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_WORKSPACE_USER=${GOOGLE_WORKSPACE_USER},PUBSUB_TOPIC=brief2booked-enquiries,GOOGLE_APPLICATION_CREDENTIALS=/secrets/workspace.json" \
  --set-secrets="/secrets/workspace.json=${SECRET_NAME}:latest" \
  --command=python \
  --args=configure_gmail_watch.py \
  --max-retries=2 \
  --task-timeout=5m

gcloud run jobs execute "${JOB}" --region="${REGION}" --wait

gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/run.invoker" \
  --condition=None >/dev/null

if ! gcloud scheduler jobs describe "${JOB}-renewal" --location="${REGION}" >/dev/null 2>&1; then
  gcloud scheduler jobs create http "${JOB}-renewal" \
    --location="${REGION}" \
    --schedule="0 6 * * *" \
    --time-zone="Africa/Johannesburg" \
    --uri="https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/${JOB}:run" \
    --http-method=POST \
    --oauth-service-account-email="${SERVICE_ACCOUNT}"
fi

echo "Workspace production mode configured for ${GOOGLE_WORKSPACE_USER}."
echo "Gmail Watch will be renewed daily by Cloud Scheduler."
