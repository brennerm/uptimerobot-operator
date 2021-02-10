#!/usr/bin/env python3

import enum

import kubernetes.client as k8s_client

from .constants import GROUP
from .utils import camel_to_snake_case


@enum.unique
class MaintenanceWindowType(enum.Enum):
    ONCE = 1
    DAILY = 2
    WEEKLY = 3
    MONTHLY = 4


class MaintenanceWindowV1Beta1:
    plural = 'maintenancewindows'
    singular = 'maintenancewindow'
    kind = 'MaintenanceWindow'
    short_names = ['mw']
    version = 'v1beta1'

    required_props = ['type', 'startTime', 'duration']

    spec_properties = {
        'type': k8s_client.V1JSONSchemaProps(
            type='string',
            enum=list(
                MaintenanceWindowType.__members__.keys()),
            description=f'the type of maintenance window, one of: {",".join(list(MaintenanceWindowType.__members__.keys()))}'
        ),
        'startTime': k8s_client.V1JSONSchemaProps(
            type='string',
            description=f'the start time of the maintenance window, in seconds since epoch for type {MaintenanceWindowType.ONCE}, in HH:mm format for the other types'
        ),
        'duration': k8s_client.V1JSONSchemaProps(
            type='number',
            description='the number of seconds the maintenance window will be active'
        ),
        'friendlyName': k8s_client.V1JSONSchemaProps(
            type='string',
            description='friendly name of the maintenance window, defaults to name of the MaintenanceWindow object'
        ),
        'value': k8s_client.V1JSONSchemaProps(
            type='string',
            description=f'allows to specify the maintenance window selection, e.g. 2-4-5 for Tuesday-Thursday-Friday or 10-17-26 for the days of the month, only valid and required for {MaintenanceWindowType.WEEKLY} and {MaintenanceWindowType.MONTHLY}'
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
        request_dict['value'] = request_dict.get('value', '')

        # map enum values
        for key, enum_class in {
            'type': MaintenanceWindowType
        }.items():
            request_dict[key] = enum_class[request_dict[key]
                                           ].value if key in request_dict else None

        # drop None entries

        return {k: v for k, v in request_dict.items() if v is not None}
