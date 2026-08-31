# Devpost submission copy

## Project name

Brief2Booked

## Tagline

An autonomous agent that turns messy client enquiries into qualified, proposal-ready and scheduled work.

## Inspiration

As a solo developer running Texcorp Solutions, I lose valuable build time every time a new enquiry arrives. Reading a vague brief is only the beginning: I must assess fit, estimate scope, check availability, prepare a proposal, arrange a follow-up, create tasks and remember to update the pipeline. The work is essential but repetitive, fragmented across apps and easy to delay.

I built Brief2Booked to remove that personal friction. It behaves like an operations coordinator that is always watching, understands the change that occurred and completes the appropriate workflow without waiting for step-by-step instructions.

## What it does

When Gmail receives a client enquiry, Pub/Sub wakes the agent on Cloud Run. Gemini 3.5 understands the unstructured message and produces a validated decision: requested service, estimated value and duration, opportunity fit, confidence, risks and next action.

The ADK coordinator routes high-confidence opportunities through the full workflow. It creates a proposal in Google Drive, reserves a discovery slot in Google Calendar, creates delivery tasks in Firestore and saves a personalised Gmail reply as a draft. Unclear or risky requests take a safer route and are queued for human review. Every model decision and tool action is captured in an observable workflow timeline.

## How I built it

- Gemini 3.5 Flash on Vertex AI for brief understanding and routing decisions
- Google ADK 2.0 for the autonomous coordinator
- Cloud Run for the asynchronous agent API
- Pub/Sub for event delivery and retry
- Firestore for idempotency, workflow state and audit events
- Gmail, Google Calendar and Google Drive APIs for real actions
- React/Next.js for the responsive Cloud Run operations dashboard

The architecture separates event ingestion, reasoning, routing, tools and state. Strict Pydantic schemas reject malformed model output. Firestore event receipts prevent duplicate work. Tool calls use least-privilege scopes, and Gmail creates drafts rather than sending externally without review.

## Challenges

The hardest problem was deciding where autonomy should stop. A Taskmaster agent must complete useful work, but client communication and time commitments can create reputational risk. I designed confidence-based routing and reversible actions: the system autonomously prepares everything, while the final external message stays reviewable.

The second challenge was reliable event execution. Pub/Sub can deliver an event more than once, so every event and downstream action has an idempotency key. This makes retries safe and gives the dashboard a trustworthy audit trail.

## Accomplishments

- A complete event-driven workflow rather than a conversational wrapper
- Autonomous routing from messy text to several Google applications
- Observable proof of action with decision rationale and tool-level events
- Failure-tolerant, idempotent execution
- A safety model that keeps the system useful without hiding consequential actions

## What I learned

Agent quality depends as much on architecture as prompting. Structured outputs, explicit state transitions, restricted tools and visible evidence make autonomy dependable. I also learned that the best personal agent is not the one that talks the most; it is the one that quietly returns finished work.

## What's next

Next I would add organisation-specific pricing memory, calendar free/busy optimisation, proposal templates by service, client approval links and outcome-based evaluation to improve qualification accuracy over time. The production connector already resolves Gmail Watch notifications through Gmail History and persists its renewal state in Firestore.
