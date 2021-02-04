import kubernetes.config as k8s_config
import kubernetes.client as k8s_client
import kopf

import crds
from k8s import K8s
import uptimerobot
from config import Config

MONITOR_ID_KEY = 'monitor_id'

config = Config()
uptime_robot = None
k8s = None


def create_crds(logger):
    try:
        k8s_config.load_kube_config()
    except k8s_config.ConfigException:
        k8s_config.load_incluster_config()

    api_instance = k8s_client.ApiextensionsV1Api()
    try:
        api_instance.create_custom_resource_definition(crds.MonitorV1Beta1.crd)
        logger.info('CRDs successfully created')
    except k8s_client.rest.ApiException as error:
        if error.status == 409:
            api_instance.patch_custom_resource_definition(
                name=crds.MonitorV1Beta1.crd.metadata.name, body=crds.MonitorV1Beta1.crd)
            logger.debug('CRDs successfully patched')
        else:
            logger.error('CRD creation failed')
            raise error


def init_uptimerobot_api(logger):
    global uptime_robot
    try:
        uptime_robot = uptimerobot.create_uptimerobot_api()
    except Exception as error:
        logger.error('failed to create UptimeRobot API')
        raise kopf.PermanentError(error)


def create_monitor(logger, **kwargs):
    resp = uptime_robot.new_monitor(**kwargs)

    if resp['stat'] == 'ok':
        identifier = resp['monitor']['id']
        logger.info(
            f'monitor with ID {identifier} has been created successfully')
        return identifier

    raise kopf.PermanentError(f'failed to create monitor: {resp["error"]}')


def update_monitor(logger, identifier, **kwargs):
    resp = uptime_robot.edit_monitor(identifier, **kwargs)

    if resp['stat'] == 'ok':
        identifier = resp['monitor']['id']
        logger.info(
            f'monitor with ID {identifier} has been updated successfully')
        return identifier

    raise kopf.PermanentError(f'failed to update monitor with ID {identifier}: {resp["error"]}')


def delete_monitor(logger, identifier):
    resp = uptime_robot.delete_monitor(identifier)
    if resp['stat'] == 'ok':
        logger.info(
            f'monitor with ID {identifier} has been deleted successfully')
    else:
        if resp['error']['type'] == 'not_found':
            logger.info(
                f'monitor with ID {identifier} has already been deleted')
            return

        raise kopf.PermanentError(
            f'failed to delete monitor with ID {identifier}: {resp["error"]}')


def monitor_type_changed(diff: list):
    try:
        for entry in diff:
            if entry[0] == 'change' and entry[1][1] == 'type':
                return True
    except IndexError:
        return False
    return False


def get_identifier(status: dict):
    if on_update.__name__ in status:
        return status[on_update.__name__][MONITOR_ID_KEY]

    if on_create.__name__ in status:
        return status[on_create.__name__][MONITOR_ID_KEY]

    raise KeyError(MONITOR_ID_KEY)


@kopf.on.startup()
def startup(logger, **_):
    if(config.DISABLE_INGRESS_HANDLING):
        logger.info('handling of Ingress resources has been disabled')
    global k8s
    k8s = K8s()
    init_uptimerobot_api(logger)
    create_crds(logger)


@kopf.on.create(crds.GROUP, crds.MonitorV1Beta1.version, crds.MonitorV1Beta1.plural)
def on_create(name: str, spec: dict, logger, **_):
    friendly_name = spec.get('friendlyName', name)
    identifier = create_monitor(
        logger,
        friendly_name=friendly_name,
        url=spec['url'],
        type=crds.MonitorType[spec['type']].value
    )

    return {MONITOR_ID_KEY: identifier}


@kopf.on.create('networking.k8s.io', 'v1', 'ingresses')
def on_ingress_create(name: str, namespace: str, spec: dict, logger, **_):
    if config.DISABLE_INGRESS_HANDLING:
        logger.info('handling of Ingress resources has been disabled')
        return

    index = 0
    for rule in spec['rules']:
        if 'host' not in rule:
            continue

        url = rule['host']

        monitor_body = K8s.construct_k8s_ur_monitor_body(
            namespace, name=f"{name}-{index}", url=url, type=crds.MonitorType.PING.name)
        kopf.adopt(monitor_body)

        k8s.create_k8s_ur_monitor_with_body(namespace, monitor_body)
        logger.info(f'created new UptimeRobotMonitor object for URL {url}')
        index += 1


@kopf.on.update('networking.k8s.io', 'v1', 'ingresses')
def on_ingress_update(name: str, namespace: str, spec: dict, diff: list, logger, **_):
    if config.DISABLE_INGRESS_HANDLING:
        logger.info('handling of Ingress resources has been disabled')
        return

    previous_rule_count = len(diff[0][2])
    index = 0

    for rule in spec['rules']:
        if 'host' not in rule:
            continue

        if rule['host'].startswith('*'):  # filter out wildcard domains
            continue

        monitor_name = f"{name}-{index}"
        url = rule['host']

        monitor_body = K8s.construct_k8s_ur_monitor_body(
            namespace, name=monitor_name, url=url, type=crds.MonitorType.PING.name)
        kopf.adopt(monitor_body)

        if index >= previous_rule_count:  # at first update existing UptimeRobotMonitors, we currently don't check if there's actually a change
            k8s.create_k8s_ur_monitor_with_body(namespace, monitor_body)
            logger.info(f'created new UptimeRobotMonitor object for URL {url}')
        else:  # then create new UptimeRobotMonitors
            k8s.update_k8s_ur_monitor_with_body(namespace, monitor_name, monitor_body)
            logger.info(f'updated UptimeRobotMonitor object for URL {url}')

        index += 1

    while index < previous_rule_count:  # make sure to clean up remaining UptimeRobotMonitors
        k8s.delete_k8s_ur_monitor(namespace, f"{name}-{index}")
        logger.info('deleted obsolete UptimeRobotMonitor object')
        index += 1


@kopf.on.update(crds.GROUP, crds.MonitorV1Beta1.version, crds.MonitorV1Beta1.plural)
def on_update(name: str, spec: dict, status: dict, diff: list, logger, **_):
    try:
        identifier = get_identifier(status)
    except KeyError as error:
        raise kopf.PermanentError(
            "was not able to determine the monitor ID for update") from error

    friendly_name = spec.get('friendlyName', name)

    if monitor_type_changed(diff):
        logger.info('monitor type changed, need to delete and recreate')
        delete_monitor(logger, identifier)

        identifier = create_monitor(
            logger,
            friendly_name=friendly_name,
            url=spec['url'],
            type=crds.MonitorType[spec['type']].value
        )

    else:
        identifier = update_monitor(
            logger,
            identifier,
            friendly_name=friendly_name,
            url=spec['url'],
            type=crds.MonitorType[spec['type']].value
        )

    return {MONITOR_ID_KEY: identifier}


@kopf.on.delete(crds.GROUP, crds.MonitorV1Beta1.version, crds.MonitorV1Beta1.plural)
def on_delete(status: dict, logger, **_):
    try:  # making sure to catch all exceptions here to prevent blocking deletion
        identifier = get_identifier(status)
        delete_monitor(logger, identifier)
    except KeyError as error:
        raise kopf.PermanentError(
            "was not able to determine the monitor ID for deletion") from error
    except Exception as error:
        raise kopf.PermanentError(f"deleting monitor failed: {error}") from error
