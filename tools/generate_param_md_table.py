import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..')))


import ur_operator.crds as crds

for crd in [crds.MonitorV1Beta1, crds.PspV1Beta1, crds.MaintenanceWindowV1Beta1]:
    print('|key|type|description|')
    print('|-|-|-|')

    for key, prop in crd.spec_properties.items():
        print(f'|`{key}`{" (required)" if key in crd.required_props else ""}|`{prop.type}`|{prop.description}|')
    print()
