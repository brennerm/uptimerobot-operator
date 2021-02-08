import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..')))


import ur_operator.crds as crds

print('|key|type|description|')
print('|-|-|-|')

for key, prop in crds.MonitorV1Beta1.spec_properties.items():
    print(f'|`{key}`{" (required)" if key in crds.MonitorV1Beta1.required_props else ""}|`{prop.type}`|{prop.description}|')
