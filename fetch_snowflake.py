"""
Fetch key product metrics from Snowflake:
- Agents in production (count, trend)
- Evals adoption (% of teams using evals, eval run counts)

Account: UIPATH-UIPATH_OBSERVABILITY
Dashboard source: https://app.snowflake.com/uipath/uipath_observability/
"""
from __future__ import annotations
import os
from datetime import date, timedelta


def fetch_metrics() -> dict:
    """Connect to Snowflake and pull agents-in-production + evals adoption."""
    try:
        import snowflake.connector

        auth_method = os.getenv("SNOWFLAKE_AUTHENTICATOR", "snowflake")
        connect_kwargs: dict = {
            "account": os.environ["SNOWFLAKE_ACCOUNT"],
            "user": os.environ["SNOWFLAKE_USER"],
            "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH"),
            "database": os.getenv("SNOWFLAKE_DATABASE", "UIPATH_OBSERVABILITY"),
            "schema": os.getenv("SNOWFLAKE_SCHEMA", "PUBLIC"),
            "client_session_keep_alive": True,
        }

        if auth_method == "externalbrowser":
            # SSO — opens browser once; subsequent runs reuse cached token
            connect_kwargs["authenticator"] = "externalbrowser"
        elif auth_method == "username_password_mfa":
            connect_kwargs["authenticator"] = "username_password_mfa"
            connect_kwargs["password"] = os.environ["SNOWFLAKE_PASSWORD"]
        else:
            connect_kwargs["password"] = os.environ["SNOWFLAKE_PASSWORD"]

        conn = snowflake.connector.connect(**connect_kwargs)
        cur = conn.cursor()

        today = date.today()
        seven_days_ago = (today - timedelta(days=7)).isoformat()
        thirty_days_ago = (today - timedelta(days=30)).isoformat()

        metrics = {}

        # ── Agents in production ──────────────────────────────────────────────
        # NOTE: Adjust table/column names to match your actual schema.
        # Run `SHOW TABLES;` in Snowflake to discover available tables.
        # Common patterns from observability schemas:
        agents_queries = [
            # Try common table name patterns
            ("agents_production_count",
             f"""
             SELECT
               COUNT(DISTINCT agent_id) AS agents_total,
               COUNT(DISTINCT CASE WHEN last_run_date >= '{seven_days_ago}' THEN agent_id END) AS agents_active_7d,
               COUNT(DISTINCT CASE WHEN last_run_date >= '{thirty_days_ago}' THEN agent_id END) AS agents_active_30d
             FROM agents_usage_production_ga
             WHERE status = 'production'
             """),
        ]

        for metric_name, query in agents_queries:
            try:
                cur.execute(query)
                rows = cur.fetchall()
                cols = [d[0].lower() for d in cur.description]
                if rows:
                    metrics[metric_name] = dict(zip(cols, rows[0]))
                break
            except Exception as e:
                metrics[f"{metric_name}_error"] = str(e)
                # Table might not exist — try to discover
                try:
                    cur.execute("SHOW TABLES LIKE '%AGENT%'")
                    tables = [r[1] for r in cur.fetchall()]
                    metrics["available_agent_tables"] = tables[:10]
                except Exception:
                    pass

        # ── Evals adoption ───────────────────────────────────────────────────
        evals_queries = [
            ("evals_adoption",
             f"""
             SELECT
               COUNT(DISTINCT tenant_id) AS tenants_using_evals,
               COUNT(DISTINCT run_id) AS eval_runs_7d,
               AVG(score) AS avg_score_7d
             FROM agent_evaluations
             WHERE run_date >= '{seven_days_ago}'
             """),
        ]

        for metric_name, query in evals_queries:
            try:
                cur.execute(query)
                rows = cur.fetchall()
                cols = [d[0].lower() for d in cur.description]
                if rows:
                    metrics[metric_name] = dict(zip(cols, rows[0]))
                break
            except Exception as e:
                metrics[f"{metric_name}_error"] = str(e)
                # Discover evals tables
                try:
                    cur.execute("SHOW TABLES LIKE '%EVAL%'")
                    tables = [r[1] for r in cur.fetchall()]
                    metrics["available_eval_tables"] = tables[:10]
                except Exception:
                    pass

        cur.close()
        conn.close()
        return metrics

    except ImportError:
        return {"error": "snowflake-connector-python not installed. Run: pip install snowflake-connector-python"}
    except KeyError as e:
        return {"error": f"Missing credential: {e}. Check your .env file."}
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    import json
    print(json.dumps(fetch_metrics(), indent=2, default=str))
