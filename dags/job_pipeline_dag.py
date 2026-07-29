import logging
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator

logger = logging.getLogger(__name__)


def on_failure_callback(context):
    task_instance = context["task_instance"]
    logger.error(
        "Task failed: dag_id=%s, task_id=%s, run_id=%s, execution_date=%s, try_number=%s",
        task_instance.dag_id,
        task_instance.task_id,
        context.get("run_id"),
        context.get("execution_date"),
        task_instance.try_number,
    )


default_args = {
    "owner": "airflow",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "sla": timedelta(minutes=30),
    "on_failure_callback": on_failure_callback,
}

with DAG(
    dag_id="job_market_pipeline",
    schedule="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["job-market"],
    default_args=default_args,
) as dag:
    extract_task = BashOperator(
        task_id="extract_task",
        bash_command="python /opt/airflow/extractors/extract_jobs.py",
    )

    dbt_run_task = BashOperator(
        task_id="dbt_run_task",
        bash_command=(
            "dbt run --project-dir /opt/airflow/dbt_project "
            "--profiles-dir /opt/airflow/dbt_project"
        ),
    )

    dbt_test_task = BashOperator(
        task_id="dbt_test_task",
        bash_command=(
            "dbt test --project-dir /opt/airflow/dbt_project "
            "--profiles-dir /opt/airflow/dbt_project"
        ),
    )

    notify_task = EmptyOperator(task_id="notify_task")

    extract_task >> dbt_run_task >> dbt_test_task >> notify_task
