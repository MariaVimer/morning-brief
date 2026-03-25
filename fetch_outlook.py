"""
Fetch Outlook calendar events and emails (inbox + sent) via Microsoft Graph API.

Auth: MSAL device code flow — sign in once in browser, token cached locally.
Setup:
  1. Register app at portal.azure.com → App registrations
  2. API permissions → Microsoft Graph → Delegated → add: Calendars.Read, Mail.Read
  3. Set MS_CLIENT_ID in .env
"""
from __future__ import annotations
import json
import os
import pathlib
from datetime import datetime, timedelta

import pytz

SCOPES = [
    "https://graph.microsoft.com/Calendars.Read",
    "https://graph.microsoft.com/Mail.Read",
    "https://graph.microsoft.com/User.Read",
]
TOKEN_CACHE_PATH = pathlib.Path(__file__).parent / "ms_token_cache.bin"
GRAPH = "https://graph.microsoft.com/v1.0"


# ── Auth ───────────────────────────────────────────────────────────────────────

def _get_token() -> str | None:
    client_id = os.getenv("MS_CLIENT_ID", "")
    if not client_id:
        return None
    try:
        import msal
    except ImportError:
        print("  ⚠ msal not installed — run: pip install msal")
        return None

    cache = msal.SerializableTokenCache()
    if TOKEN_CACHE_PATH.exists():
        cache.deserialize(TOKEN_CACHE_PATH.read_text())

    app = msal.PublicClientApplication(
        client_id,
        authority="https://login.microsoftonline.com/cdc5aeea-15c5-4db6-b079-fcadd2505dc2",
        token_cache=cache,
    )

    # Try silent (cached) first
    accounts = app.get_accounts()
    if accounts:
        result = app.acquire_token_silent(SCOPES, account=accounts[0])
        if result and "access_token" in result:
            TOKEN_CACHE_PATH.write_text(cache.serialize())
            return result["access_token"]

    # Device code flow — shows one-time login prompt
    flow = app.initiate_device_flow(scopes=SCOPES)
    if "user_code" not in flow:
        print(f"  ✗ Outlook auth failed: {flow.get('error_description')}")
        return None

    print(f"\n  ┌─ Outlook sign-in required (one time) ─────────────────────")
    print(f"  │  {flow['message']}")
    print(f"  └───────────────────────────────────────────────────────────\n")

    result = app.acquire_token_by_device_flow(flow)
    if "access_token" in result:
        TOKEN_CACHE_PATH.write_text(cache.serialize())
        return result["access_token"]

    print(f"  ✗ Outlook auth failed: {result.get('error_description')}")
    return None


def _graph_get(token: str, path: str, params: dict | None = None) -> dict:
    import requests
    resp = requests.get(
        f"{GRAPH}{path}",
        headers={"Authorization": f"Bearer {token}"},
        params=params or {},
    )
    resp.raise_for_status()
    return resp.json()


# ── Calendar ───────────────────────────────────────────────────────────────────

def fetch_outlook_calendar(days_ahead: int = 3) -> list[dict]:
    token = _get_token()
    if not token:
        return []

    tz = pytz.timezone(os.getenv("BRIEF_TIMEZONE", "America/New_York"))
    now = datetime.now(tz)
    end = now + timedelta(days=days_ahead)

    try:
        data = _graph_get(token, "/me/calendarView", {
            "startDateTime": now.isoformat(),
            "endDateTime": end.isoformat(),
            "$orderby": "start/dateTime",
            "$top": 50,
            "$select": "subject,start,end,attendees,bodyPreview,onlineMeeting,location,organizer,isCancelled",
        })
        events = [_parse_event(e) for e in data.get("value", []) if not e.get("isCancelled")]
        return events
    except Exception as e:
        return [{"error": f"Outlook calendar unavailable: {e}"}]


