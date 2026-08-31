import json
import os
import uuid

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from .google_tools import (
    create_delivery_tasks,
    create_proposal,
    draft_client_reply,
    record_workflow,
    reserve_follow_up,
)
from .models import EnquiryEvent, WorkflowDecision, WorkflowResult

MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
APP_NAME = "brief2booked"

coordinator = Agent(
    name="freelance_ops_coordinator",
    model=MODEL,
    description="Autonomous coordinator that converts inbound freelance enquiries into completed operational workflows.",
    input_schema=EnquiryEvent,
    output_schema=WorkflowDecision,
    instruction="""You are Brief2Booked, an event-driven operations coordinator for a South African software studio.
Read the enquiry and return ONLY valid JSON matching these keys:
service, summary, estimated_value_zar, delivery_weeks, fit_score, confidence, risks, next_action, rationale.
next_action must be qualify, request_clarification, or decline.
Qualify only when the request matches software, web, mobile, cloud, or IT services, confidence is at least 0.75,
and there are no legal, financial, credential, or irreversible-action risks. Never invent client facts.
All external email must remain a draft for human review.""",
)

session_service = InMemorySessionService()
runner = Runner(agent=coordinator, app_name=APP_NAME, session_service=session_service)


async def _decide(event: EnquiryEvent, run_id: str) -> WorkflowDecision:
    session = await session_service.create_session(app_name=APP_NAME, user_id="workflow", session_id=run_id)
    prompt = json.dumps(event.model_dump(mode="json"))
    message = types.Content(role="user", parts=[types.Part(text=prompt)])
    chunks = []
    async for item in runner.run_async(user_id="workflow", session_id=session.id, new_message=message):
        if item.content and item.content.parts:
            chunks.extend(part.text for part in item.content.parts if getattr(part, "text", None))
    raw = "".join(chunks).strip().removeprefix("```json").removesuffix("```").strip()
    if not raw.startswith("{"):
        start, end = raw.find("{"), raw.rfind("}")
        if start >= 0 and end > start:
            raw = raw[start : end + 1]
    return WorkflowDecision.model_validate_json(raw)


async def process_enquiry(event: EnquiryEvent) -> WorkflowResult:
    run_id = f"run-{uuid.uuid4().hex[:12]}"
    decision = await _decide(event, run_id)
    actions: list[dict] = []
    if decision.next_action != "qualify" or decision.confidence < 0.75:
        actions.append(draft_client_reply(run_id, event.sender_email, f"Re: {event.subject}", "Thanks for your enquiry. I need a few details before I can prepare the right next step."))
        result = WorkflowResult(run_id=run_id, status="needs_review", decision=decision, actions=actions)
        record_workflow(
            run_id,
            result.status,
            event.model_dump(mode="json"),
            decision.model_dump(mode="json"),
            actions,
        )
        return result

    proposal = f"""# Proposal for {event.company or event.sender_name}

## Understanding
{decision.summary}

## Recommended engagement
{decision.service}, delivered over approximately {decision.delivery_weeks} weeks.

## Working estimate
R{decision.estimated_value_zar:,}, subject to discovery and final scope.
"""
    actions.append(create_proposal(run_id, event.company or event.sender_name, proposal))
    actions.append(reserve_follow_up(run_id, event.company or event.sender_name, event.sender_email))
    actions.append(create_delivery_tasks(run_id, event.company or event.sender_name, decision.service))
    actions.append(draft_client_reply(run_id, event.sender_email, f"Re: {event.subject}", "Thank you for the clear brief. I have prepared a proposal and reserved a discovery slot for review."))
    result = WorkflowResult(run_id=run_id, status="completed", decision=decision, actions=actions)
    record_workflow(
        run_id,
        result.status,
        event.model_dump(mode="json"),
        decision.model_dump(mode="json"),
        actions,
    )
    return result
