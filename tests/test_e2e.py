import pytest
import kopf.testing as kt
import kubernetes.client as k8s_client
import kubernetes.config as k8s_config
import sys

import os
import time
sys.path.insert(0, os.path.abspath(os.path.join(
    os.path.dirname(__file__), '../ur_operator')))


import ur_operator.uptimerobot as uptimerobot
import ur_operator.crds as crds
from ur_operator.k8s import K8s

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


class TestDefaultOperator:
    @staticmethod
    @pytest.fixture(scope='class')
    def kopf_runner():
        with kt.KopfRunner(['run', '--standalone', '-A', 'ur_operator/handlers.py']) as runner:
            # wait for operator to start
            time.sleep(2)
            yield runner

    @staticmethod
    @pytest.fixture(autouse=True)
    def namespace_handling(kopf_runner):
        core_api.create_namespace(k8s_client.V1Namespace(
            metadata=k8s_client.V1ObjectMeta(name=NAMESPACE),
        ))

        yield

        delete_namespace(NAMESPACE)

    def test_create_monitor(self):
        name = 'foo'
        url = 'https://foo.com'
        monitor_type = crds.MonitorType.HTTP_HTTPS
        interval = 600

        create_k8s_ur_monitor(NAMESPACE, name, type=monitor_type.name, url=url, interval=interval)

        monitors = uptime_robot.get_all_monitors()['monitors']
        assert len(monitors) == 1
        assert monitors[0]['friendly_name'] == name
        assert monitors[0]['url'] == url
        assert monitors[0]['type'] == monitor_type.value
        assert monitors[0]['interval'] == interval

    def test_create_monitor_with_friendly_name(self):
        name = 'foo'
        friendly_name = 'bar'
        url = 'https://foo.com'
        monitor_type = crds.MonitorType.HTTP_HTTPS

        create_k8s_ur_monitor(NAMESPACE, name, type=monitor_type.name,
                              url=url, friendlyName=friendly_name)

        monitors = uptime_robot.get_all_monitors()['monitors']
        assert len(monitors) == 1
        assert monitors[0]['friendly_name'] == friendly_name

    def test_create_http_monitor_with_basic_auth(self):
        name = 'foo'
        url = 'https://foo.com'
        monitor_type = crds.MonitorType.HTTP_HTTPS
        http_auth_type = crds.MonitorHttpAuthType.BASIC_AUTH
        username = 'foo'
        password = 'bar'

        create_k8s_ur_monitor(NAMESPACE, name, type=monitor_type.name, url=url, httpAuthType=http_auth_type.name, httpUsername=username, httpPassword=password)

        monitors = uptime_robot.get_all_monitors()['monitors']
        assert len(monitors) == 1
        assert monitors[0]['friendly_name'] == name
        assert monitors[0]['url'] == url
        assert monitors[0]['type'] == monitor_type.value
        assert monitors[0]['http_username'] == username
        assert monitors[0]['http_password'] == password

    def test_create_http_monitor_with_digest_auth(self):
        name = 'foo'
        url = 'https://foo.com'
        monitor_type = crds.MonitorType.HTTP_HTTPS
        http_auth_type = crds.MonitorHttpAuthType.DIGEST
        username = 'foo'
        password = 'bar'

        create_k8s_ur_monitor(NAMESPACE, name, type=monitor_type.name, url=url, httpAuthType=http_auth_type.name, httpUsername=username, httpPassword=password)

        monitors = uptime_robot.get_all_monitors()['monitors']
        assert len(monitors) == 1
        assert monitors[0]['friendly_name'] == name
        assert monitors[0]['url'] == url
        assert monitors[0]['type'] == monitor_type.value
        assert monitors[0]['http_username'] == username
        assert monitors[0]['http_password'] == password

    def test_create_ping_monitor(self):
        name = 'foo'
        url = 'https://foo.com'
        monitor_type = crds.MonitorType.PING

        create_k8s_ur_monitor(NAMESPACE, name, type=monitor_type.name, url=url)

        monitors = uptime_robot.get_all_monitors()['monitors']
        assert len(monitors) == 1
        assert monitors[0]['friendly_name'] == name
        assert monitors[0]['url'] == url
        assert monitors[0]['type'] == monitor_type.value

    def test_create_port_monitor(self):
        name = 'foo'
        url = 'https://foo.com'
        monitor_type = crds.MonitorType.PORT
        monitor_sub_type = crds.MonitorSubType.HTTP

        create_k8s_ur_monitor(NAMESPACE, name, type=monitor_type.name, url=url, subType=monitor_sub_type.name)

        monitors = uptime_robot.get_all_monitors()['monitors']
        assert len(monitors) == 1
        assert monitors[0]['friendly_name'] == name
        assert monitors[0]['url'] == url
        assert monitors[0]['type'] == monitor_type.value
        assert monitors[0]['sub_type'] == monitor_sub_type.value

    def test_create_custom_port_monitor(self):
        name = 'foo'
        url = 'https://foo.com'
        monitor_type = crds.MonitorType.PORT
        monitor_sub_type = crds.MonitorSubType.CUSTOM
        port = 1234

        create_k8s_ur_monitor(NAMESPACE, name, type=monitor_type.name, url=url, subType=monitor_sub_type.name, port=port)

        monitors = uptime_robot.get_all_monitors()['monitors']
        assert len(monitors) == 1
        assert monitors[0]['friendly_name'] == name
        assert monitors[0]['url'] == url
        assert monitors[0]['type'] == monitor_type.value
        assert monitors[0]['sub_type'] == monitor_sub_type.value
        assert monitors[0]['port'] == port

    def test_create_keyword_monitor(self):
        name = 'foo'
        url = 'https://foo.com'
        monitor_type = crds.MonitorType.KEYWORD
        keyword_type = crds.MonitorKeywordType.EXISTS
        keyword_value = 'foo'

        create_k8s_ur_monitor(NAMESPACE, name, type=monitor_type.name, url=url, keywordType=keyword_type.name, keywordValue=keyword_value)

        monitors = uptime_robot.get_all_monitors()['monitors']
        assert len(monitors) == 1
        assert monitors[0]['friendly_name'] == name
        assert monitors[0]['url'] == url
        assert monitors[0]['type'] == monitor_type.value
        assert monitors[0]['keyword_type'] == keyword_type.value
        assert monitors[0]['keyword_value'] == keyword_value

    @pytest.mark.skip(reason='not able to test pro features')
    def test_create_heartbeat_monitor(self):
        name = 'foo'
        url = 'https://foo.com'
        monitor_type = crds.MonitorType.HEARTBEAT

        create_k8s_ur_monitor(NAMESPACE, name, type=monitor_type.name, url=url)

        monitors = uptime_robot.get_all_monitors()['monitors']
        assert len(monitors) == 1
        assert monitors[0]['friendly_name'] == name
        assert monitors[0]['url'] == url
        assert monitors[0]['type'] == monitor_type.value

    def test_update_monitor(self):
        name = 'foo'
        new_name = 'bar'
        url = 'https://foo.com'
        monitor_type = crds.MonitorType.HTTP_HTTPS

        create_k8s_ur_monitor(NAMESPACE, name, type=monitor_type.name, url=url)

        monitors = uptime_robot.get_all_monitors()['monitors']
        assert len(monitors) == 1
        assert monitors[0]['friendly_name'] == name

        update_k8s_ur_monitor(NAMESPACE, name, friendlyName=new_name)

        monitors = uptime_robot.get_all_monitors()['monitors']
        assert len(monitors) == 1
        assert monitors[0]['friendly_name'] == new_name

    def test_update_monitor_type(self):
        name = 'foo'
        url = 'https://foo.com'
        monitor_type = crds.MonitorType.HTTP_HTTPS
        new_monitor_type = crds.MonitorType.PING

        create_k8s_ur_monitor(NAMESPACE, name, type=monitor_type.name, url=url)

        monitors = uptime_robot.get_all_monitors()['monitors']
        assert len(monitors) == 1
        assert monitors[0]['type'] == monitor_type.value

        update_k8s_ur_monitor(NAMESPACE, name, type=new_monitor_type.name)

        monitors = uptime_robot.get_all_monitors()['monitors']
        assert len(monitors) == 1
        assert monitors[0]['type'] == new_monitor_type.value

    def test_delete_monitor(self):
        name = 'foo'
        url = 'https://foo.com'
        monitor_type = crds.MonitorType.HTTP_HTTPS

        create_k8s_ur_monitor(NAMESPACE, name, type=monitor_type.name, url=url)

        monitors = uptime_robot.get_all_monitors()['monitors']
        assert len(monitors) == 1

        delete_k8s_ur_monitor(NAMESPACE, name)

        monitors = uptime_robot.get_all_monitors()['monitors']
        assert len(monitors) == 0

    def test_create_ingress(self):
        name = 'foo'
        url = 'foo.com'

        create_k8s_ingress(NAMESPACE, name, [url])

        monitors = uptime_robot.get_all_monitors()['monitors']
        assert len(monitors) == 1
        assert monitors[0]['friendly_name'].startswith(name)
        assert monitors[0]['url'] == url
        assert monitors[0]['type'] == crds.MonitorType.PING.value

    def test_update_ingress_add_host(self):
        name = 'foo'
        url1 = 'foo.com'
        url2 = 'bar.com'

        create_k8s_ingress(NAMESPACE, name, [url1])

        monitors = uptime_robot.get_all_monitors()['monitors']
        assert len(monitors) == 1

        update_k8s_ingress(NAMESPACE, name, [url1, url2])

        monitors = uptime_robot.get_all_monitors()['monitors']
        assert len(monitors) == 2

    def test_update_ingress_remove_host(self):
        name = 'foo'
        url1 = 'foo.com'
        url2 = 'bar.com'

        create_k8s_ingress(NAMESPACE, name, [url1, url2])

        monitors = uptime_robot.get_all_monitors()['monitors']
        assert len(monitors) == 2

        update_k8s_ingress(NAMESPACE, name, [url1])

        monitors = uptime_robot.get_all_monitors()['monitors']
        assert len(monitors) == 1

    def test_delete_ingress(self):
        name = 'foo'
        url = 'foo.com'

        create_k8s_ingress(NAMESPACE, name, [url])

        monitors = uptime_robot.get_all_monitors()['monitors']
        assert len(monitors) == 1

        delete_k8s_ingress(NAMESPACE, name)

        monitors = uptime_robot.get_all_monitors()['monitors']
        assert len(monitors) == 0


