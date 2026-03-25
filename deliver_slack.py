"""
Send the Morning Brief to Slack as a DM.
Compact summary + link to full dashboard.
"""
from __future__ import annotations
import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

DASHBOARD_URL = os.getenv("DASHBOARD_URL", "https://morning-brief.vercel.app")


def send_brief(brief: dict) -> bool:
    client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])
    user_id = os.environ["SLACK_USER_ID"]

    todos = brief.get("todos", {})
    quick = todos.get("quick_wins", [])
    close = todos.get("must_close_today", [])
    communicate = todos.get("must_communicate_with", [])
    escalations = brief.get("metrics_snapshot", {}).get("escalations_open", {})

    # Build compact Slack message (Block Kit)
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f"☀️ Morning Brief — {brief.get('date', '')}"},
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"_{brief.get('headline', '')}_"},
        },
        {"type": "divider"},
    ]

    # Quick wins
    if quick:
        items = "\n".join(f"• {t['task']}" for t in quick[:3])
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*⚡ Quick wins*\n{items}"},
        })

    # Must close today
    if close:
        items = "\n".join(f"• {t['task']}" for t in close[:3])
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*🔴 Must close today*\n{items}"},
        })

    # Must communicate
    if communicate:
        items = "\n".join(f"• {t['person_or_team']}: {t['about']}" for t in communicate[:3])
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*💬 Must respond / communicate*\n{items}"},
        })

    # Metrics row
    m = brief.get("metrics_snapshot", {})
    agents = m.get("agents_in_production", {}).get("value", "—")
    evals = m.get("evals_adoption", {}).get("value", "—")
    esc_count = escalations.get("value", "—")
    esc_crit = escalations.get("critical_count", 0)

    meetings_today = len(brief.get("meetings_today", []))

    blocks.append({
        "type": "section",
        "fields": [
            {"type": "mrkdwn", "text": f"*Agents in prod:* {agents}"},
            {"type": "mrkdwn", "text": f"*Evals adoption:* {evals}"},
            {"type": "mrkdwn", "text": f"*Open escalations:* {esc_count} ({esc_crit} critical)"},
            {"type": "mrkdwn", "text": f"*Meetings today:* {meetings_today}"},
        ],
    })

    # Flags
    flags = brief.get("flags", [])
    if flags:
        flag_text = "\n".join(f"⚠️ {f}" for f in flags[:3])
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": flag_text},
        })

    # Link to full dashboard
    blocks.append({"type": "divider"})
    blocks.append({
        "type": "section",
        "text": {"type": "mrkdwn", "text": f"<{DASHBOARD_URL}|📋 Open full brief>"},
    })

    try:
        # If user_id starts with D it's already a DM channel ID; otherwise open one
        if user_id.startswith("D"):
            channel_id = user_id
        else:
            dm = client.conversations_open(users=user_id)
            channel_id = dm["channel"]["id"]

        client.chat_postMessage(
            channel=channel_id,
            blocks=blocks,
            text=brief.get("slack_summary", "Morning Brief ready."),  # fallback text
        )
        return True
    except SlackApiError as e:
        print(f"Slack delivery failed: {e.response['error']}")
        return False


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    # Test with dummy brief
    test_brief = {
        "date": "2026-03-24",
        "headline": "Test brief — Slack delivery check.",
        "todos": {
            "quick_wins": [{"task": "Reply to Anurag on eval framework"}],
            "must_close_today": [{"task": "Close AGENT-1234 PR review"}],
            "must_communicate_with": [{"person_or_team": "Leadership", "about": "Q2 roadmap status"}],
        },
        "meetings_today": [{"title": "Team sync"}],
        "metrics_snapshot": {
            "agents_in_production": {"value": "142"},
            "evals_adoption": {"value": "38%"},
            "escalations_open": {"value": 3, "critical_count": 1},
        },
        "flags": [],
        "slack_summary": "Test delivery successful.",
    }
    print("Sending test brief...")
    success = send_brief(test_brief)
    print("Sent!" if success else "Failed.")
