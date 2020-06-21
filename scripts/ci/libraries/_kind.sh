#!/usr/bin/env bash
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

function dump_kind_logs() {
    echo "###########################################################################################"
    echo "                   Dumping logs from KIND"
    echo "###########################################################################################"

    echo "EXIT_CODE is ${EXIT_CODE:=}"

    local DUMP_DIR_NAME DUMP_DIR
    DUMP_DIR_NAME=kind_logs_$(date "+%Y-%m-%d")_${CI_BUILD_ID:="default"}_${CI_JOB_ID:="default"}
    DUMP_DIR="/tmp/${DUMP_DIR_NAME}"
    verbose_kind --name "${KIND_CLUSTER_NAME}" export logs "${DUMP_DIR}"
}

function make_sure_kubernetes_tools_are_installed() {
    SYSTEM=$(uname -s| tr '[:upper:]' '[:lower:]')
    KIND_VERSION="v0.7.0"
    KIND_URL="https://github.com/kubernetes-sigs/kind/releases/download/${KIND_VERSION}/kind-${SYSTEM}-amd64"
    KIND_PATH="${BUILD_CACHE_DIR}/bin/kind"
    HELM_VERSION="v3.2.4"
    HELM_URL="https://get.helm.sh/helm-${HELM_VERSION}-${SYSTEM}-amd64.tar.gz"
    HELM_PATH="${BUILD_CACHE_DIR}/bin/helm"
    KUBECTL_VERSION="v1.15.3"
    KUBECTL_URL="https://storage.googleapis.com/kubernetes-release/release/${KUBECTL_VERSION}/bin/${SYSTEM}/amd64/kubectl"
    KUBECTL_PATH="${BUILD_CACHE_DIR}/bin/kubectl"
    mkdir -pv "${BUILD_CACHE_DIR}/bin"
    if [[ ! -f "${KIND_PATH}" ]]; then
        echo
        echo "Downloading Kind version ${KIND_VERSION}"
        echo
        curl --fail --location "${KIND_URL}" --output "${KIND_PATH}"
        chmod +x "${KIND_PATH}"
    fi
    if [[ ! -f "${KUBECTL_PATH}" ]]; then
        echo
        echo "Downloading Kubectl version ${KUBECTL_VERSION}"
        echo
        curl --fail --location "${KUBECTL_URL}" --output "${KUBECTL_PATH}"
        chmod +x "${KUBECTL_PATH}"
    fi
    if [[ ! -f "${HELM_PATH}" ]]; then
        echo
        echo "Downloading Helm version ${HELM_VERSION}"
        echo
        curl --fail --location "${HELM_URL}" |
            tar -xvz "${SYSTEM}-amd64/helm" -O >"${HELM_PATH}"

        chmod +x "${HELM_PATH}"
    fi
    PATH=${PATH}:${BUILD_CACHE_DIR}/bin
}

function create_cluster() {
    if [[ "${TRAVIS:="false"}" == "true" ]]; then
        # Travis CI does not handle the nice output of Kind well, so we need to capture it
        # And display only if kind fails to start
        start_output_heartbeat "Creating kubernetes cluster" 10
        set +e
        if ! OUTPUT=$(kind create cluster \
                        --name "${KIND_CLUSTER_NAME}" \
                        --config "${AIRFLOW_SOURCES}/scripts/ci/kubernetes/kind-cluster-conf.yaml" \
                        --image "kindest/node:${KUBERNETES_VERSION}" 2>&1); then
            echo "${OUTPUT}"
        fi
        stop_output_heartbeat
    else
        verbose_kind create cluster \
            --name "${KIND_CLUSTER_NAME}" \
            --config "${AIRFLOW_SOURCES}/scripts/ci/kubernetes/kind-cluster-conf.yaml" \
            --image "kindest/node:${KUBERNETES_VERSION}"
    fi
    echo
    echo "Created cluster ${KIND_CLUSTER_NAME}"
    echo

    echo
    echo "Patching CoreDNS to avoid loop and to use 8.8.8.8 DNS as forward address."
    echo
    echo "============================================================================"
    echo "      Original coredns configmap:"
    echo "============================================================================"
    verbose_kubectl --cluster "${KUBECTL_CLUSTER_NAME}" get configmaps --namespace=kube-system coredns -o yaml
    verbose_kubectl --cluster "${KUBECTL_CLUSTER_NAME}" get configmaps \
        --namespace=kube-system coredns -o yaml | \
        sed 's/forward \. .*$/forward . 8.8.8.8/' | kubectl --cluster "${KUBECTL_CLUSTER_NAME}" apply -f -

    echo
    echo "============================================================================"
    echo "      Updated coredns configmap with new forward directive:"
    echo "============================================================================"
    verbose_kubectl --cluster "${KUBECTL_CLUSTER_NAME}" get configmaps --namespace=kube-system coredns -o yaml


    echo
    echo "Restarting CoreDNS"
    echo
    verbose_kubectl --cluster "${KUBECTL_CLUSTER_NAME}" scale deployment \
        --namespace=kube-system coredns --replicas=0
    verbose_kubectl --cluster "${KUBECTL_CLUSTER_NAME}" scale deployment \
        --namespace=kube-system coredns --replicas=2
    echo
    echo "Restarted CoreDNS"
    echo
}

function delete_cluster() {
    verbose_kind delete cluster --name "${KIND_CLUSTER_NAME}"
    echo
    echo "Deleted cluster ${KIND_CLUSTER_NAME}"
    echo
    rm -rf "${HOME}/.kube/*"
}

