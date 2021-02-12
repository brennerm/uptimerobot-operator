import pytest
import kopf.testing as kt
import kubernetes.client as k8s_client
import kubernetes.config as k8s_config
import sys

from .utils import namespace_handling, kopf_runner, kopf_runner_without_ingress_handling, NAMESPACE, DEFAULT_WAIT_TIME

import os
import time
sys.path.insert(0, os.path.abspath(os.path.join(
    os.path.dirname(__file__), '../ur_operator')))


import ur_operator.uptimerobot as uptimerobot
import ur_operator.crds as crds
from ur_operator.k8s import K8s

k8s_config.load_kube_config()
networking_api = k8s_client.NetworkingV1beta1Api()
uptime_robot = uptimerobot.create_uptimerobot_api()

def create_k8s_ingress(namespace, name, urls, annotations={}, wait_for_seconds=DEFAULT_WAIT_TIME):
    networking_api.create_namespaced_ingress(
        namespace,
        k8s_client.NetworkingV1beta1Ingress(
            api_version='networking.k8s.io/v1beta1',
            kind='Ingress',
            metadata=k8s_client.V1ObjectMeta(
                name=name,
                annotations={f'{crds.GROUP}/{k}': v for k,v in annotations.items()}
                ),
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


def update_k8s_ingress(namespace, name, urls, annotations={}, wait_for_seconds=DEFAULT_WAIT_TIME):
    networking_api.patch_namespaced_ingress(
        name,
        namespace,
        k8s_client.NetworkingV1beta1Ingress(
            api_version='networking.k8s.io/v1beta1',
            kind='Ingress',
            metadata=k8s_client.V1ObjectMeta(
                name=name,
                annotations={f'{crds.GROUP}/{k}': v for k,v in annotations.items()}
            ),
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


def delete_k8s_ingress(namespace, name, wait_for_seconds=DEFAULT_WAIT_TIME):
    networking_api.delete_namespaced_ingress(name, namespace)
    time.sleep(wait_for_seconds)


class TestDefaultOperator:
    def test_create_default_ingress(self, namespace_handling, kopf_runner):
        name = 'foo'
        url = 'foo.com'

        create_k8s_ingress(NAMESPACE, name, [url])

        monitors = uptime_robot.get_all_monitors()['monitors']
        assert len(monitors) == 1
        assert monitors[0]['friendly_name'].startswith(name)
        assert monitors[0]['url'] == url
        assert monitors[0]['type'] == crds.MonitorType.PING.value

    def test_create_http_ingress(self, namespace_handling, kopf_runner):
        name = 'foo'
        url = 'foo.com'
        monitor_type = crds.MonitorType.HTTP

        create_k8s_ingress(NAMESPACE, name, [url], {'monitor.type': 'HTTP'})

        monitors = uptime_robot.get_all_monitors()['monitors']
        assert len(monitors) == 1
        assert monitors[0]['friendly_name'].startswith(name)
        assert monitors[0]['url'] == f'http://{url}'
        assert monitors[0]['type'] == monitor_type.value

    def test_create_https_ingress(self, namespace_handling, kopf_runner):
        name = 'foo'
        url = 'foo.com'
        monitor_type = crds.MonitorType.HTTPS

        create_k8s_ingress(NAMESPACE, name, [url], {'monitor.type': 'HTTPS'})

        monitors = uptime_robot.get_all_monitors()['monitors']
        assert len(monitors) == 1
        assert monitors[0]['friendly_name'].startswith(name)
        assert monitors[0]['url'] == f'https://{url}'
        assert monitors[0]['type'] == monitor_type.value

    def test_create_ingress_with_basic_auth(self, namespace_handling, kopf_runner):
        name = 'foo'
        url = 'foo.com'
        username = 'foo'
        password = 'bar'

        create_k8s_ingress(NAMESPACE, name, [url], {
            'monitor.type': 'HTTP',
            'monitor.httpUsername': username,
            'monitor.httpPassword': password,
            'monitor.httpAuthType': crds.MonitorHttpAuthType.BASIC_AUTH.name
        })

        monitors = uptime_robot.get_all_monitors()['monitors']
        assert len(monitors) == 1
        assert monitors[0]['http_username'] == username
        assert monitors[0]['http_password'] == password

    def test_create_ingress_with_digest(self, namespace_handling, kopf_runner):
        name = 'foo'
        url = 'foo.com'
        username = 'foo'
        password = 'bar'

        create_k8s_ingress(NAMESPACE, name, [url], {
            'monitor.type': 'HTTP',
            'monitor.httpUsername': username,
            'monitor.httpPassword': password,
            'monitor.httpAuthType': crds.MonitorHttpAuthType.DIGEST.name
        })

        monitors = uptime_robot.get_all_monitors()['monitors']
        assert len(monitors) == 1
        assert monitors[0]['http_username'] == username
        assert monitors[0]['http_password'] == password

    def test_update_ingress_add_host(self, namespace_handling, kopf_runner):
        name = 'foo'
        url1 = 'foo.com'
        url2 = 'bar.com'

        create_k8s_ingress(NAMESPACE, name, [url1])

        monitors = uptime_robot.get_all_monitors()['monitors']
        assert len(monitors) == 1

        update_k8s_ingress(NAMESPACE, name, [url1, url2])

        monitors = uptime_robot.get_all_monitors()['monitors']
        assert len(monitors) == 2

    def test_update_ingress_remove_host(self, namespace_handling, kopf_runner):
        name = 'foo'
        url1 = 'foo.com'
        url2 = 'bar.com'

        create_k8s_ingress(NAMESPACE, name, [url1, url2])

        monitors = uptime_robot.get_all_monitors()['monitors']
        assert len(monitors) == 2

        update_k8s_ingress(NAMESPACE, name, [url1])

        monitors = uptime_robot.get_all_monitors()['monitors']
        assert len(monitors) == 1

    def test_update_ingress_change_interval(self, namespace_handling, kopf_runner):
        name = 'foo'
        url = 'foo.com'
        interval = 600
        new_interval = 1200

        create_k8s_ingress(NAMESPACE, name, [url], {'monitor.interval': str(interval)})

        monitors = uptime_robot.get_all_monitors()['monitors']
        assert len(monitors) == 1
        assert monitors[0]['interval'] == interval


        update_k8s_ingress(NAMESPACE, name, [url], {'monitor.interval': str(new_interval)})

        monitors = uptime_robot.get_all_monitors()['monitors']
        assert len(monitors) == 1
        assert monitors[0]['interval'] == new_interval

    def test_update_ingress_change_type(self, namespace_handling, kopf_runner):
        name = 'foo'
        url = 'foo.com'
        monitor_type = crds.MonitorType.HTTP
        new_monitor_type = crds.MonitorType.PING

        create_k8s_ingress(NAMESPACE, name, [url], {'monitor.type': monitor_type.name})

        monitors = uptime_robot.get_all_monitors()['monitors']
        assert len(monitors) == 1
        assert monitors[0]['type'] == monitor_type.value


        update_k8s_ingress(NAMESPACE, name, [url], {'monitor.type': new_monitor_type.name})

        monitors = uptime_robot.get_all_monitors()['monitors']
        assert len(monitors) == 1
        assert monitors[0]['type'] == new_monitor_type.value

    def test_delete_ingress(self, namespace_handling, kopf_runner):
        name = 'foo'
        url = 'foo.com'

        create_k8s_ingress(NAMESPACE, name, [url])

        monitors = uptime_robot.get_all_monitors()['monitors']
        assert len(monitors) == 1

        delete_k8s_ingress(NAMESPACE, name)

        monitors = uptime_robot.get_all_monitors()['monitors']
        assert len(monitors) == 0


class TestOperatorWithoutIngressHandling:
    def test_create_ingress(self, namespace_handling, kopf_runner_without_ingress_handling):
        name = 'foo'
        url = 'foo.com'

        create_k8s_ingress(NAMESPACE, name, [url])

        monitors = uptime_robot.get_all_monitors()['monitors']
        assert len(monitors) == 0

    def test_update_ingress_add_host(self, namespace_handling, kopf_runner_without_ingress_handling):
        name = 'foo'
        url1 = 'foo.com'
        url2 = 'bar.com'

        create_k8s_ingress(NAMESPACE, name, [url1])

        monitors = uptime_robot.get_all_monitors()['monitors']
        assert len(monitors) == 0

        update_k8s_ingress(NAMESPACE, name, [url1, url2])

        monitors = uptime_robot.get_all_monitors()['monitors']
        assert len(monitors) == 0
