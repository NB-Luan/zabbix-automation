#!/usr/bin/env python3
"""
zabbix_api_setup.py - Setup Custom Items and Triggers via Zabbix API
Target: Zabbix Server 7.0 LTS (192.168.56.10)
"""
import json
import sys
import urllib.request

ZABBIX_URL = "http://192.168.56.10/zabbix/api_jsonrpc.php"
ZABBIX_USER = "Admin"
ZABBIX_PASS = "zabbix"
TARGET_HOST = "web-server"


def api_call(method: str, params: dict, auth_token: str = None) -> dict:
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1,
    }
    if auth_token:
        payload["auth"] = auth_token

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        ZABBIX_URL,
        data=data,
        headers={"Content-Type": "application/json-rpc"},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        if "error" in res:
            raise RuntimeError(f"Zabbix API Error: {res['error']}")
        return res["result"]


def main():
    print(f"Connecting to Zabbix API at {ZABBIX_URL}...")
    auth = api_call("user.login", {"username": ZABBIX_USER, "password": ZABBIX_PASS})
    print("Authentication successful.")

    # 1. Get Host & Interface
    hosts = api_call("host.get", {"filter": {"host": [TARGET_HOST]}}, auth)
    if not hosts:
        print(f"[ERROR] Host '{TARGET_HOST}' not found!", file=sys.stderr)
        sys.exit(1)

    host_id = hosts[0]["hostid"]
    print(f"Found host '{TARGET_HOST}' (hostid: {host_id})")

    interfaces = api_call("hostinterface.get", {"hostids": [host_id]}, auth)
    if not interfaces:
        print(f"[ERROR] No interface found for host '{TARGET_HOST}'!", file=sys.stderr)
        sys.exit(1)

    interface_id = interfaces[0]["interfaceid"]
    print(f"Using interfaceid: {interface_id} ({interfaces[0]['ip']}:{interfaces[0]['port']})")

    # 2. Define Items to Create
    items_def = [
        {
            "name": "Nginx: HTTP Response Time",
            "key_": "custom.nginx.response_ms",
            "type": 0,          # Zabbix agent (passive)
            "value_type": 3,    # Numeric unsigned (ms)
            "units": "ms",
            "delay": "15s",
        },
        {
            "name": "Nginx: HTTP 5xx Error Count",
            "key_": "custom.nginx.error_5xx",
            "type": 0,
            "value_type": 3,    # Numeric unsigned
            "units": "",
            "delay": "15s",
        },
        {
            "name": "Nginx: Active Connections",
            "key_": "custom.nginx.active_conn",
            "type": 0,
            "value_type": 3,    # Numeric unsigned
            "units": "",
            "delay": "15s",
        },
        {
            "name": "System: Zombie Processes Count",
            "key_": "custom.sys.zombie_procs",
            "type": 0,
            "value_type": 3,    # Numeric unsigned
            "units": "",
            "delay": "15s",
        },
        {
            "name": "System: Failed Systemd Units Count",
            "key_": "custom.sys.failed_units",
            "type": 0,
            "value_type": 3,    # Numeric unsigned
            "units": "",
            "delay": "15s",
        },
        {
            "name": "System: Disk I/O Utilization",
            "key_": "custom.sys.disk_io_util",
            "type": 0,
            "value_type": 0,    # Numeric float
            "units": "%",
            "delay": "15s",
        },
    ]

    # Get existing items to avoid duplicates
    existing_items = api_call(
        "item.get",
        {"hostids": [host_id], "output": ["itemid", "name", "key_"]},
        auth,
    )
    existing_keys = {item["key_"]: item["itemid"] for item in existing_items}

    created_items = {}
    for item_spec in items_def:
        key = item_spec["key_"]
        if key in existing_keys:
            item_id = existing_keys[key]
            print(f"  [EXISTS] Item '{key}' already exists (itemid: {item_id})")
            created_items[key] = item_id
        else:
            create_params = {
                "name": item_spec["name"],
                "key_": key,
                "hostid": host_id,
                "type": item_spec["type"],
                "value_type": item_spec["value_type"],
                "interfaceid": interface_id,
                "delay": item_spec["delay"],
                "history": "7d",
                "trends": "365d",
            }
            if item_spec["units"]:
                create_params["units"] = item_spec["units"]

            res = api_call("item.create", create_params, auth)
            item_id = res["itemids"][0]
            print(f"  [CREATED] Item '{key}' created successfully (itemid: {item_id})")
            created_items[key] = item_id

    # 3. Define Triggers
    triggers_def = [
        {
            "description": f"Nginx HTTP 5xx errors detected on {TARGET_HOST}",
            "expression": f"last(/{TARGET_HOST}/custom.nginx.error_5xx)>0",
            "priority": 4,  # High
        },
        {
            "description": f"Failed systemd units detected on {TARGET_HOST}",
            "expression": f"last(/{TARGET_HOST}/custom.sys.failed_units)>0",
            "priority": 3,  # Average
        },
        {
            "description": f"Nginx high response latency on {TARGET_HOST} (> 500ms)",
            "expression": f"last(/{TARGET_HOST}/custom.nginx.response_ms)>500",
            "priority": 2,  # Warning
        },
    ]

    existing_triggers = api_call(
        "trigger.get",
        {"hostids": [host_id], "output": ["triggerid", "description"]},
        auth,
    )
    existing_desc = {t["description"]: t["triggerid"] for t in existing_triggers}

    created_triggers = {}
    for trig_spec in triggers_def:
        desc = trig_spec["description"]
        if desc in existing_desc:
            trig_id = existing_desc[desc]
            print(f"  [EXISTS] Trigger '{desc}' already exists (triggerid: {trig_id})")
            created_triggers[desc] = trig_id
        else:
            res = api_call(
                "trigger.create",
                {
                    "description": desc,
                    "expression": trig_spec["expression"],
                    "priority": trig_spec["priority"],
                },
                auth,
            )
            trig_id = res["triggerids"][0]
            print(f"  [CREATED] Trigger '{desc}' created successfully (triggerid: {trig_id})")
            created_triggers[desc] = trig_id

    print("\n--- Summary ---")
    print(f"Host: {TARGET_HOST} (hostid: {host_id})")
    print(f"Items managed: {len(created_items)}")
    print(f"Triggers managed: {len(created_triggers)}")


if __name__ == "__main__":
    main()
