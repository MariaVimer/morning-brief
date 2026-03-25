"""
Fetch Jira items relevant to today's work:
- Tickets assigned to me (In Progress or To Do, updated recently)
- Items blocked or blocking others
- Items with today's due date
"""
from __future__ import annotations
import os
from datetime import date
import requests
from requests.auth import HTTPBasicAuth

JIRA_BASE = "https://uipath.atlassian.net"


def fetch_my_jira(days_back: int = 30) -> dict:
    auth = HTTPBasicAuth(os.environ["JIRA_EMAIL"], os.environ["JIRA_TOKEN"])
    email = os.environ["JIRA_EMAIL"]

    # Tickets assigned to me, active
    jql_mine = (
        f'assignee = "{email}" '
        f'AND status in ("In Progress", "To Do", "In Review", "Blocked") '
        f'AND updated >= "-{days_back}d" '
        f'ORDER BY priority DESC, updated DESC'
    )

    # Due today
    today = date.today().isoformat()
    jql_due = f'assignee = "{email}" AND due = "{today}"'

    results = {}
    for label, jql in [("active", jql_mine), ("due_today", jql_due)]:
        resp = requests.get(
            f"{JIRA_BASE}/rest/api/3/search/jql",
            params={
                "jql": jql,
                "maxResults": 50,
                "fields": "summary,status,priority,due,labels,components,assignee,description,comment,parent,issuetype",
            },
            auth=auth,
            headers={"Accept": "application/json"},
        )
        resp.raise_for_status()
        issues = resp.json().get("issues", [])
        results[label] = [
            {
                "key": i["key"],
                "summary": i["fields"]["summary"],
                "status": i["fields"]["status"]["name"],
                "priority": (i["fields"].get("priority") or {}).get("name", "—"),
                "due": i["fields"].get("due"),
                "url": f"{JIRA_BASE}/browse/{i['key']}",
                "type": i["fields"]["issuetype"]["name"],
            }
            for i in issues
        ]

    return results


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    import json
    print(json.dumps(fetch_my_jira(), indent=2))
