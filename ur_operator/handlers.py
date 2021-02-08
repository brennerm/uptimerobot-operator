import logging

import kubernetes.config as k8s_config
import kubernetes.client as k8s_client
import kopf

import crds
from k8s import K8s
import uptimerobot
from config import Config

MONITOR_ID_KEY = 'monitor_id'
PSP_ID_KEY = 'psp_id'

config = Config()
uptime_robot = None
k8s = None


# disable liveness check request logs
logging.getLogger('aiohttp.access').setLevel(logging.WARN)


def create_crds(logger):
    try:
        k8s_config.load_kube_config()
    except k8s_config.ConfigException:
        k8s_config.load_incluster_config()

    api_instance = k8s_client.ApiextensionsV1Api()
    for crd in [crds.MonitorV1Beta1.crd, crds.PspV1Beta1.crd]:
        try:
            api_instance.create_custom_resource_definition(crd)
            logger.info(f'CRDs {crd.metadata.name} successfully created')
        except k8s_client.rest.ApiException as error:
            if error.status == 409:
                api_instance.patch_custom_resource_definition(
                    name=crd.metadata.name, body=crd)
                logger.debug(f'CRDs {crd.metadata.name} successfully patched')
            else:
                logger.error(f'CRD {crd.metadata.name} failed to create')
                raise error


def init_uptimerobot_api(logger):
    global uptime_robot
    try:
        uptime_robot = uptimerobot.create_uptimerobot_api()
    except Exception as error:
        logger.error('failed to create UptimeRobot API')
        raise kopf.PermanentError(error)


def create_monitor(logger, **kwargs):
    resp = uptime_robot.new_monitor(
        **{k:str(v) for k,v in kwargs.items()}
        )

    if resp['stat'] == 'ok':
        identifier = resp['monitor']['id']
        logger.info(
            f'monitor with ID {identifier} has been created successfully')
        return identifier

    raise kopf.PermanentError(f'failed to create monitor: {resp["error"]}')


def update_monitor(logger, identifier, **kwargs):
    resp = uptime_robot.edit_monitor(
        identifier,
        **{k:str(v) for k,v in kwargs.items()}
        )

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

def create_psp(logger, **kwargs):
    resp = uptime_robot.new_psp(
        type='1',
        **{k:str(v) for k,v in kwargs.items()}
        )

    if resp['stat'] == 'ok':
        identifier = resp['psp']['id']
        logger.info(
            f'PSP with ID {identifier} has been created successfully')
        return identifier

    raise kopf.PermanentError(f'failed to create PSP: {resp["error"]}')


def update_psp(logger, identifier, **kwargs):
    resp = uptime_robot.edit_psp(
        identifier,
        **{k:str(v) for k,v in kwargs.items()}
        )

    if resp['stat'] == 'ok':
        identifier = resp['psp']['id']
        logger.info(
            f'PSP with ID {identifier} has been updated successfully')
        return identifier

    raise kopf.PermanentError(f'failed to update PSP with ID {identifier}: {resp["error"]}')


def delete_psp(logger, identifier):
    resp = uptime_robot.delete_psp(identifier)
    if resp['stat'] == 'ok':
        logger.info(
            f'PSP with ID {identifier} has been deleted successfully')
    else:
        if resp['error']['type'] == 'not_found':
            logger.info(
                f'PSP with ID {identifier} has already been deleted')
            return

        raise kopf.PermanentError(
            f'failed to delete PSP with ID {identifier}: {resp["error"]}')


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

def get_psp_identifier(status: dict):
    if on_psp_update.__name__ in status:
        return status[on_psp_update.__name__][PSP_ID_KEY]

    if on_psp_create.__name__ in status:
        return status[on_psp_create.__name__][PSP_ID_KEY]

    raise KeyError(PSP_ID_KEY)

@kopf.on.startup()
def startup(logger, **_):
    if config.DISABLE_INGRESS_HANDLING:
        logger.info('handling of Ingress resources has been disabled')

    global k8s
    k8s = K8s()
    init_uptimerobot_api(logger)
    create_crds(logger)


@kopf.on.create(crds.GROUP, crds.MonitorV1Beta1.version, crds.MonitorV1Beta1.plural)
def on_create(name: str, spec: dict, logger, **_):
    identifier = create_monitor(
        logger,
        **crds.MonitorV1Beta1.spec_to_request_dict(name, spec)
    )

    return {MONITOR_ID_KEY: identifier}


@kopf.on.create('networking.k8s.io', 'v1', 'ingresses')
def on_ingress_create(name: str, namespace: str, annotations: dict, spec: dict, logger, **_):
    if config.DISABLE_INGRESS_HANDLING:
        logger.info('handling of Ingress resources has been disabled')
        return

    monitor_prefix = f'{crds.GROUP}/monitor.'
    monitor_spec = {k.replace(monitor_prefix, ''): v for k, v in annotations.items() if k.startswith(monitor_prefix)}

    index = 0
    for rule in spec['rules']:
        if 'host' not in rule:
            continue

        if rule['host'].startswith('*'):  # filter out wildcard domains
            continue

        host = rule['host']

        # we default to a ping check
        if 'type' not in monitor_spec:
            monitor_spec['type'] = crds.MonitorType.PING.name

        if monitor_spec['type'] == 'HTTP':
            monitor_spec['url'] = f"http://{host}"
        elif monitor_spec['type'] == 'HTTPS':
            monitor_spec['url'] = f"https://{host}"
        else:
            monitor_spec['url'] = host

        monitor_body = K8s.construct_k8s_ur_monitor_body(
            namespace, name=f"{name}-{index}", **crds.MonitorV1Beta1.annotations_to_spec_dict(monitor_spec))
        kopf.adopt(monitor_body)

        k8s.create_k8s_crd_obj_with_body(crds.MonitorV1Beta1, namespace, monitor_body)
        logger.info(f'created new UptimeRobotMonitor object for URL {host}')
        index += 1


