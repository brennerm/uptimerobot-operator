import os
import sys
import time
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../ur_operator')))

from ur_operator.k8s import K8s
import ur_operator.crds as crds
import ur_operator.uptimerobot as uptimerobot

import uptimerobotpy as ur
import kubernetes.config as k8s_config
import kubernetes.client as k8s_client
import kopf.testing as kt
import pytest


NAMESPACE = "ur-operator-testing"

k8s = K8s()
k8s_config.load_kube_config()
core_api = k8s_client.CoreV1Api()
networking_api = k8s_client.NetworkingV1beta1Api()
uptime_robot = uptimerobot.create_uptimerobot_api()


def create_k8s_ur_monitor(namespace, name, wait_for_seconds=1, **spec):
    k8s.create_k8s_ur_monitor(namespace, name, **spec)
    time.sleep(wait_for_seconds)


def update_k8s_ur_monitor(namespace, name, wait_for_seconds=1, **spec):
    k8s.update_k8s_ur_monitor(namespace, name, **spec)
    time.sleep(wait_for_seconds)


def delete_k8s_ur_monitor(namespace, name, wait_for_seconds=1):
    k8s.delete_k8s_ur_monitor(namespace, name)
    time.sleep(wait_for_seconds)


def create_k8s_ingress(namespace, name, urls, wait_for_seconds=1):
    networking_api.create_namespaced_ingress(
        namespace,
        k8s_client.NetworkingV1beta1Ingress(
            api_version='networking.k8s.io/v1beta1',
            kind='Ingress',
            metadata=k8s_client.V1ObjectMeta(name=name),
            spec=k8s_client.NetworkingV1beta1IngressSpec(
                rules=[
                    k8s_client.NetworkingV1beta1IngressRule(
                        host=url
                    ) for url in urls
                ]
            )
        )
    )

    time.sleep(wait_for_seconds)


def update_k8s_ingress(namespace, name, urls, wait_for_seconds=1):
    networking_api.patch_namespaced_ingress(
        name,
        namespace,
        k8s_client.NetworkingV1beta1Ingress(
            api_version='networking.k8s.io/v1beta1',
            kind='Ingress',
            metadata=k8s_client.V1ObjectMeta(name=name),
            spec=k8s_client.NetworkingV1beta1IngressSpec(
                rules=[
                    k8s_client.NetworkingV1beta1IngressRule(
                        host=url
                    ) for url in urls
                ]
            )
        )
    )

    time.sleep(wait_for_seconds)


def delete_k8s_ingress(namespace, name, wait_for_seconds=1):
    networking_api.delete_namespaced_ingress(name, namespace)
    time.sleep(wait_for_seconds)


def delete_namespace(name, timeout_seconds=20):
    core_api.delete_namespace(NAMESPACE)
    deadline = time.time() + timeout_seconds

    while time.time() < deadline:
        try:
            time.sleep(0.1)
            status = core_api.read_namespace_status(name)
        except k8s_client.rest.ApiException as e:
            if e.status == 404:
                return
            else:
                continue
        except:
            continue

    raise TimeoutError()


@pytest.fixture(scope='session')
def kopf_runner():
    with kt.KopfRunner(['run', '--standalone', 'ur_operator/handlers.py']) as runner:
        # wait for operator to start
        time.sleep(2)
        yield runner


@pytest.fixture(autouse=True)
def namespace_handling(kopf_runner):
    core_api.create_namespace(k8s_client.V1Namespace(
        metadata=k8s_client.V1ObjectMeta(name=NAMESPACE),
    ))

    yield

    delete_namespace(NAMESPACE)


def test_create_monitor():
    name = 'foo'
    url = 'https://foo.com'
    monitor_type = crds.MonitorType.HTTP_HTTPS.name

    create_k8s_ur_monitor(NAMESPACE, name, type=monitor_type, url=url)

    monitors = uptime_robot.get_all_monitors()['monitors']
    assert len(monitors) == 1
    assert monitors[0]['friendly_name'] == name
    assert monitors[0]['url'] == url
    assert monitors[0]['type'] == crds.MonitorType.HTTP_HTTPS.value