function perform_kind_cluster_operation() {
    OPERATION="${1}"
    ALL_CLUSTERS=$(kind get clusters || true)

    echo
    echo "Kubernetes mode: ${KUBERNETES_MODE}"
    echo

    if [[ ${OPERATION} == "status" ]]; then
        if [[ ${ALL_CLUSTERS} == *"${KIND_CLUSTER_NAME}"* ]]; then
            echo
            echo "Cluster name: ${KIND_CLUSTER_NAME}"
            echo
            verbose_kind get nodes --name "${KIND_CLUSTER_NAME}"
            echo
            exit
        else
            echo
            echo "Cluster ${KIND_CLUSTER_NAME} is not running"
            echo
            exit
        fi
    fi
    if [[ ${ALL_CLUSTERS} == *"${KIND_CLUSTER_NAME}"* ]]; then
        if [[ ${OPERATION} == "start" ]]; then
            echo
            echo "Cluster ${KIND_CLUSTER_NAME} is already created"
            echo "Reusing previously created cluster"
            echo
        elif [[ ${OPERATION} == "restart" ]]; then
            echo
            echo "Recreating cluster"
            echo
            delete_cluster
            create_cluster
        elif [[ ${OPERATION} == "stop" ]]; then
            echo
            echo "Deleting cluster"
            echo
            delete_cluster
            exit
        elif [[ ${OPERATION} == "deploy" ]]; then
            echo
            echo "Deploying Airflow to KinD"
            echo
            get_ci_environment
            make_sure_kubernetes_tools_are_installed
            build_prod_image_for_kubernetes_tests
            load_image_to_kind_cluster
            deploy_airflow_with_helm
        elif [[ ${OPERATION} == "test" ]]; then
            echo
            echo "Testing with kind to KinD"
            echo
            "${AIRFLOW_SOURCES}/scripts/ci/ci_run_kubernetes_tests.sh"
        else
            echo
            echo "Wrong cluster operation: ${OPERATION}. Should be one of:"
            echo "${FORMATTED_KIND_OPERATIONS}"
            echo
            exit 1
        fi
    else
        if [[ ${OPERATION} == "start" ]]; then
            echo
            echo "Creating cluster"
            echo
            create_cluster
        elif [[ ${OPERATION} == "recreate" ]]; then
            echo
            echo "Cluster ${KIND_CLUSTER_NAME} does not exist. Creating rather than recreating"
            echo "Creating cluster"
            echo
            create_cluster
        elif [[ ${OPERATION} == "stop" || ${OEPRATON} == "deploy" || ${OPERATION} == "test" ]]; then
            echo
            echo "Cluster ${KIND_CLUSTER_NAME} does not exist. It should exist for ${OPERATION} operation"
            echo
            exit 1
        else
            echo
            echo "Wrong cluster operation: ${OPERATION}. Should be one of:"
            echo "${FORMATTED_KIND_OPERATIONS}"
            echo
            exit 1
        fi
    fi
}

function check_cluster_ready_for_airflow() {
    verbose_kubectl cluster-info --cluster "${KUBECTL_CLUSTER_NAME}"
    verbose_kubectl get nodes --cluster "${KUBECTL_CLUSTER_NAME}"
    echo
    echo "Showing storageClass"
    echo
    verbose_kubectl get storageclass --cluster "${KUBECTL_CLUSTER_NAME}"
    echo
    echo "Showing kube-system pods"
    echo
    verbose_kubectl get -n kube-system pods --cluster "${KUBECTL_CLUSTER_NAME}"
    echo
    echo "Airflow environment on kubernetes is good to go!"
    echo
    verbose_kubectl create namespace test-namespace --cluster "${KUBECTL_CLUSTER_NAME}"
}


function build_prod_image_for_kubernetes_tests() {
    cd "${AIRFLOW_SOURCES}" || exit 1
    export EMBEDDED_DAGS="airflow/example_dags"
    export DOCKER_CACHE="local"
    prepare_prod_build
    build_prod_image
    echo "The ${AIRFLOW_PROD_IMAGE} is prepared for test kubernetes deployment."
}

function load_image_to_kind_cluster() {
    echo
    echo "Loading ${AIRFLOW_PROD_IMAGE} to ${KIND_CLUSTER_NAME}"
    echo
    verbose_kind load docker-image --name "${KIND_CLUSTER_NAME}" "${AIRFLOW_PROD_IMAGE}"
}

function deploy_airflow_with_helm() {
    echo
    echo "Deploying Airflow with Helm"
    echo
    echo "Deleting namespace ${HELM_AIRFLOW_NAMESPACE}"
    verbose_kubectl delete namespace "${HELM_AIRFLOW_NAMESPACE}" >/dev/null 2>&1 || true
    verbose_kubectl create namespace "${HELM_AIRFLOW_NAMESPACE}"
    cd "${AIRFLOW_SOURCES}/chart" || exit 1
    verbose_helm repo add stable https://kubernetes-charts.storage.googleapis.com
    verbose_helm dep update
    verbose_helm install airflow . --namespace "${HELM_AIRFLOW_NAMESPACE}" \
        --set "defaultAirflowRepository=${DOCKERHUB_USER}/${DOCKERHUB_REPO}" \
        --set "defaultAirflowTag=${AIRFLOW_PROD_BASE_TAG}" -v 1
    echo

    verbose_kubectl port-forward svc/airflow-webserver 30809:8080 --namespace airflow >/dev/null &
}


function dump_kubernetes_logs() {
    POD=$(kubectl get pods -o go-template --template '{{range .items}}{{.metadata.name}}{{"\n"}}{{end}}' \
        --cluster "${KUBECTL_CLUSTER_NAME}" | grep airflow | head -1)
    echo "------- pod description -------"
    verbose_kubectl describe pod "${POD}" --cluster "${KUBECTL_CLUSTER_NAME}"
    echo "------- airflow pod logs -------"
    verbose_kubectl logs "${POD}" --all-containers=true || true
    echo "--------------"
}
