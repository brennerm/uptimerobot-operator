# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

### Added

- new property `passwordSecret` to PublicStatusPage resource, allows to reference password from Kubernetes secret [#22](https://github.com/brennerm/uptimerobot-operator/pull/22)
- new property `httpAuthSecret` to UptimeRobotMonitor resource, allows to reference username and password from Kubernetes secret [#23](https://github.com/brennerm/uptimerobot-operator/pull/23)

### Deprecated

- `password` property of PublicStatusPage resource, use `passwordSecret` instead
- `httpUsername` and `httpPassword` property of UptimeRobotMonitor resource, use `httpAuthSecret` instead

## [v0.3.0] - 2021-02-16

### Added

- introducing the PublicStatusPage resource to setup UptimeRobot status pages [#15](https://github.com/brennerm/uptimerobot-operator/pull/15)
- introducing the MaintenanceWindow resource to setup UptimeRobot maintenance windows [#16](https://github.com/brennerm/uptimerobot-operator/pull/16)
- introducing the AlertContact resource to setup UptimeRobot alert contacts [#21](https://github.com/brennerm/uptimerobot-operator/pull/21)

## [v0.2.0] - 2021-02-08

### Added

- allow to disable creating/updating/deleting monitors for Ingress resources [#6](https://github.com/brennerm/uptimerobot-operator/pull/6)
- the Helm chart now enables and makes use of the operator liveness endpoint [#8](https://github.com/brennerm/uptimerobot-operator/pull/8)
- add support for all monitor paramters to the UptimeRobot monitor resource [#10](https://github.com/brennerm/uptimerobot-operator/pull/10)
- allow to set all monitor parameters through Ingress annotations [#13](https://github.com/brennerm/uptimerobot-operator/pull/13)

## [v0.1.0] - 2021-02-02

### Added

- initial functionality
  - create ping monitors for Ingress resources
  - allow to create custom monitor with UptimeRobotMonitor resource
- first version of Helm chart
