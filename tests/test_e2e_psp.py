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


def create_k8s_ur_psp(namespace, name, wait_for_seconds=DEFAULT_WAIT_TIME, **spec):
    k8s.create_k8s_crd_obj(crds.PspV1Beta1, namespace, name, **spec)
    time.sleep(wait_for_seconds)


def update_k8s_ur_psp(namespace, name, wait_for_seconds=DEFAULT_WAIT_TIME, **spec):
    k8s.update_k8s_crd_obj(crds.PspV1Beta1, namespace, name, **spec)
    time.sleep(wait_for_seconds)


def delete_k8s_ur_psp(namespace, name, wait_for_seconds=DEFAULT_WAIT_TIME):
    k8s.delete_k8s_crd_obj(crds.PspV1Beta1, namespace, name)
    time.sleep(wait_for_seconds)


class TestDefaultOperator:
    def test_create_psp(self, kopf_runner, namespace_handling):
        name = 'foo'
        monitors = '0'
        password = 's3cr3t'
        sort = crds.PspSort.STATUS_DOWN_UP_PAUSED

        create_k8s_ur_psp(NAMESPACE, name, monitors=monitors, password=password, sort=sort.name)

        psps = uptime_robot.get_psp()['psps']
        assert len(psps) == 1
        assert psps[0]['friendly_name'] == name
        assert psps[0]['monitors'] == 0
        assert psps[0]['sort'] == sort.value

    def test_create_psp_with_friendly_name(self, kopf_runner, namespace_handling):
        name = 'foo'
        friendly_name = 'bar'
        monitors = '0'

        create_k8s_ur_psp(NAMESPACE, name, friendlyName=friendly_name, monitors=monitors)

        psps = uptime_robot.get_psp()['psps']
        assert len(psps) == 1
        assert psps[0]['friendly_name'] == friendly_name
        assert psps[0]['monitors'] == 0

    @pytest.mark.skip(reason='not able to test pro features')
    def test_create_psp_with_hidden_url_links(self, kopf_runner, namespace_handling):
        name = 'foo'
        monitors = '0'
        hiddenUrlLinks = True

        create_k8s_ur_psp(NAMESPACE, name, monitors=monitors, hiddenUrlLinks=hiddenUrlLinks)

        psps = uptime_robot.get_psp()['psps']
        assert len(psps) == 1
        assert psps[0]['friendly_name'] == name
        assert psps[0]['monitors'] == 0
        assert psps[0]['hidden_url_links'] == hiddenUrlLinks

    def test_update_psp(self, kopf_runner, namespace_handling):
        name = 'foo'
        new_name = 'bar'
        monitors = '0'

        create_k8s_ur_psp(NAMESPACE, name, monitors=monitors)

        psps = uptime_robot.get_psp()['psps']
        assert len(psps) == 1
        assert psps[0]['friendly_name'] == name

        update_k8s_ur_psp(NAMESPACE, name, friendlyName=new_name)

        psps = uptime_robot.get_psp()['psps']
        assert len(psps) == 1
        assert psps[0]['friendly_name'] == new_name

    def test_delete_psp(self, kopf_runner, namespace_handling):
        name = 'foo'
        monitors = '0'

        create_k8s_ur_psp(NAMESPACE, name, monitors=monitors)

        psps = uptime_robot.get_psp()['psps']
        assert len(psps) == 1

        delete_k8s_ur_psp(NAMESPACE, name)

        psps = uptime_robot.get_psp()['psps']
        assert len(psps) == 0