def _parse_event(e: dict) -> dict:
    attendees = [
        a.get("emailAddress", {}).get("address", "")
        for a in e.get("attendees", [])[:10]
    ]
    start_str = e.get("start", {}).get("dateTime", "")
    end_str = e.get("end", {}).get("dateTime", "")
    duration = 0
    if start_str and end_str:
        try:
            from dateutil.parser import parse
            duration = int((parse(end_str) - parse(start_str)).total_seconds() / 60)
        except Exception:
            pass
    return {
        "source": "outlook",
        "title": e.get("subject", "(no title)"),
        "start": start_str,
        "duration_min": duration,
        "attendees": attendees,
        "attendees_count": len(attendees),
        "organizer": e.get("organizer", {}).get("emailAddress", {}).get("address", ""),
        "description": e.get("bodyPreview", "")[:300],
        "meet_link": (e.get("onlineMeeting") or {}).get("joinUrl", ""),
        "location": (e.get("location") or {}).get("displayName", ""),
    }


# ── Email ──────────────────────────────────────────────────────────────────────

def fetch_outlook_email(lookback_hours: int | None = None) -> dict:
    """
    Fetch recent inbox + sent emails.
    Returns {"inbox": [...], "sent": [...]}
    """
    token = _get_token()
    if not token:
        return {"inbox": [], "sent": [], "error": "Outlook not configured"}

    hours = lookback_hours or int(os.getenv("LOOKBACK_HOURS", "16"))
    tz = pytz.timezone(os.getenv("BRIEF_TIMEZONE", "America/New_York"))
    since = (datetime.now(tz) - timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%SZ")

    result: dict = {"inbox": [], "sent": []}

    folders = {
        "inbox": "/me/mailFolders/inbox/messages",
        "sent": "/me/mailFolders/sentItems/messages",
    }

    for folder, path in folders.items():
        try:
            data = _graph_get(token, path, {
                "$filter": f"receivedDateTime ge {since}",
                "$orderby": "receivedDateTime desc",
                "$top": 30,
                "$select": "subject,from,toRecipients,receivedDateTime,bodyPreview,isRead,importance,conversationId",
            })
            result[folder] = [_parse_email(m, folder) for m in data.get("value", [])]
        except Exception as e:
            result[f"{folder}_error"] = str(e)

    return result


def _parse_email(m: dict, folder: str) -> dict:
    frm = m.get("from", {}).get("emailAddress", {})
    recipients = [
        r.get("emailAddress", {}).get("address", "")
        for r in m.get("toRecipients", [])[:5]
    ]
    return {
        "folder": folder,
        "subject": m.get("subject", "(no subject)"),
        "from": frm.get("address", ""),
        "from_name": frm.get("name", ""),
        "to": recipients,
        "preview": m.get("bodyPreview", "")[:400],
        "received": m.get("receivedDateTime", ""),
        "is_read": m.get("isRead", True),
        "importance": m.get("importance", "normal"),
        "conversation_id": m.get("conversationId", ""),
    }


# ── Combined ───────────────────────────────────────────────────────────────────

def fetch_outlook_all(days_ahead: int = 3) -> dict:
    """Returns {"calendar": [...], "email": {"inbox": [...], "sent": [...]}}"""
    if not os.getenv("MS_CLIENT_ID"):
        return {
            "calendar": [],
            "email": {"inbox": [], "sent": []},
            "error": "Outlook not configured — set MS_CLIENT_ID in .env",
        }
    token = _get_token()
    if not token:
        return {
            "calendar": [],
            "email": {"inbox": [], "sent": []},
            "error": "Outlook not configured — set MS_CLIENT_ID in .env",
        }

    # Run both in parallel would need threading; keep simple for now
    calendar = fetch_outlook_calendar(days_ahead)
    email = fetch_outlook_email()
    return {"calendar": calendar, "email": email}


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    import json as _json
    data = fetch_outlook_all()
    print(f"Calendar events: {len(data['calendar'])}")
    print(f"Inbox emails: {len(data['email']['inbox'])}")
    print(f"Sent emails: {len(data['email']['sent'])}")
    print(_json.dumps(data, indent=2, default=str)[:3000])
