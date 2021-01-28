#!/usr/bin/env python3

import kubernetes.client as k8s_client

import enum

from . import group

@enum.unique
class MonitorType(enum.Enum):
    HTTP_HTTPS = 1
    KEYWORD = 2
    PING = 3
    PORT = 4
    HEARTBEAT = 5

@enum.unique
class MonitorSubType(enum.Enum):
    HTTP = 1
    HTTPS = 2
    FTP = 3
    SMTP = 4
    POP3 = 5
    IMAP = 6
    CUSTOM = 99

@enum.unique
class MonitorStatus(enum.Enum):
    PAUSED = 0
    NOT_CHECKED_YET = 1
    UP = 2
    SEEMS_DOWN = 8
    DOWN = 9

@enum.unique
class MonitorHttpMethod(enum.Enum):
    HEAD = 1
    GET = 2
    POST = 3
    PUT = 4
    PATCH = 5
    DELETE = 6
    OPTIONS = 7

class MonitorV1Beta1:
    plural = 'uptimerobotmonitors'
    singular = 'uptimerobotmonitor'
    kind = 'UptimeRobotMonitor'
    short_names = ['urm']
    version = 'v1beta1'
    
    crd = k8s_client.V1CustomResourceDefinition(
        api_version='apiextensions.k8s.io/v1',
        kind='CustomResourceDefinition',
        metadata=k8s_client.V1ObjectMeta(name=f'{plural}.{group}'),
        spec=k8s_client.V1CustomResourceDefinitionSpec(
            group=group,
            versions=[k8s_client.V1CustomResourceDefinitionVersion(
                name=version,
                served=True,
                storage=True,
                schema=k8s_client.V1CustomResourceValidation(
                    open_apiv3_schema=k8s_client.V1JSONSchemaProps(
                        type='object',
                        properties={
                            'spec': k8s_client.V1JSONSchemaProps(
                                type='object',
                                required=['url', 'type'],
                                properties={
                                    'friendlyName': k8s_client.V1JSONSchemaProps(
                                        type='string',
                                        description='Friendly name of monitor, defaults to name of UptimeRobotMonitor object'
                                    ),
                                    'url': k8s_client.V1JSONSchemaProps(
                                        type='string',
                                        description='URL that will be monitored'
                                    ),
                                    'type': k8s_client.V1JSONSchemaProps(
                                        type='string',
                                        enum=list(MonitorType.__members__.keys()),
                                        description=f'Type of monitor, one of: {list(MonitorType.__members__.keys())}'
                                    )
                                }
                            ),
                            'status': k8s_client.V1JSONSchemaProps(
                                type='object',
                                x_kubernetes_preserve_unknown_fields=True
                            )
                        }
                    )
                )
            )],
            scope='Namespaced',
            names=k8s_client.V1CustomResourceDefinitionNames(
                plural=plural,
                singular=singular,
                kind=kind,
                short_names=short_names
            )
        )
    )