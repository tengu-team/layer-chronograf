# Overview

Chronograf is the Complete Interface for the InfluxData Platform.

Chronograf is the user interface component of InfluxData’s TICK stack. It makes the monitoring and alerting for your infrastructure easy to setup and maintain. It is simple to use and includes templates and libraries to allow you to rapidly build dashboards with real-time visualizations of your data.

# Usage

Deploy the Chronograf charm:
```sh
juju deploy chronograf
```
## InfluxDB
A relation with InfluxDB is required for Chronograf to work:
```sh
juju deploy influxdb
juju add-relation chronograf influxdb
```
## Kapacitor
A relation with Kapacitor is not required but is possible:
```sh
juju deploy kapacitor
juju add-relation chronograf kapacitor
```
## UI
Expose Chronograf so you can browse to the web application:
```sh
juju expose chronograf
```
Browse to **http://PUBLIC_IP:8888** to start using Chronograf.

# Contact Information
- [Chronograf]
- [Chronograf Documentation]
- [Chronograf Charm Github]
## Authors
- Michiel Ghyselinck <michiel.ghyselinck@tengu.io>

[chronograf documentation]: https://docs.influxdata.com/chronograf/v1.3/
[chronograf charm github]: https://github.com/tengu-team/layer-chronograf
[chronograf]: https://www.influxdata.com/time-series-platform/chronograf/
