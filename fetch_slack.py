"""
Fetch Slack context since yesterday 5pm:
- DMs to me
- @mentions in any channel
- Messages in watched channels (escalations, product-updates, etc.)
"""
from __future__ import annotations
import os
from datetime import datetime, timedelta
import pytz
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Channels to watch for relevant messages (add channel IDs or names)
# These are read from env, comma-separated, so they're configurable
_DEFAULT_WATCHED_CHANNELS = [
    "product-support-escalations",
    "help-tif-voc",
    "platform-customer-engagement",
]


def _oldest_ts(hours_back: int = 16) -> str:
    tz = pytz.timezone(os.getenv("BRIEF_TIMEZONE", "America/New_York"))
    cutoff = datetime.now(tz) - timedelta(hours=hours_back)
    return str(cutoff.timestamp())


def fetch_slack_context(hours_back: int | None = None) -> dict:
    client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])
    hours = hours_back or int(os.getenv("LOOKBACK_HOURS", "16"))
    oldest = _oldest_ts(hours)
    my_user_id = os.environ["SLACK_USER_ID"]

    result: dict = {"mentions": [], "dms": [], "watched_channels": []}

    # --- DMs ---
    try:
        convos = client.conversations_list(types="im", limit=20)
        for ch in convos["channels"]:
            try:
                msgs = client.conversations_history(
                    channel=ch["id"], oldest=oldest, limit=30
                )
                for m in msgs["messages"]:
                    if m.get("text") and not m.get("bot_id"):
                        result["dms"].append({
                            "channel": ch["id"],
                            "user": m.get("user", "unknown"),
                            "text": m["text"][:500],
                            "ts": m["ts"],
                        })
            except SlackApiError:
                pass
    except SlackApiError:
        pass

    # --- Mentions across channels ---
    try:
        search = client.search_messages(
            query=f"<@{my_user_id}>",
            sort="timestamp",
            sort_dir="desc",
            count=20,
        )
        for m in search.get("messages", {}).get("matches", []):
            result["mentions"].append({
                "channel": m.get("channel", {}).get("name", ""),
                "user": m.get("username", ""),
                "text": m.get("text", "")[:500],
                "permalink": m.get("permalink", ""),
                "ts": m.get("ts", ""),
            })
    except SlackApiError:
        pass

    # --- Watched channels ---
    watched = os.getenv(
        "SLACK_WATCHED_CHANNELS", ",".join(_DEFAULT_WATCHED_CHANNELS)
    ).split(",")

    for channel_name in watched:
        channel_name = channel_name.strip()
        try:
            # Resolve name → ID
            found = client.conversations_list(types="public_channel,private_channel", limit=200)
            ch_id = next(
                (c["id"] for c in found["channels"] if c["name"] == channel_name),
                None
            )
            if not ch_id:
                continue
            msgs = client.conversations_history(channel=ch_id, oldest=oldest, limit=20)
            channel_msgs = []
            for m in msgs["messages"]:
                if m.get("text") and not m.get("bot_id"):
                    channel_msgs.append({
                        "user": m.get("user", ""),
                        "text": m["text"][:400],
                        "ts": m["ts"],
                    })
            if channel_msgs:
                result["watched_channels"].append({
                    "channel": channel_name,
                    "messages": channel_msgs[:10],
                })
        except SlackApiError:
            pass

    return result


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    import json
    print(json.dumps(fetch_slack_context(), indent=2))
