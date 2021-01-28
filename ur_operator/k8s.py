import kubernetes.config as k8s_config
import kubernetes.client as k8s_client


import crds


class K8s:
    def __init__(self):
        k8s_config.load_kube_config()
        self.custom_objects_api = k8s_client.CustomObjectsApi()

    @staticmethod
    def construct_k8s_ur_monitor_body(namespace, name=None, **spec):
        metadata = {
            'namespace': namespace
        }

        if name:
            metadata['name'] = name

        return {
            'apiVersion': f'{crds.GROUP}/{crds.MonitorV1Beta1.version}',
            'kind': crds.MonitorV1Beta1.kind,
            'metadata': metadata,
            'spec': spec
        }

    def create_k8s_ur_monitor_with_body(self, namespace, body):
        return self.custom_objects_api.create_namespaced_custom_object(
            group=crds.GROUP,
            version=crds.MonitorV1Beta1.version,
            namespace=namespace,
            plural=crds.MonitorV1Beta1.plural,
            body=body
        )

    def update_k8s_ur_monitor_with_body(self, namespace, name, body):
        return self.custom_objects_api.patch_namespaced_custom_object(
            group=crds.GROUP,
            version=crds.MonitorV1Beta1.version,
            plural=crds.MonitorV1Beta1.plural,
            namespace=namespace,
            name=name,
            body=body
        )

    def create_k8s_ur_monitor(self, namespace, name, **spec):
        return self.create_k8s_ur_monitor_with_body(
            namespace,
            {
                'apiVersion': f'{crds.GROUP}/{crds.MonitorV1Beta1.version}',
                'kind': crds.MonitorV1Beta1.kind,
                'metadata': {'name': name, 'namespace': namespace},
                'spec': spec
            }
        )

    def update_k8s_ur_monitor(self, namespace, name, **spec):
        return self.update_k8s_ur_monitor_with_body(
            namespace,
            name,
            {
                'spec': spec
            }
        )

    def delete_k8s_ur_monitor(self, namespace, name):
        self.custom_objects_api.delete_namespaced_custom_object(
            group=crds.GROUP,
            version=crds.MonitorV1Beta1.version,
            plural=crds.MonitorV1Beta1.plural,
            namespace=namespace,
            name=name,
        )
