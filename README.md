# uptimerobot-operator

This operator automatically creates uptime monitors at [UptimeRobot](https://uptimerobot.com) for your Kubernetes Ingress resources. This allows you to easily integrate uptime monitoring of your services into your Kubernetes deployments.

> :warning: **This project is in an very early phase. Do not use it in a productive environment and expect to miss a lot of features. Feel free to create issues for things you would like to see though.**

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

```

## Installation

### Create an UptimeRobot API key

1. Log in to your UptimeRobot account
2. Go to "My Settings"
3. Generate a "Main API Key" (the other API keys do not provide sufficient permissions to create, update and delete monitors)

### Running local

1. Install all dependencies `pipenv install`
2. Set UptimeRobot API key `export UPTIMEROBOT_API_KEY=$MY_UPTIMEROBOT_API_KEY`
3. Start operator `kopf run --standalone ur_operator/handlers.py`

### Deploying to Kubernetes

**Coming soon**

## Planned features

- provide a Helm chart to ease deployment
- support all configuration parameters for Monitors that UptimeRobot offers
- add support for creating Uptime Robot alert contacts, maintenance windows and public status pages using Kubernetes resources
- implement automatic detection of HTTP path of Ingress resources
- add an integration for external-dns to support creating monitors for Service resources
