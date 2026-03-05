from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    "owner": "guruprasad",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="blinkit_hotwheels_pipeline",
    default_args=default_args,
    description="Blinkit Hot Wheels monitoring pipeline",
    schedule="*/15 * * * *",   # every 15 minutes
    start_date=datetime(2024, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["blinkit", "monitoring"],
) as dag:

    task_scrape = BashOperator(
        task_id="task_scrape",
        bash_command="python -m scrapers.blinkit_scrapper",
    )

    task_process_raw = BashOperator(
        task_id="task_process_raw",
        bash_command="python -m core.process_raw",
    )

    task_load_landing = BashOperator(
        task_id="task_load_landing",
        bash_command="python -m core.load_landing",
    )

    task_merge = BashOperator(
        task_id="task_merge",
        bash_command="python -m core.merge_to_current",
    )

    task_notify = BashOperator(
        task_id="task_notify",
        bash_command="python -m utils.telegram_notifier",
    )

    task_scrape >> task_process_raw >> task_load_landing >> task_merge >> task_notify
