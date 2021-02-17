import logging

import kubernetes.config as k8s_config
import kubernetes.client as k8s_client

from crds import constants

class K8s:
    def __init__(self):
        try:
            k8s_config.load_kube_config()
        except k8s_config.ConfigException:
            k8s_config.load_incluster_config()
        except k8s_config.ConfigException as error:
            logging.error("Failed to load kube and incluster config, giving up...")
            raise error

        self.custom_objects_api = k8s_client.CustomObjectsApi()
        self.core_api = k8s_client.CoreV1Api()

    def create_k8s_crd_obj_with_body(self, crd, namespace, body):
        return self.custom_objects_api.create_namespaced_custom_object(
            group=constants.GROUP,
            version=crd.version,
            namespace=namespace,
            plural=crd.plural,
            body=body
        )

    def update_k8s_crd_obj_with_body(self, crd, namespace, name, body):
        return self.custom_objects_api.patch_namespaced_custom_object(
            group=constants.GROUP,
            version=crd.version,
            plural=crd.plural,
            namespace=namespace,
            name=name,
            body=body
        )

    def create_k8s_crd_obj(self, crd, namespace, name, **spec):
        return self.create_k8s_crd_obj_with_body(
            crd,
            namespace,
            {
                'apiVersion': f'{constants.GROUP}/{crd.version}',
                'kind': crd.kind,
                'metadata': {'name': name, 'namespace': namespace},
                'spec': spec
            }
        )

    def update_k8s_crd_obj(self, crd, namespace, name, **spec):
        return self.update_k8s_crd_obj_with_body(
            crd,
            namespace,
            name,
            {
                'spec': spec
            }
        )

    def delete_k8s_crd_obj(self, crd, namespace, name):
        self.custom_objects_api.delete_namespaced_custom_object(
            group=constants.GROUP,
            version=crd.version,
            plural=crd.plural,
            namespace=namespace,
            name=name,
        )

    def get_secret(self, namespace, name):
        return self.core_api.read_namespaced_secret(name, namespace)
