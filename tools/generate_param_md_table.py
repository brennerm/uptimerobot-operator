import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(
    os.path.dirname(__file__), '../ur_operator')))

import k8s
import crds
import crds.constants

from crds.monitor import MonitorV1Beta1
from crds.alert_contact import AlertContactV1Beta1
from crds.psp import PspV1Beta1
from crds.maintenance_window import MaintenanceWindowV1Beta1

for crd in [MonitorV1Beta1, PspV1Beta1, MaintenanceWindowV1Beta1, AlertContactV1Beta1]:
    print('|key|type|description|')
    print('|-|-|-|')

    for key, prop in crd.spec_properties.items():
        print(f'|`{key}`{" (required)" if key in crd.required_props else ""}|`{prop.type}`|{prop.description}|')
    print()
