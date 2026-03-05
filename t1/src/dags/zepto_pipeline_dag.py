from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator


default_args = {
    "owner": "guruprasad",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
}


with DAG(
    dag_id="zepto_hotwheels_pipeline",
    default_args=default_args,
    description="Zepto Hot Wheels monitoring pipeline",
    schedule="*/15 * * * *",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["zepto", "monitoring"],
) as dag:
    task_scrape = BashOperator(
        task_id="task_scrape_zepto",
        bash_command="python -m scrapers.zepto_scrapper",
    )

    task_process_raw = BashOperator(
        task_id="task_process_raw_zepto",
        bash_command="python -m core.process_raw_zepto",
    )

    task_load_landing = BashOperator(
        task_id="task_load_landing_zepto",
        bash_command="python -m core.load_landing_zepto",
    )

    task_merge = BashOperator(
        task_id="task_merge_zepto",
        bash_command="python -m core.merge_to_current",
    )

    task_notify = BashOperator(
        task_id="task_notify_zepto",
        bash_command="python -m utils.telegram_notifier",
    )

    task_scrape >> task_process_raw >> task_load_landing >> task_merge >> task_notify
