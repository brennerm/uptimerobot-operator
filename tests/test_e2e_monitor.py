import pytest
import kubernetes.client as k8s_client
import kubernetes.config as k8s_config
import sys

from .utils import namespace_handling, kopf_runner, NAMESPACE, DEFAULT_WAIT_TIME

import os
import time
sys.path.insert(0, os.path.abspath(os.path.join(
    os.path.dirname(__file__), '../ur_operator')))


import ur_operator.uptimerobot as uptimerobot
import ur_operator.crds as crds
from ur_operator.k8s import K8s


k8s = K8s()
k8s_config.load_kube_config()
core_api = k8s_client.CoreV1Api()
uptime_robot = uptimerobot.create_uptimerobot_api()


def create_k8s_ur_monitor(namespace, name, wait_for_seconds=DEFAULT_WAIT_TIME, **spec):
    k8s.create_k8s_crd_obj(crds.MonitorV1Beta1, namespace, name, **spec)
    time.sleep(wait_for_seconds)


def update_k8s_ur_monitor(namespace, name, wait_for_seconds=DEFAULT_WAIT_TIME, **spec):
    k8s.update_k8s_crd_obj(crds.MonitorV1Beta1, namespace, name, **spec)
    time.sleep(wait_for_seconds)


def delete_k8s_ur_monitor(namespace, name, wait_for_seconds=DEFAULT_WAIT_TIME):
    k8s.delete_k8s_crd_obj(crds.MonitorV1Beta1, namespace, name)
    time.sleep(wait_for_seconds)


class TestDefaultOperator:
    def test_create_monitor(self, kopf_runner, namespace_handling):
        name = 'foo'
        url = 'https://foo.com'
        monitor_type = crds.MonitorType.HTTPS
        interval = 600

        create_k8s_ur_monitor(NAMESPACE, name, type=monitor_type.name, url=url, interval=interval)

        monitors = uptime_robot.get_all_monitors()['monitors']
        assert len(monitors) == 1
        assert monitors[0]['friendly_name'] == name
        assert monitors[0]['url'] == url
        assert monitors[0]['type'] == monitor_type.value
        assert monitors[0]['interval'] == interval

    def test_create_monitor_with_friendly_name(self, kopf_runner, namespace_handling):
        name = 'foo'
        friendly_name = 'bar'
        url = 'https://foo.com'
        monitor_type = crds.MonitorType.HTTPS

        create_k8s_ur_monitor(NAMESPACE, name, type=monitor_type.name,
                              url=url, friendlyName=friendly_name)

        monitors = uptime_robot.get_all_monitors()['monitors']
        assert len(monitors) == 1
        assert monitors[0]['friendly_name'] == friendly_name

    def test_create_http_monitor_with_basic_auth(self, kopf_runner, namespace_handling):
        name = 'foo'
        url = 'https://foo.com'
        monitor_type = crds.MonitorType.HTTPS
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

    def test_create_http_monitor_with_digest_auth(self, kopf_runner, namespace_handling):
        name = 'foo'
        url = 'https://foo.com'
        monitor_type = crds.MonitorType.HTTPS
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

    def test_create_ping_monitor(self, kopf_runner, namespace_handling):
        name = 'foo'
        url = 'https://foo.com'
        monitor_type = crds.MonitorType.PING

        create_k8s_ur_monitor(NAMESPACE, name, type=monitor_type.name, url=url)

        monitors = uptime_robot.get_all_monitors()['monitors']
        assert len(monitors) == 1
        assert monitors[0]['friendly_name'] == name
        assert monitors[0]['url'] == url
        assert monitors[0]['type'] == monitor_type.value

    def test_create_port_monitor(self, kopf_runner, namespace_handling):
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

    def test_create_custom_port_monitor(self, kopf_runner, namespace_handling):
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

    def test_create_keyword_monitor(self, kopf_runner, namespace_handling):
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
    def test_create_heartbeat_monitor(self, kopf_runner, namespace_handling):
        name = 'foo'
        url = 'https://foo.com'
        monitor_type = crds.MonitorType.HEARTBEAT

        create_k8s_ur_monitor(NAMESPACE, name, type=monitor_type.name, url=url)

        monitors = uptime_robot.get_all_monitors()['monitors']
        assert len(monitors) == 1
        assert monitors[0]['friendly_name'] == name
        assert monitors[0]['url'] == url
        assert monitors[0]['type'] == monitor_type.value

    def test_update_monitor(self, kopf_runner, namespace_handling):
        name = 'foo'
        new_name = 'bar'
        interval = 600
        new_interval = 1200
        url = 'https://foo.com'
        monitor_type = crds.MonitorType.HTTPS

        create_k8s_ur_monitor(NAMESPACE, name, type=monitor_type.name, url=url, interval=interval)

        monitors = uptime_robot.get_all_monitors()['monitors']
        assert len(monitors) == 1
        assert monitors[0]['friendly_name'] == name
        assert monitors[0]['interval'] == interval

        update_k8s_ur_monitor(NAMESPACE, name, friendlyName=new_name, interval=new_interval)

        monitors = uptime_robot.get_all_monitors()['monitors']
        assert len(monitors) == 1
        assert monitors[0]['friendly_name'] == new_name
        assert monitors[0]['interval'] == new_interval

    def test_update_monitor_type(self, kopf_runner, namespace_handling):
        name = 'foo'
        url = 'https://foo.com'
        monitor_type = crds.MonitorType.HTTPS
        new_monitor_type = crds.MonitorType.PING

        create_k8s_ur_monitor(NAMESPACE, name, type=monitor_type.name, url=url)

        monitors = uptime_robot.get_all_monitors()['monitors']
        assert len(monitors) == 1
        assert monitors[0]['type'] == monitor_type.value

        update_k8s_ur_monitor(NAMESPACE, name, type=new_monitor_type.name)

        monitors = uptime_robot.get_all_monitors()['monitors']
        assert len(monitors) == 1
        assert monitors[0]['type'] == new_monitor_type.value

    def test_delete_monitor(self, kopf_runner, namespace_handling):
        name = 'foo'
        url = 'https://foo.com'
        monitor_type = crds.MonitorType.HTTPS

        create_k8s_ur_monitor(NAMESPACE, name, type=monitor_type.name, url=url)

        monitors = uptime_robot.get_all_monitors()['monitors']
        assert len(monitors) == 1

        delete_k8s_ur_monitor(NAMESPACE, name)

        monitors = uptime_robot.get_all_monitors()['monitors']
        assert len(monitors) == 0
