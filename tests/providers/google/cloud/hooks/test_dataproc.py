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
#
import unittest

import mock
from google.cloud.dataproc_v1beta2.types import JobStatus  # pylint: disable=no-name-in-module

from airflow.exceptions import AirflowException
from airflow.providers.google.cloud.hooks.dataproc import DataprocHook, DataProcJobBuilder
from airflow.version import version

AIRFLOW_VERSION = "v" + version.replace(".", "-").replace("+", "-")

JOB = {"job": "test-job"}
JOB_ID = "test-id"
TASK_ID = "test-task-id"
GCP_LOCATION = "global"
GCP_PROJECT = "test-project"
CLUSTER = {"test": "test"}
CLUSTER_NAME = "cluster-name"

PARENT = "parent"
NAME = "name"
BASE_STRING = "airflow.providers.google.common.hooks.base_google.{}"
DATAPROC_STRING = "airflow.providers.google.cloud.hooks.dataproc.{}"


def mock_init(*args, **kwargs):
    pass


class TestDataprocHook(unittest.TestCase):
    def setUp(self):
        with mock.patch(BASE_STRING.format("GoogleBaseHook.__init__"), new=mock_init):
            self.hook = DataprocHook(gcp_conn_id="test")

    @mock.patch(DATAPROC_STRING.format("DataprocHook._get_credentials"))
    @mock.patch(
        DATAPROC_STRING.format("DataprocHook.client_info"), new_callable=mock.PropertyMock,
    )
    @mock.patch(DATAPROC_STRING.format("ClusterControllerClient"))
    def test_get_cluster_client(self, mock_client, mock_client_info, mock_get_credentials):
        self.hook.get_cluster_client(location=GCP_LOCATION)
        mock_client.assert_called_once_with(
            credentials=mock_get_credentials.return_value,
            client_info=mock_client_info.return_value,
            client_options={"api_endpoint": "{}-dataproc.googleapis.com:443".format(GCP_LOCATION)},
        )

    @mock.patch(DATAPROC_STRING.format("DataprocHook._get_credentials"))
    @mock.patch(
        DATAPROC_STRING.format("DataprocHook.client_info"), new_callable=mock.PropertyMock,
    )
    @mock.patch(DATAPROC_STRING.format("WorkflowTemplateServiceClient"))
    def test_get_template_client(self, mock_client, mock_client_info, mock_get_credentials):
        _ = self.hook.get_template_client
        mock_client.assert_called_once_with(
            credentials=mock_get_credentials.return_value, client_info=mock_client_info.return_value,
        )

    @mock.patch(DATAPROC_STRING.format("DataprocHook._get_credentials"))
    @mock.patch(
        DATAPROC_STRING.format("DataprocHook.client_info"), new_callable=mock.PropertyMock,
    )
    @mock.patch(DATAPROC_STRING.format("JobControllerClient"))
    def test_get_job_client(self, mock_client, mock_client_info, mock_get_credentials):
        self.hook.get_job_client(location=GCP_LOCATION)
        mock_client.assert_called_once_with(
            credentials=mock_get_credentials.return_value,
            client_info=mock_client_info.return_value,
            client_options={"api_endpoint": "{}-dataproc.googleapis.com:443".format(GCP_LOCATION)},
        )

    @mock.patch(DATAPROC_STRING.format("DataprocHook.get_cluster_client"))
    def test_create_cluster(self, mock_client):
        self.hook.create_cluster(project_id=GCP_PROJECT, region=GCP_LOCATION, cluster=CLUSTER)
        mock_client.assert_called_once_with(location=GCP_LOCATION)
        mock_client.return_value.create_cluster.assert_called_once_with(
            project_id=GCP_PROJECT,
            region=GCP_LOCATION,
            cluster=CLUSTER,
            metadata=None,
            request_id=None,
            retry=None,
            timeout=None,
        )

    @mock.patch(DATAPROC_STRING.format("DataprocHook.get_cluster_client"))
    def test_delete_cluster(self, mock_client):
        self.hook.delete_cluster(project_id=GCP_PROJECT, region=GCP_LOCATION, cluster_name=CLUSTER_NAME)
        mock_client.assert_called_once_with(location=GCP_LOCATION)
        mock_client.return_value.delete_cluster.assert_called_once_with(
            project_id=GCP_PROJECT,
            region=GCP_LOCATION,
            cluster_name=CLUSTER_NAME,
            cluster_uuid=None,
            metadata=None,
            request_id=None,
            retry=None,
            timeout=None,
        )

    @mock.patch(DATAPROC_STRING.format("DataprocHook.get_cluster_client"))
    def test_diagnose_cluster(self, mock_client):
        self.hook.diagnose_cluster(project_id=GCP_PROJECT, region=GCP_LOCATION, cluster_name=CLUSTER_NAME)
        mock_client.assert_called_once_with(location=GCP_LOCATION)
        mock_client.return_value.diagnose_cluster.assert_called_once_with(
            project_id=GCP_PROJECT,
            region=GCP_LOCATION,
            cluster_name=CLUSTER_NAME,
            metadata=None,
            retry=None,
            timeout=None,
        )

    @mock.patch(DATAPROC_STRING.format("DataprocHook.get_cluster_client"))
    def test_get_cluster(self, mock_client):
        self.hook.get_cluster(project_id=GCP_PROJECT, region=GCP_LOCATION, cluster_name=CLUSTER_NAME)
        mock_client.assert_called_once_with(location=GCP_LOCATION)
        mock_client.return_value.get_cluster.assert_called_once_with(
            project_id=GCP_PROJECT,
            region=GCP_LOCATION,
            cluster_name=CLUSTER_NAME,
            metadata=None,
            retry=None,
            timeout=None,
        )

    @mock.patch(DATAPROC_STRING.format("DataprocHook.get_cluster_client"))
    def test_list_clusters(self, mock_client):
        filter_ = "filter"

        self.hook.list_clusters(project_id=GCP_PROJECT, region=GCP_LOCATION, filter_=filter_)
        mock_client.assert_called_once_with(location=GCP_LOCATION)
        mock_client.return_value.list_clusters.assert_called_once_with(
            project_id=GCP_PROJECT,
            region=GCP_LOCATION,
            filter_=filter_,
            page_size=None,
            metadata=None,
            retry=None,
            timeout=None,
        )

    @mock.patch(DATAPROC_STRING.format("DataprocHook.get_cluster_client"))
    def test_update_cluster(self, mock_client):
        update_mask = "update-mask"
        self.hook.update_cluster(
            project_id=GCP_PROJECT,
            location=GCP_LOCATION,
            cluster=CLUSTER,
            cluster_name=CLUSTER_NAME,
            update_mask=update_mask,
        )
        mock_client.assert_called_once_with(location=GCP_LOCATION)
        mock_client.return_value.update_cluster.assert_called_once_with(
            project_id=GCP_PROJECT,
            region=GCP_LOCATION,
            cluster=CLUSTER,
            cluster_name=CLUSTER_NAME,
            update_mask=update_mask,
            graceful_decommission_timeout=None,
            metadata=None,
            request_id=None,
            retry=None,
            timeout=None,
        )

    @mock.patch(DATAPROC_STRING.format("DataprocHook.get_template_client"))
    def test_create_workflow_template(self, mock_client):
        template = {"test": "test"}
        mock_client.region_path.return_value = PARENT
        self.hook.create_workflow_template(location=GCP_LOCATION, template=template, project_id=GCP_PROJECT)
        mock_client.region_path.assert_called_once_with(GCP_PROJECT, GCP_LOCATION)
        mock_client.create_workflow_template.assert_called_once_with(
            parent=PARENT, template=template, retry=None, timeout=None, metadata=None
        )

    @mock.patch(DATAPROC_STRING.format("DataprocHook.get_template_client"))
    def test_instantiate_workflow_template(self, mock_client):
        template_name = "template_name"
        mock_client.workflow_template_path.return_value = NAME
        self.hook.instantiate_workflow_template(
            location=GCP_LOCATION, template_name=template_name, project_id=GCP_PROJECT
        )
        mock_client.workflow_template_path.assert_called_once_with(GCP_PROJECT, GCP_LOCATION, template_name)
        mock_client.instantiate_workflow_template.assert_called_once_with(
            name=NAME,
            version=None,
            parameters=None,
            request_id=None,
            retry=None,
            timeout=None,
            metadata=None,
        )

    @mock.patch(DATAPROC_STRING.format("DataprocHook.get_template_client"))
    def test_instantiate_inline_workflow_template(self, mock_client):
        template = {"test": "test"}
        mock_client.region_path.return_value = PARENT
        self.hook.instantiate_inline_workflow_template(
            location=GCP_LOCATION, template=template, project_id=GCP_PROJECT
        )
        mock_client.region_path.assert_called_once_with(GCP_PROJECT, GCP_LOCATION)
        mock_client.instantiate_inline_workflow_template.assert_called_once_with(
            parent=PARENT, template=template, request_id=None, retry=None, timeout=None, metadata=None,
        )

    @mock.patch(DATAPROC_STRING.format("DataprocHook.get_job"))
    def test_wait_for_job(self, mock_get_job):
        mock_get_job.side_effect = [
            mock.MagicMock(status=mock.MagicMock(state=JobStatus.RUNNING)),
            mock.MagicMock(status=mock.MagicMock(state=JobStatus.ERROR)),
        ]
        with self.assertRaises(AirflowException):
            self.hook.wait_for_job(
                job_id=JOB_ID, location=GCP_LOCATION, project_id=GCP_PROJECT, wait_time=0,
            )
        calls = [
            mock.call(location=GCP_LOCATION, job_id=JOB_ID, project_id=GCP_PROJECT),
            mock.call(location=GCP_LOCATION, job_id=JOB_ID, project_id=GCP_PROJECT),
        ]
        mock_get_job.has_calls(calls)

    @mock.patch(DATAPROC_STRING.format("DataprocHook.get_job_client"))
    def test_get_job(self, mock_client):
        self.hook.get_job(location=GCP_LOCATION, job_id=JOB_ID, project_id=GCP_PROJECT)
        mock_client.assert_called_once_with(location=GCP_LOCATION)
        mock_client.return_value.get_job.assert_called_once_with(
            region=GCP_LOCATION,
            job_id=JOB_ID,
            project_id=GCP_PROJECT,
            retry=None,
            timeout=None,
            metadata=None,
        )

    @mock.patch(DATAPROC_STRING.format("DataprocHook.get_job_client"))
    def test_submit_job(self, mock_client):
        self.hook.submit_job(location=GCP_LOCATION, job=JOB, project_id=GCP_PROJECT)
        mock_client.assert_called_once_with(location=GCP_LOCATION)
        mock_client.return_value.submit_job.assert_called_once_with(
            region=GCP_LOCATION,
            job=JOB,
            project_id=GCP_PROJECT,
            request_id=None,
            retry=None,
            timeout=None,
            metadata=None,
        )

    @mock.patch(DATAPROC_STRING.format("DataprocHook.wait_for_job"))
    @mock.patch(DATAPROC_STRING.format("DataprocHook.submit_job"))
    def test_submit(self, mock_submit_job, mock_wait_for_job):
        mock_submit_job.return_value.reference.job_id = JOB_ID
        with self.assertWarns(DeprecationWarning):
            self.hook.submit(project_id=GCP_PROJECT, job=JOB, region=GCP_LOCATION)
        mock_submit_job.assert_called_once_with(location=GCP_LOCATION, project_id=GCP_PROJECT, job=JOB)
        mock_wait_for_job.assert_called_once_with(
            location=GCP_LOCATION, project_id=GCP_PROJECT, job_id=JOB_ID
        )

    @mock.patch(DATAPROC_STRING.format("DataprocHook.get_job_client"))
    def test_cancel_job(self, mock_client):
        self.hook.cancel_job(location=GCP_LOCATION, job_id=JOB_ID, project_id=GCP_PROJECT)
        mock_client.assert_called_once_with(location=GCP_LOCATION)
        mock_client.return_value.cancel_job.assert_called_once_with(
            region=GCP_LOCATION,
            job_id=JOB_ID,
            project_id=GCP_PROJECT,
            retry=None,
            timeout=None,
            metadata=None,
        )


