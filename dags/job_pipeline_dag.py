from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator

with DAG(
    dag_id="job_market_pipeline",
    schedule="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["job-market"],
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