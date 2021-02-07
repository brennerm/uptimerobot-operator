#!/usr/bin/env python3

import enum
import json
import re

import kubernetes.client as k8s_client

from .constants import GROUP


pattern = re.compile(r'(?<!^)(?=[A-Z])')
def camel_to_snake_case(string): return pattern.sub('_', string).lower()


class MonitorType(enum.Enum):
    HTTP = 1
    HTTPS = 1
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
class MonitorHttpMethod(enum.Enum):
    HEAD = 1
    GET = 2
    POST = 3
    PUT = 4
    PATCH = 5
    DELETE = 6
    OPTIONS = 7


@enum.unique
class MonitorKeywordType(enum.Enum):
    EXISTS = 1
    NOT_EXISTS = 2


@enum.unique
class MonitorStatus(enum.Enum):
    PAUSED = 0
    NOT_CHECKED_YET = 1


@enum.unique
class MonitorHttpAuthType(enum.Enum):
    BASIC_AUTH = 1
    DIGEST = 2


@enum.unique
class MonitorPostType(enum.Enum):
    KEY_VALUE = 1
    RAW = 2


@enum.unique
class MonitorPostContentType(enum.Enum):
    TEXT_HTML = 0
    APPLICATION_JSON = 1


class MonitorV1Beta1:
    plural = 'uptimerobotmonitors'
    singular = 'uptimerobotmonitor'
    kind = 'UptimeRobotMonitor'
    short_names = ['urm']
    version = 'v1beta1'

    required_props = ['url', 'type']

    spec_properties = {
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
            enum=list(
                MonitorType.__members__.keys()),
            description=f'Type of monitor, one of: {",".join(list(MonitorType.__members__.keys()))}'
        ),
        'subType': k8s_client.V1JSONSchemaProps(
            type='string',
            enum=list(
                MonitorSubType.__members__.keys()),
            description=f'Subtype of monitor, one of: {",".join(list(MonitorType.__members__.keys()))}'
        ),
        'port': k8s_client.V1JSONSchemaProps(
            type='integer',
            description=f'Port to monitor when using monitor sub type {MonitorType.PORT.name}'
        ),
        'keywordType': k8s_client.V1JSONSchemaProps(
            type='string',
            enum=list(
                MonitorKeywordType.__members__.keys()),
            description=f'Keyword type when using monitor type {MonitorType.KEYWORD.name}, one of: {",".join(list(MonitorKeywordType.__members__.keys()))}'
        ),
        'keywordValue': k8s_client.V1JSONSchemaProps(
            type='string',
            description=f'Keyword value when using monitor type {MonitorType.KEYWORD.name}'
        ),
        'interval': k8s_client.V1JSONSchemaProps(
            type='integer',
            multiple_of=60.,
            description='The interval for the monitoring check (300 seconds by default)'
        ),
        'httpUsername': k8s_client.V1JSONSchemaProps(
            type='string',
            description=f'Used for password protected pages when using monitor type {MonitorType.HTTP.name},{MonitorType.HTTPS.name} or {MonitorType.KEYWORD.name}'
        ),
        'httpPassword': k8s_client.V1JSONSchemaProps(
            type='string',
            description=f'Used for password protected pages when using monitor type {MonitorType.HTTP.name},{MonitorType.HTTPS.name} or {MonitorType.KEYWORD.name}'
        ),
        'httpAuthType': k8s_client.V1JSONSchemaProps(
            type='string',
            enum=list(
                MonitorHttpAuthType.__members__.keys()),
            description=f'Used for password protected pages when using monitor type {MonitorType.HTTP.name},{MonitorType.HTTPS.name} or {MonitorType.KEYWORD.name}, one of: {",".join(list(MonitorHttpAuthType.__members__.keys()))}'
        ),
        'httpMethod': k8s_client.V1JSONSchemaProps(
            type='string',
            enum=list(
                MonitorHttpMethod.__members__.keys()),
            description=f'The HTTP method to be used, one of: {",".join(list(MonitorHttpMethod.__members__.keys()))}'
        ),
        'postType': k8s_client.V1JSONSchemaProps(
            type='string',
            enum=list(
                MonitorPostType.__members__.keys()),
            description='The format of data to be sent with POST, PUT, PATCH, DELETE, OPTIONS requests'
        ),
        'postContentType': k8s_client.V1JSONSchemaProps(
            type='string',
            enum=list(
                MonitorPostContentType.__members__.keys()),
            description=f'The Content-Type header to be sent with POST, PUT, PATCH, DELETE, OPTIONS requests, one of: {",".join(list(MonitorPostContentType.__members__.keys()))}'
        ),
        'postValue': k8s_client.V1JSONSchemaProps(
            type='object',
            description='The data to be sent with POST, PUT, PATCH, DELETE, OPTIONS requests',
            x_kubernetes_preserve_unknown_fields=True
        ),
        'customHttpHeaders': k8s_client.V1JSONSchemaProps(
            type='object',
            description='Custom HTTP headers to be sent along monitor request, formatted as JSON',
            x_kubernetes_preserve_unknown_fields=True
        ),
        'customHttpStatuses': k8s_client.V1JSONSchemaProps(
            type='string',
            description='Allows to define HTTP status codes that will be handled as up or down, e.g. 404:0_200:1 to accept 404 as down and 200 as up'
        ),
        'ignoreSslErrors': k8s_client.V1JSONSchemaProps(
            type='boolean',
            description='Flag to ignore SSL certificate related issues'
        ),
        'alertContacts': k8s_client.V1JSONSchemaProps(
            type='string',
            description='Alert contacts to be notified when monitor goes up or down. For syntax check https://uptimerobot.com/api/#newMonitorWrap'
        ),
        'mwindows': k8s_client.V1JSONSchemaProps(
            type='string',
            description='Maintenance window IDs for this monitor'
        )
    }

    crd = k8s_client.V1CustomResourceDefinition(
        api_version='apiextensions.k8s.io/v1',
        kind='CustomResourceDefinition',
        metadata=k8s_client.V1ObjectMeta(name=f'{plural}.{GROUP}'),
        spec=k8s_client.V1CustomResourceDefinitionSpec(
            group=GROUP,
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
                                required=required_props,
                                properties=spec_properties
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

    @staticmethod
    def spec_to_request_dict(name: str, spec: dict) -> dict:
        # convert all keys from camel to snake case
        request_dict = {camel_to_snake_case(k): v for k, v in spec.items()}
        request_dict['friendly_name'] = request_dict.get('friendly_name', name)
        request_dict['type'] = MonitorType[spec['type']].value

        # map enum values
        for key, enum_class in {
            'sub_type': MonitorSubType,
            'keyword_type': MonitorKeywordType,
            'http_auth_type': MonitorHttpAuthType,
            'http_method': MonitorHttpMethod,
            'post_type': MonitorPostType,
            'post_content_type': MonitorPostContentType
        }.items():
            request_dict[key] = enum_class[request_dict[key]
                                           ].value if key in request_dict else None

        # drop None entries

        return {k: v for k, v in request_dict.items() if v is not None}

    @staticmethod
    def annotations_to_spec_dict(annotations: dict) -> dict:
        spec = {}

        for key, value in annotations.items():
            if key not in MonitorV1Beta1.spec_properties:
                continue

            if MonitorV1Beta1.spec_properties[key].type == 'integer':
                spec[key] = int(value)
            elif MonitorV1Beta1.spec_properties[key].type == 'object':
                spec[key] = json.loads(value)
            else:
                spec[key] = value

        return spec
