import os
import sys
import time

import pytest
import kopf.testing as kt
import kubernetes.client as k8s_client
import kubernetes.config as k8s_config

sys.path.insert(0, os.path.abspath(os.path.join(
    os.path.dirname(__file__), '../ur_operator')))

import ur_operator.crds as crds

k8s_config.load_kube_config()
core_api = k8s_client.CoreV1Api()

NAMESPACE = "ur-operator-testing"

def delete_namespace(name, timeout_seconds=20):
    core_api.delete_namespace(name)
    deadline = time.time() + timeout_seconds

    while time.time() < deadline:
        try:
            time.sleep(0.1)
            core_api.read_namespace_status(name)
        except k8s_client.rest.ApiException as e:
            if e.status == 404:
                return
            else:
                continue
        except:
            continue

    raise TimeoutError()

@pytest.fixture(scope='class')
def kopf_runner():
    with kt.KopfRunner(['run', '--standalone', '-A', 'ur_operator/handlers.py']) as runner:
        # wait for operator to start
        time.sleep(2)
        yield runner

@pytest.fixture(scope='class')
def kopf_runner_without_ingress_handling():
    os.environ['URO_DISABLE_INGRESS_HANDLING'] = '1'

    with kt.KopfRunner(['run', '--standalone', '-A', 'ur_operator/handlers.py']) as runner:
        # wait for operator to start
        time.sleep(2)
        yield runner

    os.environ.pop('URO_DISABLE_INGRESS_HANDLING')

@pytest.fixture()
def namespace_handling():
    core_api.create_namespace(k8s_client.V1Namespace(
        metadata=k8s_client.V1ObjectMeta(name=NAMESPACE),
    ))

    yield

    delete_namespace(NAMESPACE)

