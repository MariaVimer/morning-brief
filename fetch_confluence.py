"""
Fetch OKRs and goals from the configured Confluence page.
Page: Big Rock Agents Bi-weekly — Appendix section (personal OKRs, P&E metrics, team KPIs)
"""
from __future__ import annotations
import os
import re
import requests
from requests.auth import HTTPBasicAuth

CONFLUENCE_BASE = "https://uipath.atlassian.net"


def fetch_okr_page() -> dict:
    page_id = os.environ["CONFLUENCE_OKR_PAGE_ID"]
    auth = HTTPBasicAuth(os.environ["JIRA_EMAIL"], os.environ["JIRA_TOKEN"])

    resp = requests.get(
        f"{CONFLUENCE_BASE}/wiki/rest/api/content/{page_id}",
        params={"expand": "body.storage,version,title"},
        auth=auth,
        headers={"Accept": "application/json"},
    )
    resp.raise_for_status()
    data = resp.json()

    title = data.get("title", "")
    body_html = data.get("body", {}).get("storage", {}).get("value", "")
    text = _strip_html(body_html)
    appendix_text = _extract_section(text, "Appendix")

    # Extract the known agent metrics from the telemetry table
    metrics = _parse_agent_metrics(text)

    # Maria's known ownership areas (extracted from the page)
    maria_items = _extract_maria_items(text)

    return {
        "page_title": title,
        "page_url": f"{CONFLUENCE_BASE}/wiki/spaces/Agents/pages/{page_id}",
        "full_text": text[:6000],
        "appendix_metrics": metrics,
        "maria_ownership": maria_items,
        "last_updated": data.get("version", {}).get("when", ""),
        "release": "26.4+",
    }


def _parse_agent_metrics(text: str) -> dict:
    """Pull structured numbers from the telemetry table in the Appendix."""
    def _find(pattern):
        m = re.search(pattern, text, re.IGNORECASE)
        return m.group(1).strip() if m else "N/A"

    return {
        "period": "February 2026 (latest complete month)",
        "lowcode": {
            "subsidiaries_deployed": _find(r"Subsidiary Who Deployed an Agent\s+(\d[\d,]+)\s"),
            "agents_deployed": _find(r"Agent Deployed\s+(\d[\d,]+)\s+\d"),
            "deployed_runs": _find(r"Deployed Agent Runs\s+(\d[\d,]+)\s"),
            "conversion_created_to_deployed": _find(r"Conversion from Created.*?Deployed\s+([\d.]+%)"),
            "retention": _find(r"Retained Agents\s+([\d.]+%)"),
            "avg_days_to_deploy": _find(r"Avg\. Time.*?Created to Deployed\s+([\d.]+)"),
        },
        "coded": {
            "subsidiaries_deployed": _find(r"Subsidiary Who Deployed an Agent\s+\d[\d,]+\s+\d+\s+\d[\d,]+\s+\d+\s+\d[\d,]+\s+(\d+)"),
            "agents_deployed": _find(r"Agent Deployed\s+\d[\d,]+\s+\d+\s+\d[\d,]+\s+\d+\s+\d[\d,]+\s+(\d+)"),
            "deployed_runs": _find(r"Deployed Agent Runs\s+\d[\d,]+\s+\d[\d,]+\s+\d[\d,]+\s+\d[\d,]+\s+\d[\d,]+\s+([\d,]+)"),
            "conversion_published_to_deployed": _find(r"Conversion.*?Deployed\s+[\d.]+%\s+([\d.]+%)"),
        },
        "source": "prod_orchestrator.dbo.jobs (external customers only, UiPath internal excluded)",
    }


def _extract_maria_items(text: str) -> list[str]:
    """Find agenda items owned by Maria."""
    items = []
    for m in re.finditer(r"(?:Updates from Maria|Maria on)[^.]*\.", text, re.IGNORECASE):
        items.append(m.group(0).strip())
    return items


def _strip_html(html: str) -> str:
    """Very basic HTML → plain text."""
    # Remove tags
    text = re.sub(r"<[^>]+>", " ", html)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _extract_section(text: str, section_name: str) -> str:
    """Extract text after a section heading."""
    pattern = re.compile(
        rf"{re.escape(section_name)}\s*(.*?)(?=\n[A-Z][A-Z]|\Z)",
        re.IGNORECASE | re.DOTALL,
    )
    m = pattern.search(text)
    return m.group(1).strip() if m else ""


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    import json
    print(json.dumps(fetch_okr_page(), indent=2))
