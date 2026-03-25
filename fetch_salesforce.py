"""
Fetch open escalations and high-priority accounts from Salesforce.
Focuses on: open cases tagged as escalations, at-risk renewals, and
accounts with recent negative activity.
"""
from __future__ import annotations
import os
from datetime import date, timedelta


def fetch_escalations() -> dict:
    try:
        from simple_salesforce import Salesforce, SalesforceLogin

        sf = Salesforce(
            username=os.getenv("SALESFORCE_USERNAME", os.environ.get("JIRA_EMAIL", "")),
            password=os.environ["SALESFORCE_PASSWORD"],
            security_token=os.getenv("SALESFORCE_SECURITY_TOKEN", ""),
            instance_url=os.getenv("SALESFORCE_INSTANCE_URL", "https://uipath.my.salesforce.com"),
            domain="login",
        )
    except Exception as e:
        return {"error": f"Salesforce auth failed: {e}. Check SALESFORCE_* env vars."}

    seven_days_ago = (date.today() - timedelta(days=7)).isoformat()
    results: dict = {}

    # Open escalation cases
    try:
        cases = sf.query(
            f"""
            SELECT Id, CaseNumber, Subject, Status, Priority, Account.Name,
                   Owner.Name, CreatedDate, LastModifiedDate, Description
            FROM Case
            WHERE IsEscalated = true
              AND Status NOT IN ('Closed', 'Resolved')
              AND LastModifiedDate >= {seven_days_ago}T00:00:00Z
            ORDER BY Priority DESC, LastModifiedDate DESC
            LIMIT 20
            """
        )
        results["open_escalations"] = [
            {
                "case_number": c["CaseNumber"],
                "subject": c["Subject"],
                "account": (c.get("Account") or {}).get("Name", ""),
                "status": c["Status"],
                "priority": c["Priority"],
                "owner": (c.get("Owner") or {}).get("Name", ""),
                "created": c["CreatedDate"][:10],
                "url": f"{os.getenv('SALESFORCE_INSTANCE_URL', 'https://uipath.my.salesforce.com')}/{c['Id']}",
            }
            for c in cases["records"]
        ]
    except Exception as e:
        results["open_escalations_error"] = str(e)

    # High-priority open cases (not escalation, but critical/high)
    try:
        high_priority = sf.query(
            f"""
            SELECT Id, CaseNumber, Subject, Status, Priority, Account.Name, Owner.Name
            FROM Case
            WHERE Priority IN ('Critical', 'High')
              AND Status NOT IN ('Closed', 'Resolved')
              AND LastModifiedDate >= {seven_days_ago}T00:00:00Z
            ORDER BY CreatedDate DESC
            LIMIT 15
            """
        )
        results["high_priority_cases"] = [
            {
                "case_number": c["CaseNumber"],
                "subject": c["Subject"],
                "account": (c.get("Account") or {}).get("Name", ""),
                "priority": c["Priority"],
                "url": f"{os.getenv('SALESFORCE_INSTANCE_URL', 'https://uipath.my.salesforce.com')}/{c['Id']}",
            }
            for c in high_priority["records"]
        ]
    except Exception as e:
        results["high_priority_error"] = str(e)

    return results


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    import json
    print(json.dumps(fetch_escalations(), indent=2))
