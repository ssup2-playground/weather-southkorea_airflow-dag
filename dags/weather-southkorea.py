from datetime import datetime, timedelta

from airflow import DAG
from airflow.kubernetes.secret import Secret
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator

import pendulum
from kubernetes.client import models as k8s_models

## Init dag
dag = DAG(
    dag_id="weather-southkorea",
    default_args={
        "owner": "airflow",
        "depends_on_past": False,
        "retries": 5,
        "retry_delay": timedelta(minutes=10),
    },
    start_date=datetime(2023, 1, 1, tzinfo=pendulum.timezone("Asia/Seoul")),
    schedule="@hourly",
    catchup=True,
    max_active_tasks=4,
)

## Init operators
secret_aws_access_env = Secret(
    deploy_type="env",
    deploy_target="AWS_KEY_ACCESS",
    secret="aws-secret",
    key="AWS_KEY_ACCESS",
)

secret_aws_secret_env = Secret(
    deploy_type="env",
    deploy_target="AWS_KEY_SECRET",
    secret="aws-secret",
    key="AWS_KEY_SECRET",
)

secret_data_key_env = Secret(
    deploy_type="env",
    deploy_target="DATA_KEY",
    secret="data-secret",
    key="DATA_KEY",
)

synoptic_ingestor = KubernetesPodOperator(
    dag=dag,
    task_id="synoptic-ingestor",
    image="ghcr.io/ssup2-playground/weather-southkorea-injestor-synoptic:0.1.6",
    container_resources=k8s_models.V1ResourceRequirements(
        requests={"memory": "2Gi", "cpu": "500m"},
    ),
    env_vars={
        "AWS_REGION" : "ap-northeast-2",
        "AWS_S3_BUCKET" : "weather-southkorea-data",
        "AWS_S3_DIRECTORY" : "synoptic-hourly",
        "REQUEST_DATE" : "{{ execution_date.subtract(hours=24) | ds_nodash }}",
        "REQUEST_HOUR" : "{{ execution_date.subtract(hours=24).hour }}",
    },
    secrets=[secret_aws_access_env, secret_aws_secret_env, secret_data_key_env],
)

## Run
synoptic_ingestor