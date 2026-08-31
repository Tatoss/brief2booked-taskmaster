import base64
from email.utils import parseaddr
from hashlib import sha256

from google.cloud import firestore

from .google_tools import _workspace_service
from .models import EnquiryEvent

GMAIL_READ_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"


def _body_text(payload: dict) -> str:
    body = payload.get("body", {}).get("data")
    if payload.get("mimeType") == "text/plain" and body:
        return base64.urlsafe_b64decode(body + "===").decode("utf-8", errors="replace")
    for part in payload.get("parts", []):
        text = _body_text(part)
        if text:
            return text
    if body:
        return base64.urlsafe_b64decode(body + "===").decode("utf-8", errors="replace")
    return ""


def _normalise_message(message: dict) -> EnquiryEvent | None:
    if "SENT" in message.get("labelIds", []):
        return None
    headers = {
        item.get("name", "").lower(): item.get("value", "")
        for item in message.get("payload", {}).get("headers", [])
    }
    sender_name, sender_email = parseaddr(headers.get("from", ""))
    body = _body_text(message.get("payload", {})).strip()
    if not sender_email or not body:
        return None
    return EnquiryEvent(
        event_id=f"gmail-{message['id']}",
        source="gmail",
        sender_name=sender_name or sender_email.split("@", 1)[0],
        sender_email=sender_email,
        subject=headers.get("subject", "New client enquiry"),
        body=body[:20_000],
    )


def resolve_gmail_notification(notification: dict) -> list[EnquiryEvent]:
    """Resolve a Gmail watch history notification into normalized enquiries."""
    mailbox = notification["emailAddress"]
    current_history_id = str(notification["historyId"])
    state_id = sha256(mailbox.lower().encode()).hexdigest()
    state_ref = firestore.Client().collection("gmail_watch_state").document(state_id)
    state = state_ref.get().to_dict() or {}
    previous_history_id = state.get("history_id")
    if not previous_history_id:
        state_ref.set({"email": mailbox, "history_id": current_history_id}, merge=True)
        return []

    gmail = _workspace_service("gmail", "v1", [GMAIL_READ_SCOPE])
    message_ids: set[str] = set()
    request = gmail.users().history().list(
        userId="me",
        startHistoryId=previous_history_id,
        historyTypes=["messageAdded"],
    )
    while request is not None:
        response = request.execute()
        for history in response.get("history", []):
            for added in history.get("messagesAdded", []):
                if added.get("message", {}).get("id"):
                    message_ids.add(added["message"]["id"])
        request = gmail.users().history().list_next(request, response)

    enquiries: list[EnquiryEvent] = []
    for message_id in message_ids:
        message = gmail.users().messages().get(userId="me", id=message_id, format="full").execute()
        enquiry = _normalise_message(message)
        if enquiry:
            enquiries.append(enquiry)

    state_ref.set({"email": mailbox, "history_id": current_history_id}, merge=True)
    return enquiries