@kopf.on.update('networking.k8s.io', 'v1', 'ingresses')
def on_ingress_update(name: str, namespace: str, annotations: dict, spec: dict, old: dict, logger, **_):
    if config.DISABLE_INGRESS_HANDLING:
        logger.info('handling of Ingress resources has been disabled')
        return

    monitor_prefix = f'{crds.GROUP}/monitor.'
    monitor_spec = {k.replace(monitor_prefix, ''): v for k, v in annotations.items() if k.startswith(monitor_prefix)}

    previous_rule_count = len(old['spec']['rules'])
    index = 0

    for rule in spec['rules']:
        if 'host' not in rule:
            continue

        if rule['host'].startswith('*'):  # filter out wildcard domains
            continue

        host = rule['host']

        # we default to a ping check
        if 'type' not in monitor_spec:
            monitor_spec['type'] = crds.MonitorType.PING.name

        if monitor_spec['type'] == 'HTTP':
            monitor_spec['url'] = f"http://{host}"
        elif monitor_spec['type'] == 'HTTPS':
            monitor_spec['url'] = f"https://{host}"
        else:
            monitor_spec['url'] = host

        monitor_name = f"{name}-{index}"

        monitor_body = K8s.construct_k8s_ur_monitor_body(
            namespace, name=monitor_name, **crds.MonitorV1Beta1.annotations_to_spec_dict(monitor_spec))
        kopf.adopt(monitor_body)

        if index >= previous_rule_count:  # at first update existing UptimeRobotMonitors, we currently don't check if there's actually a change
            k8s.create_k8s_crd_obj_with_body(crds.MonitorV1Beta1, namespace, monitor_body)
            logger.info(f'created new UptimeRobotMonitor object for URL {host}')
        else:  # then create new UptimeRobotMonitors
            k8s.update_k8s_crd_obj_with_body(crds.MonitorV1Beta1, namespace, monitor_name, monitor_body)
            logger.info(f'updated UptimeRobotMonitor object for URL {host}')

        index += 1

    while index < previous_rule_count:  # make sure to clean up remaining UptimeRobotMonitors
        k8s.delete_k8s_crd_obj(crds.MonitorV1Beta1, namespace, f"{name}-{index}")
        logger.info('deleted obsolete UptimeRobotMonitor object')
        index += 1


@kopf.on.update(crds.GROUP, crds.MonitorV1Beta1.version, crds.MonitorV1Beta1.plural)
def on_update(name: str, spec: dict, status: dict, diff: list, logger, **_):
    try:
        identifier = get_identifier(status)
    except KeyError as error:
        raise kopf.PermanentError(
            "was not able to determine the monitor ID for update") from error

    if monitor_type_changed(diff):
        logger.info('monitor type changed, need to delete and recreate')
        delete_monitor(logger, identifier)

        identifier = create_monitor(
            logger,
            **crds.MonitorV1Beta1.spec_to_request_dict(name, spec)
        )

    else:
        identifier = update_monitor(
            logger,
            identifier,
            **crds.MonitorV1Beta1.spec_to_request_dict(name, spec)
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

@kopf.on.create(crds.GROUP, crds.MonitorV1Beta1.version, crds.PspV1Beta1.plural)
def on_psp_create(name: str, spec: dict, logger, **_):
    identifier = create_psp(
        logger,
        **crds.PspV1Beta1.spec_to_request_dict(name, spec)
    )

    return {PSP_ID_KEY: identifier}

@kopf.on.update(crds.GROUP, crds.MonitorV1Beta1.version, crds.PspV1Beta1.plural)
def on_psp_update(name: str, spec: dict, status: dict, logger, **_):
    try:
        identifier = get_psp_identifier(status)
    except KeyError as error:
        raise kopf.PermanentError(
            "was not able to determine the PSP ID for update") from error

    identifier = update_psp(
        logger,
        identifier,
        **crds.PspV1Beta1.spec_to_request_dict(name, spec)
    )

    return {PSP_ID_KEY: identifier}

@kopf.on.delete(crds.GROUP, crds.MonitorV1Beta1.version, crds.PspV1Beta1.plural)
def on_psp_delete(status: dict, logger, **_):
    try:  # making sure to catch all exceptions here to prevent blocking deletion
        identifier = get_psp_identifier(status)
        delete_psp(logger, identifier)
    except KeyError as error:
        raise kopf.PermanentError(
            "was not able to determine the PSP ID for deletion") from error
    except Exception as error:
        raise kopf.PermanentError(f"deleting PSP failed: {error}") from error
