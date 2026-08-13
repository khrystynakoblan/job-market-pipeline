import os
import sys
import time

import requests

METABASE_URL = os.getenv("METABASE_URL", "http://metabase:3000").rstrip("/")
ADMIN_EMAIL = os.getenv("METABASE_ADMIN_EMAIL", "admin@jobmarket.local")
ADMIN_PASSWORD = os.getenv("METABASE_ADMIN_PASSWORD", "metabase_admin")
ADMIN_FIRST_NAME = os.getenv("METABASE_ADMIN_FIRST_NAME", "Job")
ADMIN_LAST_NAME = os.getenv("METABASE_ADMIN_LAST_NAME", "Market")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")
DATABASE_NAME = os.getenv("METABASE_DATABASE_NAME", "Job Market Pipeline")
DASHBOARD_NAME = os.getenv("METABASE_DASHBOARD_NAME", "Job Market Insights")


def wait_for_metabase(timeout_seconds: int = 300) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            response = requests.get(f"{METABASE_URL}/api/health", timeout=5)
            if response.status_code == 200:
                return
        except requests.RequestException:
            pass
        time.sleep(5)
    raise TimeoutError("Metabase did not become healthy in time")


def setup_admin_if_needed(session: requests.Session) -> None:
    properties = session.get(f"{METABASE_URL}/api/session/properties", timeout=30).json()
    if properties.get("has-user-setup"):
        return

    setup_token = properties.get("setup-token")
    if not setup_token:
        raise RuntimeError("Metabase setup token is missing")

    payload = {
        "token": setup_token,
        "user": {
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD,
            "first_name": ADMIN_FIRST_NAME,
            "last_name": ADMIN_LAST_NAME,
            "site_name": "Job Market Pipeline",
        },
        "prefs": {
            "site_name": "Job Market Pipeline",
            "site_locale": "en",
        },
    }
    response = session.post(f"{METABASE_URL}/api/setup", json=payload, timeout=30)
    response.raise_for_status()


def login(session: requests.Session) -> None:
    response = session.post(
        f"{METABASE_URL}/api/session",
        json={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=30,
    )
    response.raise_for_status()


def get_or_create_database(session: requests.Session) -> int:
    response = session.get(f"{METABASE_URL}/api/database", timeout=30)
    response.raise_for_status()

    for database in response.json().get("data", []):
        if database["name"] == DATABASE_NAME:
            return database["id"]

    payload = {
        "engine": "postgres",
        "name": DATABASE_NAME,
        "details": {
            "host": POSTGRES_HOST,
            "port": POSTGRES_PORT,
            "dbname": POSTGRES_DB,
            "user": POSTGRES_USER,
            "password": POSTGRES_PASSWORD,
            "ssl": False,
            "schema-filters-type": "inclusion",
            "schema-filters-patterns": "marts",
        },
        "auto_run_queries": True,
        "is_full_sync": True,
    }
    response = session.post(f"{METABASE_URL}/api/database", json=payload, timeout=60)
    response.raise_for_status()
    return response.json()["id"]


def create_native_card(
    session: requests.Session,
    database_id: int,
    name: str,
    sql: str,
    display: str,
    visualization_settings: dict,
) -> int:
    payload = {
        "name": name,
        "display": display,
        "visualization_settings": visualization_settings,
        "dataset_query": {
            "type": "native",
            "native": {"query": sql},
            "database": database_id,
        },
    }
    response = session.post(f"{METABASE_URL}/api/card", json=payload, timeout=30)
    response.raise_for_status()
    return response.json()["id"]


def get_or_create_dashboard(session: requests.Session) -> tuple[int, bool]:
    response = session.get(f"{METABASE_URL}/api/dashboard", timeout=30)
    response.raise_for_status()

    for dashboard in response.json():
        if dashboard["name"] == DASHBOARD_NAME:
            details = session.get(
                f"{METABASE_URL}/api/dashboard/{dashboard['id']}",
                timeout=30,
            ).json()
            return dashboard["id"], len(details.get("dashcards", [])) > 0

    response = session.post(
        f"{METABASE_URL}/api/dashboard",
        json={"name": DASHBOARD_NAME, "description": "Job market analytics dashboard"},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["id"], False


def add_cards_to_dashboard(
    session: requests.Session,
    dashboard_id: int,
    cards: list[tuple[int, int, int, int, int]],
) -> None:
    dashcards = []
    for index, (card_id, row, col, size_x, size_y) in enumerate(cards):
        dashcards.append(
            {
                "id": -index - 1,
                "card_id": card_id,
                "row": row,
                "col": col,
                "size_x": size_x,
                "size_y": size_y,
            }
        )

    response = session.put(
        f"{METABASE_URL}/api/dashboard/{dashboard_id}",
        json={"dashcards": dashcards},
        timeout=30,
    )
    response.raise_for_status()


def main() -> int:
    required = {
        "POSTGRES_USER": POSTGRES_USER,
        "POSTGRES_PASSWORD": POSTGRES_PASSWORD,
        "POSTGRES_DB": POSTGRES_DB,
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        print(f"Missing required environment variables: {', '.join(missing)}", file=sys.stderr)
        return 1

    wait_for_metabase()

    with requests.Session() as session:
        setup_admin_if_needed(session)
        login(session)
        database_id = get_or_create_database(session)

        top_skills_card = create_native_card(
            session,
            database_id,
            "Top 10 Skills by Demand",
            """
            select skill, job_count
            from marts.rpt_top_skills
            order by skill_rank
            """.strip(),
            "bar",
            {
                "graph.dimensions": ["skill"],
                "graph.metrics": ["job_count"],
                "graph.x_axis.title_text": "Skill",
                "graph.y_axis.title_text": "Job postings",
            },
        )

        salary_card = create_native_card(
            session,
            database_id,
            "Salary Distribution by City",
            """
            select
                city,
                median_salary,
                avg_salary,
                min_salary,
                max_salary,
                job_count
            from marts.rpt_salary_by_city
            order by median_salary desc
            """.strip(),
            "bar",
            {
                "graph.dimensions": ["city"],
                "graph.metrics": ["median_salary", "avg_salary"],
                "graph.x_axis.title_text": "City",
                "graph.y_axis.title_text": "Salary",
            },
        )

        weekly_card = create_native_card(
            session,
            database_id,
            "Weekly Job Posting Trend",
            """
            select week_start, job_count
            from marts.rpt_weekly_job_trends
            order by week_start
            """.strip(),
            "line",
            {
                "graph.dimensions": ["week_start"],
                "graph.metrics": ["job_count"],
                "graph.x_axis.title_text": "Week",
                "graph.y_axis.title_text": "Job postings",
            },
        )

        company_card = create_native_card(
            session,
            database_id,
            "Job Postings by Company",
            """
            select company_name, job_count
            from marts.rpt_jobs_by_company
            order by job_count desc
            limit 15
            """.strip(),
            "row",
            {
                "graph.dimensions": ["company_name"],
                "graph.metrics": ["job_count"],
            },
        )

        dashboard_id, has_cards = get_or_create_dashboard(session)
        if not has_cards:
            add_cards_to_dashboard(
                session,
                dashboard_id,
                [
                    (top_skills_card, 0, 0, 12, 7),
                    (weekly_card, 7, 0, 12, 7),
                    (salary_card, 14, 0, 12, 7),
                    (company_card, 21, 0, 12, 7),
                ],
            )

    print(f"Metabase dashboard ready: {METABASE_URL}/dashboard/{dashboard_id}")
    print(f"Login: {ADMIN_EMAIL}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
