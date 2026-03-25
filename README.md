# Morning Brief

Generates a prioritized daily brief at 7am EST. Pulls from Jira, Slack, Google Calendar, Outlook, Confluence, Salesforce, and Snowflake. Synthesizes with Claude. Delivers via Slack DM + web dashboard.

## Setup (15 minutes)

### 1. Copy and fill credentials
```bash
cp .env.example .env
```
Edit `.env` — required credentials marked in the file.

**Credentials you need:**
| Credential | Where to get it |
|---|---|
| `JIRA_TOKEN` | https://id.atlassian.com/manage-profile/security/api-tokens |
| `SLACK_USER_ID` | Slack → right-click your name → Copy member ID |
| `GOOGLE_CREDENTIALS_JSON` | Google Cloud Console → OAuth 2.0 credentials |
| `MS_CLIENT_ID/SECRET/TENANT` | Azure AD → App registrations |
| `SNOWFLAKE_PASSWORD` | Your UiPath SSO password (or use `SNOWFLAKE_AUTHENTICATOR=externalbrowser`) |
| `SALESFORCE_*` | Salesforce Settings → Security → Reset Security Token |

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Test locally
```bash
python build.py --dry-run   # synthesize and print, no Slack
python build.py             # full run
```

### 4. First Snowflake run (table discovery)
If the Snowflake queries fail on first run, check `latest_brief.json` — the error response will include `available_agent_tables` and `available_eval_tables`. Update `fetch_snowflake.py` with the correct table names.

### 5. GitHub Actions (scheduled 7am EST)
Add all credentials as GitHub repository secrets with the same names as in `.env.example`.

The workflow runs weekdays at 7am EST, commits the updated `index.html`, and deploys to Vercel.

### 6. Deploy dashboard to Vercel
```bash
VERCEL_TOKEN=vcp_... npx vercel --prod --yes
```
Set `DASHBOARD_URL` in your `.env` and GitHub secrets to the deployed URL.

## Manual trigger
From GitHub Actions → select "Morning Brief" → "Run workflow"

Or locally:
```bash
python build.py
```

## Architecture
```
build.py (orchestrator)
├── fetch_jira.py      → active/due tickets assigned to you
├── fetch_slack.py     → DMs, mentions, escalation channels
├── fetch_calendar.py  → Google Calendar + Outlook (merged, deduplicated)
├── fetch_confluence.py→ OKR page (goals, team KPIs, personal OKRs)
├── fetch_salesforce.py→ open escalations, high-priority cases
├── fetch_snowflake.py → agents in production, evals adoption
└── synthesize.py      → Claude → structured brief JSON
    └── deliver_slack.py → Slack DM (compact) + link to dashboard
```

## Adjusting what appears
- **Todo buckets**: edit the `PROMPT_TEMPLATE` in `synthesize.py`
- **Slack channels to monitor**: set `SLACK_WATCHED_CHANNELS` in `.env`
- **Metrics queries**: edit `fetch_snowflake.py` (run `SHOW TABLES` in Snowflake first)
- **Lookback window**: set `LOOKBACK_HOURS` in `.env` (default: 16)
