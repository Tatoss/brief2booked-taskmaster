# Four-minute demo script

## 0:00–0:25 — The friction

“I’m Thato Ramoshaba, a developer and founder of Texcorp Solutions. Every client enquiry pulls me out of engineering and into a chain of repetitive work across email, documents, calendar and project planning. Brief2Booked completes that workflow for me.”

Show the dashboard opening view.

## 0:25–0:50 — The event

Show the sample Gmail enquiry from Ubuntu Engineering. Explain that Gmail Watch publishes the change to Pub/Sub and wakes the private Cloud Run service. Briefly show the Pub/Sub topic and Cloud Run service URL/dashboard as required proof of Google Cloud deployment.

## 0:50–2:20 — Unedited proof of action

Start one continuous screen recording. Click **Run demo**.

As each event appears, narrate:

1. “The agent intercepted the enquiry without a chat prompt.”
2. “Gemini 3.5 extracted the requested service, budget, timeline and risks.”
3. “ADK applied the routing policy and qualified this opportunity at 92 out of 100.”
4. “The agent created a proposal in Drive.”
5. “It reserved a discovery slot in Calendar.”
6. “It created delivery tasks and a Gmail draft.”

Open the created Drive document, Calendar event and Gmail draft in quick succession. Do not cut the execution.

For this full Workspace proof, configure domain-wide delegation and set `DEMO_MODE=false` before recording. If recording in safe demo mode, state clearly that Gemini and Firestore are live while the reversible Workspace actions are simulated.

## 2:20–3:05 — Architecture and reliability

Show the architecture diagram in the README.

“Pub/Sub decouples the trigger from execution and retries transient failures. Firestore stores workflow state, claims event IDs to prevent duplicates and records every tool action. Model output must pass a strict schema before it can reach a tool.”

Show the Firestore run and action documents or live Cloud Run logs.

## 3:05–3:35 — Autonomous but safe

Show the decision panel.

“High-confidence, low-risk requests continue automatically. An unclear or risky enquiry follows a different branch and stops in review. Gmail has compose-only permission, so the agent prepares the work but cannot silently send an external commitment.”

## 3:35–3:55 — Value

“Brief2Booked gives solo developers back hours each week and responds to good opportunities while they are still fresh. It is not a chatbot. It is a background action engine that turns one event into completed operational work.”

End on the completed workflow and Google Cloud status.

## Recording checklist

- Keep the final video at 3:55 or shorter.
- Record in English or add English subtitles.
- Show an unedited live run.
- Show Cloud Run, Vertex AI logs or the `.run.app` service.
- Upload publicly to YouTube or Vimeo.
- Avoid real client names, messages and credentials.
