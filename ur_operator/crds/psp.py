#!/usr/bin/env python3
import enum
import base64

import kubernetes.client as k8s_client

from k8s import K8s
from .constants import GROUP
from .utils import camel_to_snake_case

@enum.unique
class PspStatus(enum.Enum):
    PAUSED = 0
    ACTIVE = 1


@enum.unique
class PspSort(enum.Enum):
    FRIENDLY_NAME_A_Z = 1
    FRIENDLY_NAME_Z_A = 2
    STATUS_UP_DOWN_PAUSED = 3
    STATUS_DOWN_UP_PAUSED = 4


class PspV1Beta1:
    plural = 'publicstatuspages'
    singular = 'publicstatuspage'
    kind = 'PublicStatusPage'
    short_names = ['psp']
    version = 'v1beta1'

    required_props = ['monitors']

    spec_properties = {
        'monitors': k8s_client.V1JSONSchemaProps(
            type='string',
            description='the list of monitor IDs to be displayed in status page (the values are seperated with "-" or 0 for all monitors)'
        ),
        'friendlyName': k8s_client.V1JSONSchemaProps(
            type='string',
            description='Friendly name of public status page, defaults to name of PublicStatusPage object'
        ),
        'customDomain': k8s_client.V1JSONSchemaProps(
            type='string',
            description='the domain or subdomain that the status page will run on'
        ),
        'password': k8s_client.V1JSONSchemaProps(
            type='string',
            description='the password for the status page, deprecated: use passwordSecret'
        ),
        'passwordSecret': k8s_client.V1JSONSchemaProps(
            type='string',
            description='reference to a Kubernetes secret in the same namespace containing the password for the status page'
        ),
        'sort': k8s_client.V1JSONSchemaProps(
            type='string',
            enum=list(
                PspSort.__members__.keys()),
            description=f'the sorting of the monitors on the status page, one of: {",".join(list(PspSort.__members__.keys()))}'
        ),
        'status': k8s_client.V1JSONSchemaProps(
            type='string',
            enum=list(
                PspStatus.__members__.keys()),
            description=f'the status of the status page, one of: {",".join(list(PspStatus.__members__.keys()))}'
        ),
        'hideUrlLinks': k8s_client.V1JSONSchemaProps(
            type='boolean',
            description='Flag to remove the UptimeRobot link from the status page (pro plan feature)'
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
    def spec_to_request_dict(namespace: str, name: str, spec: dict) -> dict:
        k8s = K8s()

        # convert all keys from camel to snake case
        request_dict = {camel_to_snake_case(k): v for k, v in spec.items()}
        request_dict['friendly_name'] = request_dict.get('friendly_name', name)

        if 'password_secret' in request_dict:
            secret = k8s.get_secret(namespace, request_dict['password_secret'])

            request_dict['password'] = base64.b64decode(secret.data['password']).decode()
            request_dict.pop('password_secret')

        # map enum values
        for key, enum_class in {
            'sort': PspSort,
            'status': PspStatus
        }.items():
            request_dict[key] = enum_class[request_dict[key]
                                           ].value if key in request_dict else None

        # drop None entries
        return {k: v for k, v in request_dict.items() if v is not None}
