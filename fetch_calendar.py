"""
Fetch today's meetings from:
- Google Calendar (personal Google Workspace account)
- Microsoft Outlook / Exchange (UiPath work account via MS Graph)
"""
from __future__ import annotations
import os
from datetime import datetime, timedelta, timezone
from typing import Optional
import pytz


# ── Google Calendar ────────────────────────────────────────────────────────────

def fetch_google_calendar(days_ahead: int = 3) -> list[dict]:
    """Returns events for today + next N days from Google Calendar."""
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
        import pickle, pathlib

        SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
        creds_path = os.getenv("GOOGLE_CREDENTIALS_JSON", "google_credentials.json")
        token_path = os.getenv("GOOGLE_TOKEN_JSON", "google_token.json")

        creds: Optional[Credentials] = None
        if pathlib.Path(token_path).exists():
            with open(token_path, "rb") as f:
                creds = pickle.load(f)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(token_path, "wb") as f:
                pickle.dump(creds, f)

        service = build("calendar", "v3", credentials=creds)
        tz = pytz.timezone(os.getenv("BRIEF_TIMEZONE", "America/New_York"))
        now = datetime.now(tz)
        end = now + timedelta(days=days_ahead)

        events_result = service.events().list(
            calendarId="primary",
            timeMin=now.isoformat(),
            timeMax=end.isoformat(),
            maxResults=30,
            singleEvents=True,
            orderBy="startTime",
        ).execute()

        return [_parse_google_event(e) for e in events_result.get("items", [])]
    except Exception as e:
        return [{"error": f"Google Calendar unavailable: {e}"}]


def _parse_google_event(e: dict) -> dict:
    start = e.get("start", {})
    start_str = start.get("dateTime") or start.get("date", "")
    return {
        "source": "google",
        "title": e.get("summary", "(no title)"),
        "start": start_str,
        "duration_min": _duration_min(e),
        "attendees": [a.get("email", "") for a in e.get("attendees", [])[:8]],
        "description": (e.get("description") or "")[:300],
        "meet_link": e.get("hangoutLink", ""),
        "location": e.get("location", ""),
    }


def _duration_min(e: dict) -> int:
    try:
        s = e["start"].get("dateTime")
        en = e["end"].get("dateTime")
        if s and en:
            from dateutil.parser import parse
            return int((parse(en) - parse(s)).total_seconds() / 60)
    except Exception:
        pass
    return 0


# ── Microsoft / Outlook ────────────────────────────────────────────────────────

def fetch_outlook_calendar(days_ahead: int = 3) -> list[dict]:
    """Returns events from Outlook via MS Graph API."""
    try:
        import msal
        import requests as req

        client_id = os.environ["MS_CLIENT_ID"]
        client_secret = os.environ["MS_CLIENT_SECRET"]
        tenant_id = os.environ["MS_TENANT_ID"]
        user_email = os.environ["MS_USER_EMAIL"]

        app = msal.ConfidentialClientApplication(
            client_id,
            authority=f"https://login.microsoftonline.com/{tenant_id}",
            client_credential=client_secret,
        )
        token_result = app.acquire_token_for_client(
            scopes=["https://graph.microsoft.com/.default"]
        )
        if "access_token" not in token_result:
            return [{"error": f"MS Graph auth failed: {token_result.get('error_description')}"}]

        headers = {"Authorization": f"Bearer {token_result['access_token']}"}
        tz = pytz.timezone(os.getenv("BRIEF_TIMEZONE", "America/New_York"))
        now = datetime.now(tz)
        end = now + timedelta(days=days_ahead)

        url = (
            f"https://graph.microsoft.com/v1.0/users/{user_email}/calendarView"
            f"?startDateTime={now.isoformat()}&endDateTime={end.isoformat()}"
            f"&$orderby=start/dateTime&$top=30"
            f"&$select=subject,start,end,attendees,bodyPreview,onlineMeeting,location"
        )
        resp = req.get(url, headers=headers)
        resp.raise_for_status()

        return [_parse_outlook_event(e) for e in resp.json().get("value", [])]
    except KeyError:
        return []  # MS credentials not configured, skip silently
    except Exception as e:
        return [{"error": f"Outlook calendar unavailable: {e}"}]


def _parse_outlook_event(e: dict) -> dict:
    attendees = [
        a.get("emailAddress", {}).get("address", "")
        for a in e.get("attendees", [])[:8]
    ]
    return {
        "source": "outlook",
        "title": e.get("subject", "(no title)"),
        "start": e.get("start", {}).get("dateTime", ""),
        "duration_min": _outlook_duration(e),
        "attendees": attendees,
        "description": e.get("bodyPreview", "")[:300],
        "meet_link": (e.get("onlineMeeting") or {}).get("joinUrl", ""),
        "location": (e.get("location") or {}).get("displayName", ""),
    }


def _outlook_duration(e: dict) -> int:
    try:
        from dateutil.parser import parse
        s = e["start"]["dateTime"]
        en = e["end"]["dateTime"]
        return int((parse(en) - parse(s)).total_seconds() / 60)
    except Exception:
        return 0


def fetch_all_calendar(days_ahead: int = 3) -> list[dict]:
    """Merge Google + Outlook calendars, deduplicated by title + start time."""
    google = fetch_google_calendar(days_ahead)
    outlook = fetch_outlook_calendar(days_ahead)
    all_events = google + outlook

    # Deduplicate: if same title + same hour, keep first occurrence
    seen: set[str] = set()
    deduped = []
    for ev in all_events:
        if "error" in ev:
            continue
        key = f"{ev['title'].lower().strip()}|{ev['start'][:13]}"
        if key not in seen:
            seen.add(key)
            deduped.append(ev)

    return sorted(deduped, key=lambda x: x.get("start", ""))


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    import json
    print(json.dumps(fetch_all_calendar(), indent=2))
