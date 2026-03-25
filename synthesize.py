"""
Take all raw data and produce a structured Morning Brief via Claude.
Returns a dict with todo buckets, meeting context, metrics, and a Slack summary.
"""
from __future__ import annotations
import json
import os
from datetime import date
import anthropic

MODEL = "claude-opus-4-6"

SYSTEM = """You are a Chief of Staff AI for a senior Product Manager at UiPath.
Every morning you synthesize their entire work context into a sharp, actionable brief.
You are direct, specific, and ruthlessly prioritizing. You don't pad.
Format your response as valid JSON only — no prose before or after."""

PROMPT_TEMPLATE = """Today is {today}.

Here is the PM's full context for today:

## CALENDAR (today + next 3 days)
{calendar}

## EMAIL — inbox and sent (last 16h)
{email}

## JIRA — active tickets assigned to me
{jira}

## SLACK — DMs, mentions, and escalation channels (last 16h)
{slack}

## SALESFORCE — open escalations and high-priority cases
{salesforce}

## SNOWFLAKE METRICS
{metrics}

## COMPANY GOALS / OKRs (from Confluence)
{okrs}

---

Based on ALL of the above, produce a Morning Brief as JSON with exactly this structure:

{{
  "date": "YYYY-MM-DD",
  "headline": "One sentence capturing the most important thing about today",

  "todos": {{
    "quick_wins": [
      {{"task": "...", "why": "...", "source": "jira|slack|salesforce", "link": "..."}}
    ],
    "must_close_today": [
      {{"task": "...", "why": "...", "source": "...", "link": "...", "deadline_note": "..."}}
    ],
    "must_make_progress": [
      {{"task": "...", "why": "...", "source": "...", "link": "..."}}
    ],
    "must_communicate_with": [
      {{"person_or_team": "...", "about": "...", "channel": "slack|email|meeting", "urgency": "today|this_week"}}
    ],
    "must_report_status": [
      {{"topic": "...", "to": "...", "via": "...", "note": "..."}}
    ]
  }},

  "meetings_today": [
    {{
      "title": "...",
      "time": "HH:MM",
      "duration_min": 0,
      "prep_note": "One thing to know or do before this meeting",
      "attendees_count": 0
    }}
  ],

  "metrics_snapshot": {{
    "agents_in_production": {{"value": "...", "trend": "up|down|flat|unknown", "vs_goal": "..."}},
    "evals_adoption": {{"value": "...", "trend": "up|down|flat|unknown", "vs_goal": "..."}},
    "escalations_open": {{"value": 0, "critical_count": 0}}
  }},

  "flags": [
    "Any risks, blockers, or things that need attention that don't fit elsewhere"
  ],

  "deliverables": {{
    "tasks_completed": [{{"item": "Jira ticket or task completed/resolved", "source": "jira", "link": "..."}}],
    "documents": [{{"item": "PRD, design doc, spec, or wiki page written or updated", "source": "jira|confluence", "link": "..."}}],
    "features_or_initiatives": [{{"item": "Feature, initiative, or project advanced", "source": "jira", "link": "..."}}],
    "customer_enablement": [{{"item": "Customer call, demo, training, or enablement session", "source": "salesforce|slack|email"}}],
    "slack_supported": [{{"item": "Thread or question you answered or unblocked", "channel": "...", "source": "slack"}}],
    "other": [{{"item": "Blog, event, prototype, git commit, or other output", "source": "..."}}]
  }},

  "praise": [
    {{"from": "Person name or team", "quote": "Exact or paraphrased positive feedback", "context": "slack|email"}}
  ],

  "outcomes": {{
    "business_impact": "One sentence: what moved the business forward today (escalations resolved, customers unblocked, decisions made, leadership alignment)",
    "product_adoption": "One sentence: progress on product adoption — metrics, features shipped, enablement done, or adoption-driving work advanced"
  }},

  "slack_summary": "3-4 sentence plain-English summary for Slack DM. Start with the headline. Mention the top 2 urgent items. End with meeting count for today."
}}

Rules:
- quick_wins: tasks completable in under 30 minutes. Prioritize these first.
- must_close_today: truly must be done today (deadline, blocking others, SLA).
- must_make_progress: important but not necessarily closable today.
- must_communicate_with: specific people who need a reply, update, or decision.
- must_report_status: stakeholders waiting on your status (leadership, cross-team, customers).
- deliverables: extract from Jira resolved/done tickets, Confluence pages updated, Slack threads where the PM helped, and email. Only include things actually done (past tense), not planned.
- praise: any explicit positive feedback, kudos, or appreciation from Slack messages or emails directed at the PM.
- outcomes.business_impact: synthesize the concrete business value from all data — be specific.
- outcomes.product_adoption: summarize adoption metric progress or adoption-driving work.
- Be specific. "Reply to Anurag about eval framework" is better than "check Slack messages."
- If data is unavailable for a metric, use "unavailable" as the value.
- Maximum 5 items per bucket. deliverables sub-lists max 5 each.
- Return ONLY valid JSON. No markdown fences."""


def synthesize_brief(
    calendar: list[dict],
    email: dict,
    jira: dict,
    slack: dict,
    salesforce: dict,
    metrics: dict,
    okrs: dict,
) -> dict:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    prompt = PROMPT_TEMPLATE.format(
        today=date.today().isoformat(),
        calendar=json.dumps(calendar, default=str, indent=2)[:3000],
        email=json.dumps(email, default=str, indent=2)[:3000],
        jira=json.dumps(jira, default=str, indent=2)[:3000],
        slack=json.dumps(slack, default=str, indent=2)[:3000],
        salesforce=json.dumps(salesforce, default=str, indent=2)[:2000],
        metrics=json.dumps(metrics, default=str, indent=2)[:1000],
        okrs=json.dumps(okrs, default=str, indent=2)[:2000],
    )

    msg = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = msg.content[0].text.strip()

    # Strip markdown fences if model added them anyway
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
        raw = raw.rsplit("```", 1)[0]

    return json.loads(raw)


if __name__ == "__main__":
    # Quick smoke test with empty data
    result = synthesize_brief([], {}, {}, {}, {}, {})
    print(json.dumps(result, indent=2))
