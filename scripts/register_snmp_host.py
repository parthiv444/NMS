#!/usr/bin/env python3
import os
import sys
import time
import requests

ZBX_URL = os.getenv("ZBX_URL", "http://localhost:8080")
ZBX_USER = os.getenv("ZBX_USER", "Admin")
ZBX_PASS = os.getenv("ZBX_PASS", "zabbix")

HOST_NAME = os.getenv("SNMP_HOST_NAME", "snmpsim-device")
HOST_IP = os.getenv("SNMP_HOST_IP", "snmpsim")
SNMP_COMMUNITY = os.getenv("SNMP_COMMUNITY", "public")

HEADERS = {"Content-Type": "application/json-rpc"}


def zbx_api(method, params, auth=None, id_=1):
    payload = {"jsonrpc": "2.0", "method": method, "params": params, "id": id_}
    if auth:
        payload["auth"] = auth
    resp = requests.post(f"{ZBX_URL}/api_jsonrpc.php", json=payload, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if "error" in data:
        raise RuntimeError(data["error"]) 
    return data["result"]


def login():
    return zbx_api("user.login", {"username": ZBX_USER, "password": ZBX_PASS})


def ensure_snmp_interface_group(auth):
    groups = zbx_api("hostgroup.get", {"filter": {"name": ["Discovered hosts", "SNMP devices"]}}, auth)
    target_name = "SNMP devices"
    for g in groups:
        if g["name"] == target_name:
            return g["groupid"]
    res = zbx_api("hostgroup.create", {"name": target_name}, auth)
    return res["groupids"][0]


def get_snmp_template(auth):
    # Try common template names in Zabbix 6.x
    candidates = [
        "Linux by SNMP",
        "Template Module ICMP Ping",
        "Template Net SNMP",
        "Template OS Linux by SNMP",
    ]
    res = zbx_api("template.get", {"output": ["templateid", "name"], "filter": {"name": candidates}}, auth)
    if not res:
        # Return None if no template found - we'll create host without template
        return None
    # Prefer SNMP templates
    res.sort(key=lambda t: 0 if "SNMP" in t["name"] else 1)
    return res[0]["templateid"]


def ensure_host(auth, groupid, templateid):
    hosts = zbx_api("host.get", {"filter": {"host": [HOST_NAME]}}, auth)
    if hosts:
        return hosts[0]["hostid"]
    params = {
        "host": HOST_NAME,
        "name": HOST_NAME,
        "interfaces": [
            {
                "type": 2,  # SNMP
                "main": 1,
                "useip": 1,
                "ip": HOST_IP,
                "dns": "",
                "port": "161",
                "details": {
                    "version": 2,
                    "community": SNMP_COMMUNITY
                }
            }
        ],
        "groups": [{"groupid": groupid}],
    }
    if templateid:
        params["templates"] = [{"templateid": templateid}]
    res = zbx_api("host.create", params, auth)
    return res["hostids"][0]


def main():
    try:
        auth = login()
        groupid = ensure_snmp_interface_group(auth)
        templateid = get_snmp_template(auth)
        hostid = ensure_host(auth, groupid, templateid)
        if templateid:
            print(f"✓ Registered host '{HOST_NAME}' (id={hostid}) with template (id={templateid})")
        else:
            print(f"✓ Registered host '{HOST_NAME}' (id={hostid}) without template")
            print("  You can link SNMP templates manually via Zabbix UI")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()



