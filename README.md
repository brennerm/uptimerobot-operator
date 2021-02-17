# uptimerobot-operator

This operator automatically creates uptime monitors at [UptimeRobot](https://uptimerobot.com) for your Kubernetes Ingress resources. This allows you to easily integrate uptime monitoring of your services into your Kubernetes deployments.

> :warning: **This project is still in an early phase. Use it on your own risk but make sure to create issues for issues you encounter.**

:heart: to UptimeRobot for providing a pro account to be able to test the pro plan features!

## Usage

After installing the uptimerobot-operator it'll watch for Ingress resources in your Kubernetes cluster. For example after creating the following Ingress

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-ingress
  annotations:
    uroperator.brennerm.github.io/monitor.type: HTTPS
    uroperator.brennerm.github.io/monitor.interval: "600"
spec:
  rules:
  - host: brennerm.github.io
    http:
      paths:
      - pathType: Prefix
        path: "/"
        backend:
          service:
            name: service1
            port:
              number: 80
```

a new monitor for the URL *https://brennerm.github.io* is automatically being created in your UptimeRobot account.

The same monitor can also be created using the UptimeRobotMonitor resource like so:

```yaml
apiVersion: uroperator.brennerm.github.io/v1beta1
kind: UptimeRobotMonitor
metadata:
  name: my-custom-monitor
spec:
  url: "https://brennerm.github.io"
  type: HTTPS
  interval: 600
```

The operator also supports creating public status pages. See below for details.

## Installation

### Create an UptimeRobot API key

1. [Create an](https://uptimerobot.com/signUp) or login to your UptimeRobot account (no credit card required and they provide up to 50 monitors for free)
2. Go to "My Settings"
3. Generate and save "Main API Key" (the other API keys do not provide sufficient permissions to create, update and delete monitors)

### Deploying to Kubernetes using Helm

1. Add the uptimerobot-operator chart repo `helm repo add uptimerobot-operator https://brennerm.github.io/uptimerobot-operator/helm`
2. Deploy the Helm chart `helm upgrade --install uptimerobot-operator uptimerobot-operator --set uptimeRobotApiKey=$MY_UPTIMEROBOT_API_KEY`

Have a look at the [values file](helm/uptimerobot-operator/values.yaml) if you want to customize the deployment.

### Running local

> :information_source: **The following commands will make the operator work with your currently selected Kubernetes cluster (`kubectl config current-context`).**

1. Install all dependencies `pipenv install`
2. Set UptimeRobot API key `export UPTIMEROBOT_API_KEY=$MY_UPTIMEROBOT_API_KEY`
3. Start operator `kopf run --standalone ur_operator/handlers.py`

### Running in self-built Docker

1. Build Docker image `docker build -t uptimerobot-operator .`
2. Start container `docker run -e UPTIMEROBOT_API_KEY=$MY_UPTIMEROBOT_API_KEY -v ~/.kube:/home/ur_operator/.kube uptimerobot-operator`

### Running in pre-built Docker

1. Start container `docker run -e UPTIMEROBOT_API_KEY=$MY_UPTIMEROBOT_API_KEY -v ~/.kube:/home/ur_operator/.kube ghcr.io/brennerm/uptimerobot-operator:latest`

## Documentation

### UptimeRobotMonitor

The UptimeRobotMonitor resource supports all current parameters for monitors that UptimeRobot offers. Below you can find a list that contains all of them.

|key|type|description|
|-|-|-|
|`url` (required)|`string`|URL that will be monitored|
|`type` (required)|`string`|Type of monitor, one of: HTTP,HTTPS,KEYWORD,PING,PORT,HEARTBEAT|
|`friendlyName`|`string`|Friendly name of monitor, defaults to name of UptimeRobotMonitor object|
|`subType`|`string`|Subtype of monitor, one of: HTTP,HTTPS,KEYWORD,PING,PORT,HEARTBEAT|
|`port`|`integer`|Port to monitor when using monitor sub type PORT|
|`keywordType`|`string`|Keyword type when using monitor type KEYWORD, one of: EXISTS,NOT_EXISTS|
|`keywordValue`|`string`|Keyword value when using monitor type KEYWORD|
|`interval`|`integer`|The interval for the monitoring check (300 seconds by default)|
|`httpUsername`|`string`|Used for password protected pages when using monitor type HTTP,HTTP or KEYWORD, deprecated: use httpAuthSecret|
|`httpPassword`|`string`|Used for password protected pages when using monitor type HTTP,HTTP or KEYWORD, deprecated: use httpAuthSecret|
|`httpAuthSecret`|`string`|reference to a Kubernetes secret in the same namespace containing user and password for password protected pages when using monitor type HTTP,HTTPS or KEYWORD|
|`httpAuthType`|`string`|Used for password protected pages when using monitor type HTTP,HTTPS or KEYWORD, one of: BASIC_AUTH,DIGEST|
|`httpMethod`|`string`|The HTTP method to be used, one of: HEAD,GET,POST,PUT,PATCH,DELETE,OPTIONS|
|`postType`|`string`|The format of data to be sent with POST, PUT, PATCH, DELETE, OPTIONS requests|
|`postContentType`|`string`|The Content-Type header to be sent with POST, PUT, PATCH, DELETE, OPTIONS requests, one of: TEXT_HTML,APPLICATION_JSON|
|`postValue`|`object`|The data to be sent with POST, PUT, PATCH, DELETE, OPTIONS requests|
|`customHttpHeaders`|`object`|Custom HTTP headers to be sent along monitor request, formatted as JSON|
|`customHttpStatuses`|`string`|Allows to define HTTP status codes that will be handled as up or down, e.g. 404:0_200:1 to accept 404 as down and 200 as up|
|`ignoreSslErrors`|`boolean`|Flag to ignore SSL certificate related issues|
|`alertContacts`|`string`|Alert contacts to be notified when monitor goes up or down. For syntax check https://uptimerobot.com/api/#newMonitorWrap|
|`mwindows`|`string`|Maintenance window IDs for this monitor|

### Ingress

For Ingress resources the same parameters are supported. You pass them through annotations attached to your Ingress with the prefix `uroperator.brennerm.github.io/monitor.`.
See below for an example.

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-ingress
  annotations:
    uroperator.brennerm.github.io/monitor.type: HTTPS
    uroperator.brennerm.github.io/monitor.interval: "600"
spec:
  rules:
...
```

To disable ingress handling completely pass the environment variable `URO_DISABLE_INGRESS_HANDLING=1` to the operator.

### Public Status Pages

The PublicStatusPage resource supports all current parameters for status pages that UptimeRobot offers. Below you can find a list that contains all of them.

|key|type|description|
|-|-|-|
|`monitors` (required)|`string`|the list of monitor IDs to be displayed in status page (the values are seperated with "-" or 0 for all monitors)|
|`friendlyName`|`string`|Friendly name of public status page, defaults to name of PublicStatusPage object|
|`customDomain`|`string`|the domain or subdomain that the status page will run on|
|`password`|`string`|the password for the status page, deprecated: use passwordSecret|
|`passwordSecret`|`string`|reference to a Kubernetes secret in the same namespace containing the password for the status page|
|`sort`|`string`|the sorting of the monitors on the status page, one of: FRIENDLY_NAME_A_Z,FRIENDLY_NAME_Z_A,STATUS_UP_DOWN_PAUSED,STATUS_DOWN_UP_PAUSED|
|`status`|`string`|the status of the status page, one of: PAUSED,ACTIVE|
|`hideUrlLinks`|`boolean`|Flag to remove the UptimeRobot link from the status page (pro plan feature)|

```yaml
apiVersion: uroperator.brennerm.github.io/v1beta1
kind: PublicStatusPage
metadata:
  name: my-public-status-page
spec:
  monitors: "0" # will include all monitors
```

### Maintenance Windows

The MaintenanceWindow resource supports all current parameters for maintenance windows that UptimeRobot offers. Below you can find a list that contains all of them.

|key|type|description|
|-|-|-|
|`type` (required)|`string`|the type of maintenance window, one of: ONCE,DAILY,WEEKLY,MONTHLY|
|`startTime` (required)|`string`|the start time of the maintenance window, in seconds since epoch for type MaintenanceWindowType.ONCE, in HH:mm format for the other types|
|`duration` (required)|`number`|the number of seconds the maintenance window will be active|
|`friendlyName`|`string`|friendly name of the maintenance window, defaults to name of the MaintenanceWindow object|
|`value`|`string`|allows to specify the maintenance window selection, e.g. 2-4-5 for Tuesday-Thursday-Friday or 10-17-26 for the days of the month, only valid and required for MaintenanceWindowType.WEEKLY and MaintenanceWindowType.MONTHLY|

```yaml
apiVersion: uroperator.brennerm.github.io/v1beta1
kind: MaintenanceWindow
metadata:
  name: my-maintenance-window
spec:
  type: DAILY
  startTime: "10:00"
  duration: 30
```

### Alert Contacts

The AlertContact resource supports all current parameters for alert contacts that UptimeRobot offers. Below you can find a list that contains all of them.

|key|type|description|
|-|-|-|
|`type` (required)|`string`|the type of alert contact, one of: SMS,EMAIL,TWITTER_DM,BOXCAR,WEB_HOOK,PUSHBULLET,ZAPIER,PUSHOVER,HIPCHAT,SLACK|
|`value` (required)|`string`|the alert contact's mail address / phone number / URL / connection string|
|`friendlyName`|`string`|friendly name of the alert contact, defaults to name of the AlertContact object|

```yaml
apiVersion: uroperator.brennerm.github.io/v1beta1
kind: AlertContact
metadata:
  name: my-alert-contact
spec:
  type: EMAIL
  value: foo@bar.com
```

## Planned features

- provide a Helm chart to ease deployment :heavy_check_mark:
- support all configuration parameters for Monitors that UptimeRobot offers :heavy_check_mark:
- add support for creating Uptime Robot :heavy_check_mark:
  - alert contacts, :heavy_check_mark:
  - maintenance windows :heavy_check_mark:
  - public status pages using Kubernetes resources :heavy_check_mark:
- implement automatic detection of HTTP path of Ingress resources
- add an integration for external-dns to support creating monitors for Service resources
