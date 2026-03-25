"""
Morning Brief — main pipeline.
Fetches all data sources in parallel, synthesizes with Claude,
updates index.html dashboard, and sends Slack DM.

Usage:
  python build.py           # full run
  python build.py --dry-run # synthesize and print, no Slack / no deploy
"""
from __future__ import annotations
import argparse
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from fetch_jira import fetch_my_jira
from fetch_slack import fetch_slack_context
from fetch_outlook import fetch_outlook_all
from fetch_confluence import fetch_okr_page
from fetch_salesforce import fetch_escalations
from fetch_snowflake import fetch_metrics
from synthesize import synthesize_brief
from deliver_slack import send_brief


def _safe_call(fn, label: str, *args, **kwargs):
    """Run a fetch function, returning empty dict/list on error."""
    try:
        print(f"  → {label}...")
        result = fn(*args, **kwargs)
        print(f"    ✓ {label}")
        return result
    except Exception as e:
        print(f"    ✗ {label}: {e}")
        return {} if label != "calendar" else []


def fetch_all() -> dict:
    print("Fetching all data sources in parallel...")
    results: dict = {}

    tasks = {
        "jira": (fetch_my_jira, [], {}),
        "slack": (fetch_slack_context, [], {}),
        "outlook": (fetch_outlook_all, [], {}),
        "confluence": (fetch_okr_page, [], {}),
        "salesforce": (fetch_escalations, [], {}),
        "snowflake": (fetch_metrics, [], {}),
    }

    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {
            pool.submit(_safe_call, fn, label, *args, **kwargs): label
            for label, (fn, args, kwargs) in tasks.items()
        }
        for future in as_completed(futures):
            label = futures[future]
            try:
                results[label] = future.result()
            except Exception as e:
                results[label] = {}
                print(f"    ✗ {label} (unexpected): {e}")

    return results


def inject_into_html(brief: dict, data: dict) -> None:
    """Inject the brief JSON into index.html."""
    template_path = Path(__file__).parent / "index.html"
    if not template_path.exists():
        print("  ⚠ index.html not found — skipping dashboard update")
        return

    html = template_path.read_text()
    brief_json = json.dumps(brief, indent=2, default=str)
    data_json = json.dumps({
        "meetings": data.get("calendar", []),
        "metrics": data.get("snowflake", {}),
    }, indent=2, default=str)

    html = _replace_between(html, "/* BRIEF_DATA_START */", "/* BRIEF_DATA_END */",
                             f"const BRIEF = {brief_json};")
    html = _replace_between(html, "/* RAW_DATA_START */", "/* RAW_DATA_END */",
                             f"const RAW_DATA = {data_json};")
    template_path.write_text(html)
    print("  ✓ index.html updated")


def _replace_between(text: str, start_marker: str, end_marker: str, replacement: str) -> str:
    import re
    pattern = re.compile(
        re.escape(start_marker) + r".*?" + re.escape(end_marker),
        re.DOTALL,
    )
    new_block = f"{start_marker}\n{replacement}\n{end_marker}"
    if pattern.search(text):
        return pattern.sub(lambda _: new_block, text)
    # Marker not found — append before </script> as fallback
    return text


def _deliver_macos(brief: dict) -> None:
    import subprocess
    dashboard = Path(__file__).parent / "index.html"

    # Build notification body: headline + top todos
    todos = brief.get("todos", {})
    lines = []
    for t in todos.get("quick_wins", [])[:2]:
        lines.append(f"⚡ {t['task']}")
    for t in todos.get("must_close_today", [])[:2]:
        lines.append(f"🔴 {t['task']}")
    body = " · ".join(lines) if lines else brief.get("slack_summary", "")
    # Truncate for notification
    if len(body) > 200:
        body = body[:197] + "..."

    title = f"☀️ Morning Brief — {brief.get('date', '')}"
    headline = brief.get("headline", "")[:120]

    script = (
        f'display notification "{_esc(body)}" '
        f'with title "{_esc(title)}" '
        f'subtitle "{_esc(headline)}"'
    )
    subprocess.run(["osascript", "-e", script], check=False)
    print("  ✓ macOS notification sent")

    # Open dashboard in default browser
    subprocess.run(["open", str(dashboard)], check=False)
    print(f"  ✓ Dashboard opened ({dashboard})")


def _esc(s: str) -> str:
    """Escape string for osascript double-quoted string."""
    return s.replace("\\", "\\\\").replace('"', '\\"')


def main(dry_run: bool = False) -> None:
    print("=" * 50)
    print("MORNING BRIEF")
    print("=" * 50)

    # 1. Fetch
    data = fetch_all()

    # 2. Synthesize
    print("\nSynthesizing with Claude...")
    outlook = data.get("outlook", {})
    brief = synthesize_brief(
        calendar=outlook.get("calendar", []),
        email=outlook.get("email", {}),
        jira=data.get("jira", {}),
        slack=data.get("slack", {}),
        salesforce=data.get("salesforce", {}),
        metrics=data.get("snowflake", {}),
        okrs=data.get("confluence", {}),
    )
    print("  ✓ Brief synthesized")

    # Save raw output
    output_path = Path(__file__).parent / "latest_brief.json"
    output_path.write_text(json.dumps(brief, indent=2, default=str))
    print(f"  ✓ Saved to {output_path}")

    if dry_run:
        print("\n--- DRY RUN OUTPUT ---")
        print(json.dumps(brief, indent=2))
        return

    # 3. Update dashboard
    print("\nUpdating dashboard...")
    inject_into_html(brief, data)

    # 4. Deliver — macOS notification locally, Slack in CI
    print("\nDelivering notification...")
    import platform
    if platform.system() == "Darwin":
        _deliver_macos(brief)
    else:
        # CI / non-macOS — attempt Slack
        success = send_brief(brief)
        print("  ✓ Slack DM sent" if success else "  ✗ Slack DM failed (check token scope)")

    print("\n✓ Morning Brief complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Morning Brief pipeline")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print output without sending Slack DM or deploying")
    args = parser.parse_args()
    main(dry_run=args.dry_run)
