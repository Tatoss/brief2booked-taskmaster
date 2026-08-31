"""Start or renew Gmail Watch after Workspace delegation is configured."""

import os
from hashlib import sha256

from google.cloud import firestore

from brief2booked.gmail_events import GMAIL_READ_SCOPE
from brief2booked.google_tools import _workspace_service


def main() -> None:
    project_id = os.environ["GOOGLE_CLOUD_PROJECT"]
    workspace_user = os.environ["GOOGLE_WORKSPACE_USER"]
    topic = os.getenv("PUBSUB_TOPIC", "brief2booked-enquiries")
    topic_name = f"projects/{project_id}/topics/{topic}"
    gmail = _workspace_service("gmail", "v1", [GMAIL_READ_SCOPE])
    response = gmail.users().watch(
        userId="me",
        body={"topicName": topic_name, "labelIds": ["INBOX"]},
    ).execute()
    state_id = sha256(workspace_user.lower().encode()).hexdigest()
    firestore.Client().collection("gmail_watch_state").document(state_id).set(
        {
            "email": workspace_user,
            "history_id": str(response["historyId"]),
            "expiration": response.get("expiration"),
            "topic": topic_name,
        },
        merge=True,
    )
    print(f"Gmail Watch configured for {workspace_user} -> {topic_name}")
    print(f"History ID: {response['historyId']}")
    print(f"Expiration: {response.get('expiration', 'not returned')}")


if __name__ == "__main__":
    main()
