#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

"""
Example Airflow DAG for Google BigQuery service.
"""
import os
import time
from urllib.parse import urlparse

from airflow import models
from airflow.operators.bash import BashOperator
from airflow.providers.google.cloud.operators.bigquery import (
    BigQueryCreateEmptyDatasetOperator,
    BigQueryCreateEmptyTableOperator,
    BigQueryCreateExternalTableOperator,
    BigQueryDeleteDatasetOperator,
    BigQueryDeleteTableOperator,
    BigQueryGetDatasetOperator,
    BigQueryGetDatasetTablesOperator,
    BigQueryPatchDatasetOperator,
    BigQueryUpdateDatasetOperator,
    BigQueryUpsertTableOperator,
)
from airflow.utils.dates import days_ago

default_args = {"start_date": days_ago(1)}

PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "example-project")
BQ_LOCATION = "europe-north1"

DATASET_NAME = os.environ.get("GCP_BIGQUERY_DATASET_NAME", "test_dataset_operations")
LOCATION_DATASET_NAME = "{}_location".format(DATASET_NAME)
DATA_SAMPLE_GCS_URL = os.environ.get(
    "GCP_BIGQUERY_DATA_GCS_URL", "gs://cloud-samples-data/bigquery/us-states/us-states.csv",
)

DATA_SAMPLE_GCS_URL_PARTS = urlparse(DATA_SAMPLE_GCS_URL)
DATA_SAMPLE_GCS_BUCKET_NAME = DATA_SAMPLE_GCS_URL_PARTS.netloc
DATA_SAMPLE_GCS_OBJECT_NAME = DATA_SAMPLE_GCS_URL_PARTS.path[1:]


with models.DAG(
    "example_bigquery_operations",
    default_args=default_args,
    schedule_interval=None,  # Override to match your needs
    tags=["example"],
) as dag:
    # [START howto_operator_bigquery_create_table]
    create_table = BigQueryCreateEmptyTableOperator(
        task_id="create_table",
        dataset_id=DATASET_NAME,
        table_id="test_table",
        schema_fields=[
            {"name": "emp_name", "type": "STRING", "mode": "REQUIRED"},
            {"name": "salary", "type": "INTEGER", "mode": "NULLABLE"},
        ],
    )
    # [END howto_operator_bigquery_create_table]

    # [START howto_operator_bigquery_delete_table]
    delete_table = BigQueryDeleteTableOperator(
        task_id="delete_table", deletion_dataset_table=f"{PROJECT_ID}.{DATASET_NAME}.test_table",
    )
    # [END howto_operator_bigquery_delete_table]

    # [START howto_operator_bigquery_create_view]
    create_view = BigQueryCreateEmptyTableOperator(
        task_id="create_view",
        dataset_id=DATASET_NAME,
        table_id="test_view",
        view={"query": f"SELECT * FROM `{PROJECT_ID}.{DATASET_NAME}.test_table`", "useLegacySql": False,},
    )
    # [END howto_operator_bigquery_create_view]

    # [START howto_operator_bigquery_delete_view]
    delete_view = BigQueryDeleteTableOperator(
        task_id="delete_view", deletion_dataset_table=f"{PROJECT_ID}.{DATASET_NAME}.test_view"
    )
    # [END howto_operator_bigquery_delete_view]

    # [START howto_operator_bigquery_create_external_table]
    create_external_table = BigQueryCreateExternalTableOperator(
        task_id="create_external_table",
        bucket=DATA_SAMPLE_GCS_BUCKET_NAME,
        source_objects=[DATA_SAMPLE_GCS_OBJECT_NAME],
        destination_project_dataset_table=f"{DATASET_NAME}.external_table",
        skip_leading_rows=1,
        schema_fields=[{"name": "name", "type": "STRING"}, {"name": "post_abbr", "type": "STRING"},],
    )
    # [END howto_operator_bigquery_create_external_table]

    # [START howto_operator_bigquery_upsert_table]
    update_table = BigQueryUpsertTableOperator(
        task_id="update_table",
        dataset_id=DATASET_NAME,
        table_resource={
            "tableReference": {"tableId": "test_table_id"},
            "expirationTime": (int(time.time()) + 300) * 1000,
        },
    )
    # [END howto_operator_bigquery_upsert_table]

    # [START howto_operator_bigquery_create_dataset]
    create_dataset = BigQueryCreateEmptyDatasetOperator(task_id="create-dataset", dataset_id=DATASET_NAME)
    # [END howto_operator_bigquery_create_dataset]

    # [START howto_operator_bigquery_get_dataset_tables]
    get_dataset_tables = BigQueryGetDatasetTablesOperator(
        task_id="get_dataset_tables", dataset_id=DATASET_NAME
    )
    # [END howto_operator_bigquery_get_dataset_tables]

    # [START howto_operator_bigquery_get_dataset]
    get_dataset = BigQueryGetDatasetOperator(task_id="get-dataset", dataset_id=DATASET_NAME)
    # [END howto_operator_bigquery_get_dataset]

    get_dataset_result = BashOperator(
        task_id="get_dataset_result",
        bash_command="echo \"{{ task_instance.xcom_pull('get-dataset')['id'] }}\"",
    )

    # [START howto_operator_bigquery_patch_dataset]
    patch_dataset = BigQueryPatchDatasetOperator(
        task_id="patch_dataset",
        dataset_id=DATASET_NAME,
        dataset_resource={"friendlyName": "Patched Dataset", "description": "Patched dataset",},
    )
    # [END howto_operator_bigquery_patch_dataset]

    # [START howto_operator_bigquery_update_dataset]
    update_dataset = BigQueryUpdateDatasetOperator(
        task_id="update_dataset",
        dataset_id=DATASET_NAME,
        dataset_resource={"description": "Updated dataset"},
    )
    # [END howto_operator_bigquery_update_dataset]

    # [START howto_operator_bigquery_delete_dataset]
    delete_dataset = BigQueryDeleteDatasetOperator(
        task_id="delete_dataset", dataset_id=DATASET_NAME, delete_contents=True
    )
    # [END howto_operator_bigquery_delete_dataset]

    create_dataset >> patch_dataset >> update_dataset >> get_dataset >> get_dataset_result >> delete_dataset

    update_dataset >> create_table >> create_view >> [
        get_dataset_tables,
        delete_view,
    ] >> update_table >> delete_table >> delete_dataset
    update_dataset >> create_external_table >> delete_dataset

with models.DAG(
    "example_bigquery_operations_location",
    default_args=default_args,
    schedule_interval=None,  # Override to match your needs
    tags=["example"],
):
    create_dataset_with_location = BigQueryCreateEmptyDatasetOperator(
        task_id="create_dataset_with_location", dataset_id=LOCATION_DATASET_NAME, location=BQ_LOCATION,
    )

    create_table_with_location = BigQueryCreateEmptyTableOperator(
        task_id="create_table_with_location",
        dataset_id=LOCATION_DATASET_NAME,
        table_id="test_table",
        schema_fields=[
            {"name": "emp_name", "type": "STRING", "mode": "REQUIRED"},
            {"name": "salary", "type": "INTEGER", "mode": "NULLABLE"},
        ],
    )

    delete_dataset_with_location = BigQueryDeleteDatasetOperator(
        task_id="delete_dataset_with_location", dataset_id=LOCATION_DATASET_NAME, delete_contents=True,
    )
    create_dataset_with_location >> create_table_with_location >> delete_dataset_with_location
