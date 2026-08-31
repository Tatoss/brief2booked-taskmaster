# Brief2Booked

**An autonomous freelance-operations agent for the Taskmaster track.**

[Open the live dashboard](https://brief2booked-taskmaster.texcorp.chatgpt.site)

Brief2Booked watches for a new client enquiry and completes the operational work that normally steals focus from a solo developer: it understands an unstructured brief, qualifies the opportunity, routes uncertain cases, creates a tailored proposal, reserves a follow-up slot, creates delivery tasks, drafts the client reply, and records every decision.

This is not a chatbot. The primary interface is an event-driven operations console; the agent runs asynchronously after a Gmail event and leaves completed work behind.

## The personal friction

Running Texcorp Solutions means switching from engineering into sales operations whenever an enquiry arrives. A promising message can require 30–60 minutes of reading, research, scoping, document preparation, calendar checking, follow-up writing, and pipeline administration. Delays cost leads; rushing creates bad estimates.

Brief2Booked turns that repeated, messy workflow into one observable and failure-tolerant action engine.

## What happens automatically

1. Gmail Watch emits a change event to Pub/Sub.
2. Cloud Run normalizes and deduplicates the event.
3. Google ADK runs Gemini 3.5 against the raw client brief.
4. Gemini classifies service, estimates fit and identifies risks.
5. The coordinator routes the workflow:
   - high confidence → proposal, calendar hold, tasks and reply draft;
   - unclear brief → clarification draft and review queue;
   - unsafe/out-of-scope → no downstream actions.
6. Google Drive receives the proposal.
7. Google Calendar receives a provisional discovery slot.
8. Gmail receives a reply **draft** (never an automatic send).
9. Firestore records state, outputs, timestamps and every tool action.
10. The dashboard shows the proof of action.

## Google technology

| Requirement | Implementation |
| --- | --- |
| Gemini 3.5+ | Gemini 3.5 Flash through Vertex AI |
| Agent framework | Google Agent Development Kit (ADK) 2.0 |
| Cloud infrastructure | Cloud Run, Pub/Sub and Firestore |
| Google tools | Gmail API, Calendar API and Drive API |
| Frontend | React / Next-compatible Vinext dashboard |

## Architecture

```mermaid
flowchart LR
  A["Gmail watch"] --> B["Pub/Sub"]
  B --> C["Cloud Run API"]
  C --> D["ADK + Gemini 3.5"]
  D --> E{"Confidence route"}
  E -->|High| F["Drive · Calendar · Gmail draft"]
  E -->|Low or risky| G["Review queue"]
  F --> H["Firestore audit log"]
  G --> H
  H --> I["Operations dashboard"]
```

The event boundary is separated from model reasoning and tool execution. Pub/Sub retries transient delivery failures. Firestore event receipts enforce idempotency. Tool permissions are scoped independently. The Gmail tool only has compose access and creates drafts.

## Repository structure

```text
app/                         Dashboard and interactive proof-of-action demo
backend/
  brief2booked/
    main.py                  Cloud Run API and Pub/Sub receiver
    agent.py                 ADK coordinator and routing policy
    google_tools.py          Scoped Workspace and Firestore actions
    models.py                Validated event, decision and result contracts
  Dockerfile
  requirements.txt
  deploy.sh
docs/
  DEVPOST.md                 Submission-ready project copy
  DEMO_SCRIPT.md             Four-minute video plan
```

## Run the dashboard

Prerequisites: Node.js 22+.

```bash
npm install
npm run dev
```

Open the displayed local URL and choose **Run demo**. The dashboard demo uses safe sample data and does not access external accounts.

## Run the agent API locally

Prerequisites: Python 3.12+, a Google Cloud project, Application Default Credentials, and Vertex AI access.

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
set -a && source .env && set +a
uvicorn brief2booked.main:app --reload --port 8080
```

Try the deterministic demo event:

```bash
curl -X POST http://localhost:8080/v1/demo
```

Keep `DEMO_MODE=true` until Google Workspace credentials and delegated scopes are configured.

## Deploy to Google Cloud

For project `brief2booked` (`147279859950`), open Google Cloud Shell from the project console and run:

```bash
git clone https://github.com/Tatoss/brief2booked-taskmaster.git
cd brief2booked-taskmaster
bash backend/deploy.sh
```

The script enables the required APIs, provisions Firestore in Johannesburg, creates the Pub/Sub topic and least-privilege agent service account, then deploys the Gemini 3.5 + ADK backend to Cloud Run.

After the demo deployment, configure Google Workspace domain-wide delegation and a Gmail Watch publisher before changing `DEMO_MODE` to `false`.

## Reliability and safety

- **Idempotency:** each Pub/Sub message is claimed once in `event_receipts`.
- **Schema validation:** all model decisions must pass a strict Pydantic contract.
- **Confidence routing:** scores below 0.75 cannot trigger proposal/calendar actions.
- **Least privilege:** Gmail compose scope creates drafts but cannot silently send mail.
- **Human boundary:** anything external, sensitive or irreversible is queued for review.
- **Auditability:** every action is written under its workflow run.
- **Failure recovery:** Pub/Sub retries transport failures; partial actions are idempotent by run and action name.
- **Privacy:** raw enquiries stay inside the configured Google Cloud project.

## New-project disclosure

Brief2Booked was created during the All Things Agentic Hackathon submission period. The project uses standard open-source libraries and the official Google SDKs listed in `backend/requirements.txt`. No pre-existing product code is included.

## License

Copyright © 2026 Texcorp Solutions (PTY) LTD. All rights reserved for the hackathon submission.
