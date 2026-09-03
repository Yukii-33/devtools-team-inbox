import os

from fastapi import FastAPI, HTTPException

from .contact_router import DeveloperContact, RoutedContact, route_contact
from .infrai_email import InfraiEmail, InfraiError

app = FastAPI(title="Developer Tools Inbox")


@app.post("/contacts", response_model=RoutedContact, status_code=202)
async def submit_contact(contact: DeveloperContact) -> RoutedContact:
    api_key = os.environ["INFRAI_API_KEY"]
    team_inbox = os.environ["TEAM_INBOX"]
    sender = InfraiEmail(api_key)
    try:
        return await route_contact(contact, sender, team_inbox)
    except InfraiError as exc:
        caller_status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(
            status_code=caller_status,
            detail={"code": exc.code, "error": exc.detail},
        ) from exc
    finally:
        await sender.close()
