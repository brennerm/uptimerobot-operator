# uptimerobot-operator

This operator automatically creates uptime monitors at [UptimeRobot](https://uptimerobot.com) for your Kubernetes Ingress resources. This allows you to easily integrate uptime monitoring of your services into your Kubernetes deployments.

> :warning: **This project is in an very early phase. Do not use it in a productive environment and expect to miss a lot of features. Feel free to create issues for things you would like to see though.**
> **Additionally I'm not able to test pro plan features, e.g. like Hearbeat monitors as I don't have a pro account. They are implemented according to UptimeRobot's documentation but don't expect them to work.**

## Usage

After installing the uptimerobot-operator it'll watch for Ingress resources in your Kubernetes cluster. For example after creating the following Ingress

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-example-ingress
spec:
  rules:
  - host: "foo.com"
    http:
      paths:
      - pathType: Prefix
        path: "/bar"
        backend:
          service:
            name: service1
            port:
              number: 80
```

a new monitor for the URL *foo.com* is automatically being created in your UptimeRobot account.

Additionally you can create custom monitors using the UptimeRobotMonitor resource.

```yaml
apiVersion: uroperator.brennerm.github.io/v1beta1
kind: UptimeRobotMonitor
metadata:
  name: my-custom-monitor
spec:
  url: "bar.com"
  type: HTTP_HTTPS
  interval: 600
  httpAuthType: BASIC_AUTH
  httpUsername: foo
  httpPassword: s3cr3t

```

## Installation

### Create an UptimeRobot API key

1. [Create an](https://uptimerobot.com/signUp) or login to your UptimeRobot account (no credit card required and they provide up to 50 monitors for free)
2. Go to "My Settings"
3. Generate and save "Main API Key" (the other API keys do not provide sufficient permissions to create, update and delete monitors)

### Deploying to Kubernetes using Helm

1. Add the uptimerobot-operator uptimerobot-operato chart repo `helm repo add uptimerobot-operator https://brennerm.github.io/uptimerobot-operator/helm`
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

## Planned features

- provide a Helm chart to ease deployment :heavy_check_mark:
- support all configuration parameters for Monitors that UptimeRobot offers :heavy_check_mark:
- add support for creating Uptime Robot
  - alert contacts,
  - maintenance windows
  - public status pages using Kubernetes resources
- implement automatic detection of HTTP path of Ingress resources
- add an integration for external-dns to support creating monitors for Service resources