class TestOperatorWithoutIngressHandling:
    @staticmethod
    @pytest.fixture(scope='class')
    def kopf_runner_without_ingress_handling():
        os.environ['URO_DISABLE_INGRESS_HANDLING'] = '1'

        with kt.KopfRunner(['run', '--standalone', '-A', 'ur_operator/handlers.py']) as runner:
            # wait for operator to start
            time.sleep(2)
            yield runner

        os.environ.pop('URO_DISABLE_INGRESS_HANDLING')

    @staticmethod
    @pytest.fixture(autouse=True)
    def namespace_handling(kopf_runner_without_ingress_handling):
        core_api.create_namespace(k8s_client.V1Namespace(
            metadata=k8s_client.V1ObjectMeta(name=NAMESPACE),
        ))

        yield

        delete_namespace(NAMESPACE)

    def test_create_ingress(self):
        name = 'foo'
        url = 'foo.com'

        create_k8s_ingress(NAMESPACE, name, [url])

        monitors = uptime_robot.get_all_monitors()['monitors']
        assert len(monitors) == 0

    def test_update_ingress_add_host(self):
        name = 'foo'
        url1 = 'foo.com'
        url2 = 'bar.com'

        create_k8s_ingress(NAMESPACE, name, [url1])

        monitors = uptime_robot.get_all_monitors()['monitors']
        assert len(monitors) == 0

        update_k8s_ingress(NAMESPACE, name, [url1, url2])

        monitors = uptime_robot.get_all_monitors()['monitors']
        assert len(monitors) == 0
