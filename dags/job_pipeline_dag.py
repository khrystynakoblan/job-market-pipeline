from datetime import datetime

from airflow import DAG
from airflow.operators.empty import EmptyOperator

with DAG(
    dag_id="job_market_pipeline",
    schedule="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["job-market"],
) as dag:
    extract_task = EmptyOperator(task_id="extract_task")
    load_raw_task = EmptyOperator(task_id="load_raw_task")
    dbt_run_task = EmptyOperator(task_id="dbt_run_task")
    dbt_test_task = EmptyOperator(task_id="dbt_test_task")
    notify_task = EmptyOperator(task_id="notify_task")

    extract_task >> load_raw_task >> dbt_run_task >> dbt_test_task >> notify_task
