# Real-Time Healthcare IoT Network Monitoring (Project 8)

This stack deploys Zabbix (server + web), PostgreSQL, Grafana, an SNMP simulator, and a basic NETCONF simulator to demonstrate real-time monitoring, alarm lifecycle, and dashboards.

## Prerequisites
- Docker and Docker Compose installed
- Ports available: 8080 (Zabbix UI), 3000 (Grafana), 10051 (Zabbix server), 161/udp (SNMP), 830 (NETCONF)

## Quick Start
```bash
cd "$(dirname "$0")"
docker compose up -d
# wait ~60-90s for Zabbix DB init
python3 scripts/register_snmp_host.py
```

- Zabbix UI: `http://localhost:8080` (Admin / zabbix)
- Grafana: `http://localhost:3000` (admin / admin)

Grafana is pre-provisioned with the Zabbix datasource and a starter dashboard.

## SNMP Simulator
We run `snmpsim` exposing OIDs based on `simulators/snmpsim/data/public.snmprec`. The simulator is reachable as host `snmpsim` from the Zabbix container network and `localhost:161/udp` on the host.

Zabbix host created by the script uses:
- Hostname: `snmpsim-device`
- IP: `snmpsim`
- Community: `public`

## Zabbix Templates and Triggers
The registration script expects a common SNMP template like "Template Net SNMP". If missing, import a suitable template into Zabbix (Configuration → Templates), then re-run the script.

## NETCONF Simulator
A basic NETCONF server is exposed at port 830. It's present for future extension (e.g., device config audit), not used by the basic demo.

## Validation
1. Open Zabbix UI → Monitoring → Hosts → `snmpsim-device` should appear and start collecting after a few minutes.
2. In Grafana, open the "Zabbix Overview" dashboard. Add panels based on Zabbix metrics once data is flowing.

## Environment Variables (optional)
Script accepts overrides:
```bash
ZBX_URL=http://localhost:8080 ZBX_USER=Admin ZBX_PASS=zabbix \
SNMP_HOST_NAME=snmpsim-device SNMP_HOST_IP=snmpsim SNMP_COMMUNITY=public \
python3 scripts/register_snmp_host.py
```

## Tear Down
```bash
docker compose down -v
```

## Notes
- First data may take 1–3 minutes to show due to discovery and polling intervals.
- If Grafana errors on datasource, verify the Zabbix plugin is installed (environment `GF_INSTALL_PLUGINS`).

