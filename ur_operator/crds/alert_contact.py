#!/usr/bin/env python3

import enum

import kubernetes.client as k8s_client

from .constants import GROUP
from .utils import camel_to_snake_case


@enum.unique
class AlertContactType(enum.Enum):
    SMS = 1
    EMAIL = 2
    TWITTER_DM = 3
    BOXCAR = 4
    WEB_HOOK = 5
    PUSHBULLET = 6
    ZAPIER = 7
    PUSHOVER = 9
    HIPCHAT = 10
    SLACK = 11


class AlertContactV1Beta1:
    plural = 'alertcontacts'
    singular = 'alertcontact'
    kind = 'AlertContact'
    short_names = ['ac']
    version = 'v1beta1'

    required_props = ['type', 'value']

    spec_properties = {
        'type': k8s_client.V1JSONSchemaProps(
            type='string',
            enum=list(
                AlertContactType.__members__.keys()),
            description=f'the type of alert contact, one of: {",".join(list(AlertContactType.__members__.keys()))}'
        ),
        'value': k8s_client.V1JSONSchemaProps(
            type='string',
            description='the alert contact\'s mail address / phone number / URL / connection string'
        ),
        'friendlyName': k8s_client.V1JSONSchemaProps(
            type='string',
            description='friendly name of the alert contact, defaults to name of the AlertContact object'
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

        # map enum values
        for key, enum_class in {
            'type': AlertContactType
        }.items():
            request_dict[key] = enum_class[request_dict[key]
                                           ].value if key in request_dict else None

        # drop None entries

        return {k: v for k, v in request_dict.items() if v is not None}
