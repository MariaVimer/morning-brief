"""
Generate simulated morning briefs for the past 5 weekdays and rebuild the dashboard.
Run once to populate briefs/ history for testing.
"""
import json
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

BRIEFS = {
    "2026-03-18": {
        "date": "2026-03-18",
        "headline": "Evals design kicked off — alignment needed with ML before doc can move forward.",
        "todos": {
            "quick_wins": [
                {"task": "Add AE-1079 target date in Jira", "why": "Ticket has no due date and risks slipping", "source": "jira", "link": "https://uipath.atlassian.net/browse/AE-1079"},
            ],
            "must_close_today": [],
            "must_make_progress": [
                {"task": "Outline the no-ground-truth evals design doc", "why": "26.4 deliverable, unblocks downstream ML work", "source": "jira", "link": "https://uipath.atlassian.net/browse/AE-1079"},
            ],
            "must_communicate_with": [
                {"person_or_team": "Dragos (ML/Applied Science)", "about": "Align on feasibility of generated evals without labels", "channel": "slack", "urgency": "this_week"},
            ],
            "must_report_status": [],
        },
        "meetings_today": [
            {"title": "Agents bi-weekly TR", "time": "10:00", "duration_min": 60, "prep_note": "Review Autopilot Yellow risk and evals adoption numbers", "attendees_count": 14},
            {"title": "1:1 with Adrian", "time": "14:00", "duration_min": 30, "prep_note": "Flag evals design scope and request ML reviewer", "attendees_count": 2},
        ],
        "metrics_snapshot": {
            "agents_in_production": {"value": "187", "trend": "up", "vs_goal": "74% of Q2 target"},
            "evals_adoption": {"value": "23%", "trend": "flat", "vs_goal": "Below 40% goal"},
            "escalations_open": {"value": 4, "critical_count": 1},
        },
        "flags": [
            "Autopilot flagged Yellow in TR — downstream evals work may expand in scope.",
            "1 critical escalation open with Accenture — awaiting engineering triage.",
        ],
        "deliverables": {
            "tasks_completed": [
                {"item": "Created AE-1079 and wrote initial problem statement", "source": "jira", "link": "https://uipath.atlassian.net/browse/AE-1079"},
            ],
            "documents": [],
            "features_or_initiatives": [
                {"item": "Kicked off no-ground-truth evaluations initiative (evals 26.4)", "source": "jira", "link": "https://uipath.atlassian.net/browse/AE-1079"},
            ],
            "customer_enablement": [],
            "slack_supported": [
                {"item": "Answered question about eval metric definitions in #agents-pm", "channel": "agents-pm", "source": "slack"},
            ],
            "other": [],
        },
        "praise": [],
        "outcomes": {
            "business_impact": "Kicked off the no-ground-truth evals initiative and aligned leadership at bi-weekly TR on scope and 26.4 timeline.",
            "product_adoption": "Evals adoption at 23%, flat vs last week — design doc is the primary lever to unlock new customers.",
        },
        "slack_summary": "Evals design kicked off today. Created AE-1079 and flagged scope with Adrian. Autopilot risk is yellow — monitoring for downstream impact. 4 open escalations including 1 critical with Accenture.",
    },

    "2026-03-19": {
        "date": "2026-03-19",
        "headline": "Design doc structure agreed with ML — first full draft due before next TR.",
        "todos": {
            "quick_wins": [
                {"task": "Share evals doc outline with Jordan for early feedback", "why": "Jordan is tracking patterns work that overlaps with evals", "source": "slack", "link": ""},
            ],
            "must_close_today": [],
            "must_make_progress": [
                {"task": "Write Section 1 and Section 2 of AE-1079 design doc", "why": "Agreed with Dragos that draft needs to be shareable by end of week", "source": "jira", "link": "https://uipath.atlassian.net/browse/AE-1079"},
            ],
            "must_communicate_with": [
                {"person_or_team": "Jordan (Templates & Patterns)", "about": "Check for overlap between patterns spec and no-ground-truth evals", "channel": "slack", "urgency": "today"},
            ],
            "must_report_status": [],
        },
        "meetings_today": [
            {"title": "Evals sync with Dragos + Tomasz", "time": "11:00", "duration_min": 45, "prep_note": "Walk through the generated-evals technical constraints doc", "attendees_count": 3},
        ],
        "metrics_snapshot": {
            "agents_in_production": {"value": "189", "trend": "up", "vs_goal": "75% of Q2 target"},
            "evals_adoption": {"value": "24%", "trend": "up", "vs_goal": "Below 40% goal — improving"},
            "escalations_open": {"value": 3, "critical_count": 0},
        },
        "flags": [
            "Accenture critical escalation resolved by engineering — monitor for follow-up.",
        ],
        "deliverables": {
            "tasks_completed": [],
            "documents": [
                {"item": "Wrote Sections 1–2 of AE-1079 design doc (problem statement + proposed approach)", "source": "confluence", "link": "https://uipath.atlassian.net/wiki/spaces/Agents"},
            ],
            "features_or_initiatives": [],
            "customer_enablement": [],
            "slack_supported": [
                {"item": "Unblocked Tomasz on eval pipeline input format question", "channel": "agents-ml", "source": "slack"},
                {"item": "Clarified evals terminology for Zach's skills doc", "channel": "agents-content", "source": "slack"},
            ],
            "other": [],
        },
        "praise": [
            {"from": "Dragos (ML)", "quote": "Great clarity on the no-ground-truth constraint — exactly what we needed to scope the ML approach.", "context": "slack"},
        ],
        "outcomes": {
            "business_impact": "Resolved the critical Accenture escalation and aligned ML team on evals design approach, unblocking the 26.4 engineering track.",
            "product_adoption": "Evals adoption ticked up to 24% — design doc progress is the key driver. Draft sections written today accelerate reviewer turnaround.",
        },
        "slack_summary": "Strong day. Wrote sections 1–2 of the evals design doc and got positive alignment from Dragos/ML. Critical Accenture escalation resolved. Evals adoption at 24%, improving. No meetings tomorrow — good deep work window.",
    },

    "2026-03-20": {
        "date": "2026-03-20",
        "headline": "Customer enablement session delivered — three prospects now unblocked on evals setup.",
        "todos": {
            "quick_wins": [
                {"task": "Send follow-up resources to Siemens after enablement call", "why": "Promised eval framework doc links during the call", "source": "email", "link": ""},
            ],
            "must_close_today": [],
            "must_make_progress": [
                {"task": "Complete Section 3 (evaluation metrics) of AE-1079 design doc", "why": "Dragos is waiting to review metrics section before ML estimation", "source": "jira", "link": "https://uipath.atlassian.net/browse/AE-1079"},
            ],
            "must_communicate_with": [
                {"person_or_team": "Marius (leadership)", "about": "Quick update on evals doc progress and enablement outcomes", "channel": "slack", "urgency": "today"},
            ],
            "must_report_status": [],
        },
        "meetings_today": [
            {"title": "Customer enablement — Siemens, ABB, Michelin", "time": "09:00", "duration_min": 90, "prep_note": "Walk through eval framework setup guide and answer live questions", "attendees_count": 11},
            {"title": "Friday product standup", "time": "15:00", "duration_min": 30, "prep_note": "Share evals doc status and customer enablement outcomes", "attendees_count": 8},
        ],
        "metrics_snapshot": {
            "agents_in_production": {"value": "191", "trend": "up", "vs_goal": "76% of Q2 target"},
            "evals_adoption": {"value": "24%", "trend": "flat", "vs_goal": "Below 40% goal"},
            "escalations_open": {"value": 2, "critical_count": 0},
        },
        "flags": [],
        "deliverables": {
            "tasks_completed": [
                {"item": "Sent Siemens follow-up with eval framework resources", "source": "email", "link": ""},
            ],
            "documents": [
                {"item": "Completed Section 3 (evaluation metrics) of AE-1079 design doc", "source": "confluence", "link": "https://uipath.atlassian.net/wiki/spaces/Agents"},
            ],
            "features_or_initiatives": [],
            "customer_enablement": [
                {"item": "Led evals enablement session for Siemens, ABB, and Michelin — 3 prospects unblocked on setup", "source": "email"},
            ],
            "slack_supported": [
                {"item": "Answered post-session eval config questions from ABB team", "channel": "customer-abb", "source": "slack"},
            ],
            "other": [],
        },
        "praise": [
            {"from": "Elena (Siemens)", "quote": "This was the clearest explanation of the eval framework we've heard — finally feel confident to move forward.", "context": "email"},
            {"from": "Marius (leadership)", "quote": "Great work on the enablement call — this is exactly the kind of customer investment we need right now.", "context": "slack"},
        ],
        "outcomes": {
            "business_impact": "Three enterprise customers (Siemens, ABB, Michelin) unblocked on evals setup — direct pipeline impact for Q2 expansion deals.",
            "product_adoption": "Enablement session directly drives adoption for 3 accounts. Evals design doc Section 3 complete, accelerating ML review timeline.",
        },
        "slack_summary": "High-impact Friday. Led enablement for Siemens, ABB, and Michelin — 3 customers now unblocked. Finished Section 3 of the evals design doc. 2 open escalations, none critical. Praise from Siemens and Marius for the session quality.",
    },

    "2026-03-23": {
        "date": "2026-03-23",
        "headline": "Design doc review scheduled for Wednesday — need full draft ready by Tuesday EOD.",
        "todos": {
            "quick_wins": [
                {"task": "Add Section 4 outline (implementation timeline) to design doc", "why": "Reviewers asked for timeline before the Wednesday session", "source": "slack", "link": ""},
            ],
            "must_close_today": [
                {"task": "Complete full draft of AE-1079 design doc", "why": "Review session scheduled for Wed March 25 — reviewers need 24h to pre-read", "source": "jira", "link": "https://uipath.atlassian.net/browse/AE-1079", "deadline_note": "Must share by Tue EOD"},
            ],
            "must_make_progress": [],
            "must_communicate_with": [
                {"person_or_team": "Jordan, Dragos, Tomasz", "about": "Share completed design doc draft for Wednesday review", "channel": "slack", "urgency": "today"},
            ],
            "must_report_status": [
                {"topic": "AE-1079 design doc — draft complete, review scheduled", "to": "Adrian / Marius", "via": "slack", "note": "Brief update so leadership knows review is on track"},
            ],
        },
        "meetings_today": [
            {"title": "1:1 with Adrian", "time": "09:30", "duration_min": 30, "prep_note": "Confirm Wednesday review attendees and discuss Autopilot Yellow risk update", "attendees_count": 2},
        ],
        "metrics_snapshot": {
            "agents_in_production": {"value": "194", "trend": "up", "vs_goal": "77% of Q2 target"},
            "evals_adoption": {"value": "26%", "trend": "up", "vs_goal": "Accelerating — 3 new accounts from Friday enablement"},
            "escalations_open": {"value": 2, "critical_count": 0},
        },
        "flags": [
            "Design doc review is Wednesday — no room to slip. Must share draft today.",
        ],
        "deliverables": {
            "tasks_completed": [],
            "documents": [
                {"item": "Completed full draft of AE-1079 no-ground-truth evals design doc (all 4 sections)", "source": "confluence", "link": "https://uipath.atlassian.net/wiki/spaces/Agents"},
                {"item": "Shared draft with Jordan, Dragos, Tomasz for pre-read", "source": "slack", "link": ""},
            ],
            "features_or_initiatives": [],
            "customer_enablement": [],
            "slack_supported": [
                {"item": "Answered Michelin team question on eval dataset size requirements", "channel": "customer-michelin", "source": "slack"},
            ],
            "other": [],
        },
        "praise": [
            {"from": "Jordan (Templates)", "quote": "Just read the draft — this is really well structured. The no-ground-truth framing is exactly right.", "context": "slack"},
        ],
        "outcomes": {
            "business_impact": "Full design doc draft completed and shared with reviewers — on track for Wednesday review and 26.4 delivery.",
            "product_adoption": "Evals adoption jumped to 26% — Siemens, ABB, and Michelin accounts now active following Friday enablement session.",
        },
        "slack_summary": "Design doc is done and shared — review is Wednesday. Evals adoption at 26%, up 2 points driven by Friday's enablement. Praise from Jordan on the doc structure. 2 open escalations, none critical.",
    },

    "2026-03-24": {
        "date": "2026-03-24",
        "headline": "Design doc review completed — two open questions to resolve before final sign-off.",
        "todos": {
            "quick_wins": [
                {"task": "Update AE-1079 with reviewer comments from today's session", "why": "Two open questions raised by Dragos need clarification before final approval", "source": "jira", "link": "https://uipath.atlassian.net/browse/AE-1079"},
            ],
            "must_close_today": [],
            "must_make_progress": [
                {"task": "Draft response to Dragos's open questions on evaluation scoring thresholds", "why": "ML team needs this to finalize the implementation estimate", "source": "slack", "link": ""},
            ],
            "must_communicate_with": [
                {"person_or_team": "Dragos", "about": "Confirm scoring threshold approach from design doc review", "channel": "slack", "urgency": "today"},
                {"person_or_team": "Adrian", "about": "Share review outcomes and updated timeline to sign-off", "channel": "slack", "urgency": "today"},
            ],
            "must_report_status": [
                {"topic": "AE-1079 design doc review complete — pending 2 open questions", "to": "Adrian / Marius", "via": "slack", "note": "Sign-off expected by Thursday once Dragos confirms scoring approach"},
            ],
        },
        "meetings_today": [
            {"title": "AE-1079 Design Doc Review", "time": "10:00", "duration_min": 60, "prep_note": "Walk through all 4 sections, focus on scoring thresholds and timeline", "attendees_count": 6},
            {"title": "Agents weekly sync", "time": "14:00", "duration_min": 45, "prep_note": "Share evals progress, adoption numbers, and customer enablement outcomes", "attendees_count": 12},
        ],
        "metrics_snapshot": {
            "agents_in_production": {"value": "196", "trend": "up", "vs_goal": "78% of Q2 target"},
            "evals_adoption": {"value": "27%", "trend": "up", "vs_goal": "Trending toward 40% — 4 more accounts in onboarding"},
            "escalations_open": {"value": 1, "critical_count": 0},
        },
        "flags": [
            "Dragos flagged that scoring thresholds need more specificity — resolve before final sign-off.",
        ],
        "deliverables": {
            "tasks_completed": [
                {"item": "Ran AE-1079 design doc review session with 6 stakeholders", "source": "jira", "link": "https://uipath.atlassian.net/browse/AE-1079"},
                {"item": "Updated design doc with review feedback and open questions", "source": "confluence", "link": "https://uipath.atlassian.net/wiki/spaces/Agents"},
            ],
            "documents": [
                {"item": "Added reviewer comments and resolution notes to AE-1079 design doc", "source": "confluence", "link": ""},
            ],
            "features_or_initiatives": [],
            "customer_enablement": [],
            "slack_supported": [
                {"item": "Answered ABB question on eval run frequency and cost implications", "channel": "customer-abb", "source": "slack"},
                {"item": "Helped Zach with eval terminology for the skills doc", "channel": "agents-content", "source": "slack"},
            ],
            "other": [],
        },
        "praise": [
            {"from": "Tomasz (ML)", "quote": "Best-written design doc I've seen from PM in a while — the tradeoff section saved us a lot of back and forth.", "context": "slack"},
            {"from": "Adrian (leadership)", "quote": "Nice job driving the review efficiently. This is unblocking the whole evals track.", "context": "slack"},
        ],
        "outcomes": {
            "business_impact": "Design doc review completed with cross-functional alignment — evals 26.4 track unblocked pending two technical clarifications.",
            "product_adoption": "Evals adoption at 27% and accelerating — 4 more accounts in onboarding pipeline. ABB and Michelin moving to production setup.",
        },
        "slack_summary": "Design doc review done — great alignment across ML, Engineering, and PM. Two open questions to resolve with Dragos before final sign-off. Evals adoption at 27% with 4 more accounts onboarding. Praise from Tomasz and Adrian on the review quality.",
    },
}


def main():
    from build import inject_into_html, load_briefs_history
    import json
    from pathlib import Path

    briefs_dir = Path("briefs")
    briefs_dir.mkdir(exist_ok=True)

    # Write each simulated brief (skip if today's already exists)
    today_file = Path("briefs/2026-03-25.json")
    for date_str, brief in BRIEFS.items():
        path = briefs_dir / f"{date_str}.json"
        path.write_text(json.dumps(brief, indent=2))
        print(f"  ✓ Wrote {path}")

    # Rebuild dashboard with full history
    print("\nRebuilding dashboard...")
    latest = json.loads(Path("latest_brief.json").read_text())
    inject_into_html(latest, {"calendar": [], "snowflake": {}})
    print("Done. Open index.html to preview.")


if __name__ == "__main__":
    main()