def test_create_monitor_with_friendly_name():
    name = 'foo'
    friendly_name = "bar"
    url = 'https://foo.com'
    monitor_type = crds.MonitorType.HTTP_HTTPS.name

    create_k8s_ur_monitor(NAMESPACE, name, type=monitor_type,
                          url=url, friendlyName=friendly_name)

    monitors = uptime_robot.get_all_monitors()['monitors']
    assert len(monitors) == 1
    assert monitors[0]['friendly_name'] == friendly_name


def test_update_monitor():
    name = 'foo'
    new_name = 'bar'
    url = 'https://foo.com'
    monitor_type = crds.MonitorType.HTTP_HTTPS.name

    create_k8s_ur_monitor(NAMESPACE, name, type=monitor_type, url=url)

    monitors = uptime_robot.get_all_monitors()['monitors']
    assert len(monitors) == 1
    assert monitors[0]['friendly_name'] == name

    update_k8s_ur_monitor(NAMESPACE, name, friendlyName=new_name)

    monitors = uptime_robot.get_all_monitors()['monitors']
    assert len(monitors) == 1
    assert monitors[0]['friendly_name'] == new_name


def test_update_monitor_type():
    name = 'foo'
    url = 'https://foo.com'
    monitor_type = crds.MonitorType.HTTP_HTTPS.name
    new_monitor_type = crds.MonitorType.PING.name

    create_k8s_ur_monitor(NAMESPACE, name, type=monitor_type, url=url)

    monitors = uptime_robot.get_all_monitors()['monitors']
    assert len(monitors) == 1
    assert monitors[0]['type'] == crds.MonitorType.HTTP_HTTPS.value

    update_k8s_ur_monitor(NAMESPACE, name, type=new_monitor_type)

    monitors = uptime_robot.get_all_monitors()['monitors']
    assert len(monitors) == 1
    assert monitors[0]['type'] == crds.MonitorType.PING.value


def test_delete_monitor():
    name = 'foo'
    url = 'https://foo.com'
    monitor_type = crds.MonitorType.HTTP_HTTPS.name

    create_k8s_ur_monitor(NAMESPACE, name, type=monitor_type, url=url)

    monitors = uptime_robot.get_all_monitors()['monitors']
    assert len(monitors) == 1

    delete_k8s_ur_monitor(NAMESPACE, name)

    monitors = uptime_robot.get_all_monitors()['monitors']
    assert len(monitors) == 0


def test_create_ingress():
    name = 'foo'
    url = 'foo.com'

    create_k8s_ingress(NAMESPACE, name, [url])

    monitors = uptime_robot.get_all_monitors()['monitors']
    assert len(monitors) == 1
    assert monitors[0]['friendly_name'].startswith(name)
    assert monitors[0]['url'] == url
    assert monitors[0]['type'] == crds.MonitorType.PING.value


def test_update_ingress_add_host():
    name = 'foo'
    url1 = 'foo.com'
    url2 = 'bar.com'

    create_k8s_ingress(NAMESPACE, name, [url1])

    monitors = uptime_robot.get_all_monitors()['monitors']
    assert len(monitors) == 1

    update_k8s_ingress(NAMESPACE, name, [url1, url2])

    monitors = uptime_robot.get_all_monitors()['monitors']
    assert len(monitors) == 2


def test_update_ingress_remove_host():
    name = 'foo'
    url1 = 'foo.com'
    url2 = 'bar.com'

    create_k8s_ingress(NAMESPACE, name, [url1, url2])

    monitors = uptime_robot.get_all_monitors()['monitors']
    assert len(monitors) == 2

    update_k8s_ingress(NAMESPACE, name, [url1])

    monitors = uptime_robot.get_all_monitors()['monitors']
    assert len(monitors) == 1


def test_delete_ingress():
    name = 'foo'
    url = 'foo.com'

    create_k8s_ingress(NAMESPACE, name, [url])

    monitors = uptime_robot.get_all_monitors()['monitors']
    assert len(monitors) == 1

    delete_k8s_ingress(NAMESPACE, name)

    monitors = uptime_robot.get_all_monitors()['monitors']
    assert len(monitors) == 0