class TestDataProcJobBuilder(unittest.TestCase):
    def setUp(self) -> None:
        self.job_type = "test"
        self.builder = DataProcJobBuilder(
            project_id=GCP_PROJECT,
            task_id=TASK_ID,
            cluster_name=CLUSTER_NAME,
            job_type=self.job_type,
            properties={"test": "test"},
        )

    @mock.patch(DATAPROC_STRING.format("uuid.uuid4"))
    def test_init(self, mock_uuid):
        mock_uuid.return_value = "uuid"
        properties = {"test": "test"}
        job = {
            "job": {
                "labels": {"airflow-version": AIRFLOW_VERSION},
                "placement": {"cluster_name": CLUSTER_NAME},
                "reference": {"job_id": TASK_ID + "_uuid", "project_id": GCP_PROJECT},
                "test": {"properties": properties},
            }
        }
        builder = DataProcJobBuilder(
            project_id=GCP_PROJECT,
            task_id=TASK_ID,
            cluster_name=CLUSTER_NAME,
            job_type="test",
            properties=properties,
        )

        self.assertDictEqual(job, builder.job)

    def test_add_labels(self):
        labels = {"key": "value"}
        self.builder.add_labels(labels)
        self.assertIn("key", self.builder.job["job"]["labels"])
        self.assertEqual("value", self.builder.job["job"]["labels"]["key"])

    def test_add_variables(self):
        variables = ["variable"]
        self.builder.add_variables(variables)
        self.assertEqual(variables, self.builder.job["job"][self.job_type]["script_variables"])

    def test_add_args(self):
        args = ["args"]
        self.builder.add_args(args)
        self.assertEqual(args, self.builder.job["job"][self.job_type]["args"])

    def test_add_query(self):
        query = ["query"]
        self.builder.add_query(query)
        self.assertEqual({"queries": [query]}, self.builder.job["job"][self.job_type]["query_list"])

    def test_add_query_uri(self):
        query_uri = "query_uri"
        self.builder.add_query_uri(query_uri)
        self.assertEqual(query_uri, self.builder.job["job"][self.job_type]["query_file_uri"])

    def test_add_jar_file_uris(self):
        jar_file_uris = ["jar_file_uris"]
        self.builder.add_jar_file_uris(jar_file_uris)
        self.assertEqual(jar_file_uris, self.builder.job["job"][self.job_type]["jar_file_uris"])

    def test_add_archive_uris(self):
        archive_uris = ["archive_uris"]
        self.builder.add_archive_uris(archive_uris)
        self.assertEqual(archive_uris, self.builder.job["job"][self.job_type]["archive_uris"])

    def test_add_file_uris(self):
        file_uris = ["file_uris"]
        self.builder.add_file_uris(file_uris)
        self.assertEqual(file_uris, self.builder.job["job"][self.job_type]["file_uris"])

    def test_add_python_file_uris(self):
        python_file_uris = ["python_file_uris"]
        self.builder.add_python_file_uris(python_file_uris)
        self.assertEqual(python_file_uris, self.builder.job["job"][self.job_type]["python_file_uris"])

    def test_set_main_error(self):
        with self.assertRaises(Exception):
            self.builder.set_main("test", "test")

    def test_set_main_class(self):
        main = "main"
        self.builder.set_main(main_class=main, main_jar=None)
        self.assertEqual(main, self.builder.job["job"][self.job_type]["main_class"])

    def test_set_main_jar(self):
        main = "main"
        self.builder.set_main(main_class=None, main_jar=main)
        self.assertEqual(main, self.builder.job["job"][self.job_type]["main_jar_file_uri"])

    def test_set_python_main(self):
        main = "main"
        self.builder.set_python_main(main)
        self.assertEqual(main, self.builder.job["job"][self.job_type]["main_python_file_uri"])

    @mock.patch(DATAPROC_STRING.format("uuid.uuid4"))
    def test_set_job_name(self, mock_uuid):
        uuid = "test_uuid"
        mock_uuid.return_value = uuid
        name = "name"
        self.builder.set_job_name(name)
        name += "_" + uuid[:8]
        self.assertEqual(name, self.builder.job["job"]["reference"]["job_id"])

    def test_build(self):
        self.assertEqual(self.builder.job, self.builder.build())
