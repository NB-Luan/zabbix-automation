#!/usr/bin/env python3
"""
zabbix_api_setup.py - Full Zabbix Server Setup & Verification via Zabbix JSON-RPC API
Target: Zabbix Server 7.0 LTS (Default: 192.168.56.10)
Host: web-server (Default: 192.168.56.21)
"""
import json
import os
import sys
import time
import urllib.request


def load_env_file():
    """Load key-value pairs from .env file if present in the project root."""
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    if os.path.isfile(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    if key and key not in os.environ:
                        os.environ[key] = val


load_env_file()

ZABBIX_SERVER_IP = os.environ.get("ZABBIX_SERVER_IP", "192.168.56.10")
ZABBIX_URL = os.environ.get("ZABBIX_API_URL", f"http://{ZABBIX_SERVER_IP}/zabbix/api_jsonrpc.php")
ZABBIX_USER = os.environ.get("ZABBIX_API_USER", "Admin")
ZABBIX_PASS = os.environ.get("ZABBIX_API_PASS", "zabbix")
TARGET_HOST = os.environ.get("TARGET_HOST_NAME", "web-server")
STUB_STATUS_PORT = os.environ.get("WEB_SERVER_STUB_PORT", "8080")


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
    print(f"Target Host: '{TARGET_HOST}' (hostid: {host_id})")

    interfaces = api_call("hostinterface.get", {"hostids": [host_id]}, auth)
    if not interfaces:
        print(f"[ERROR] No interface found for host '{TARGET_HOST}'!", file=sys.stderr)
        sys.exit(1)

    interface_id = interfaces[0]["interfaceid"]
    print(f"Interface: {interface_id} ({interfaces[0]['ip']}:{interfaces[0]['port']})")

    # 2. Configure Host Macro for Nginx stub_status port
    existing_macros = api_call("usermacro.get", {"hostids": [host_id]}, auth)
    macro_name = "{$NGINX.STUB_STATUS.PORT}"
    macro_found = False
    for m in existing_macros:
        if m["macro"] == macro_name:
            macro_found = True
            if m["value"] != STUB_STATUS_PORT:
                api_call("usermacro.update", {"hostmacroid": m["hostmacroid"], "value": STUB_STATUS_PORT}, auth)
                print(f"  [UPDATED] Macro {macro_name} updated to {STUB_STATUS_PORT}")
            else:
                print(f"  [EXISTS] Macro {macro_name} = {STUB_STATUS_PORT}")
            break

    if not macro_found:
        api_call("usermacro.create", {"hostid": host_id, "macro": macro_name, "value": STUB_STATUS_PORT}, auth)
        print(f"  [CREATED] Macro {macro_name} = {STUB_STATUS_PORT}")

    # 3. Define & Create Custom Items
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
            "value_type": 3,
            "units": "",
            "delay": "15s",
        },
        {
            "name": "Nginx: Active Connections",
            "key_": "custom.nginx.active_conn",
            "type": 0,
            "value_type": 3,
            "units": "",
            "delay": "15s",
        },
        {
            "name": "System: Zombie Processes Count",
            "key_": "custom.sys.zombie_procs",
            "type": 0,
            "value_type": 3,
            "units": "",
            "delay": "15s",
        },
        {
            "name": "System: Failed Systemd Units Count",
            "key_": "custom.sys.failed_units",
            "type": 0,
            "value_type": 3,
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
            print(f"  [CREATED] Item '{key}' (itemid: {item_id})")
            created_items[key] = item_id

    # 4. Define & Create Custom Triggers
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
            created_triggers[desc] = existing_desc[desc]
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
            print(f"  [CREATED] Trigger '{desc}' (triggerid: {trig_id})")
            created_triggers[desc] = trig_id

    # 5. Trigger Instant Polling (Execute Now) for Custom Items
    task_requests = [{"type": 6, "request": {"itemid": i_id}} for i_id in created_items.values()]
    try:
        api_call("task.create", task_requests, auth)
        time.sleep(2)
    except Exception:
        pass

    # 6. Display Current Status Report
    monitored_items = api_call(
        "item.get",
        {
            "hostids": [host_id],
            "itemids": list(created_items.values()),
            "output": ["itemid", "name", "key_", "lastvalue", "state", "error"],
        },
        auth,
    )

    print("\n" + "=" * 70)
    print("  ZABBIX SERVER: VERIFIED CUSTOM ITEMS STATUS")
    print("=" * 70)
    for it in sorted(monitored_items, key=lambda x: x["key_"]):
        st = "Supported" if it["state"] == "0" else f"Unsupported ({it['error']})"
        print(f"  Key: {it['key_']:<25} | Val: {it['lastvalue']:<8} | State: {st}")

    print("\n" + "=" * 70)
    print("  ZABBIX SERVER: VERIFIED CUSTOM TRIGGERS STATUS")
    print("=" * 70)
    p_names = {"2": "Warning", "3": "Average", "4": "High"}
    monitored_triggers = api_call(
        "trigger.get",
        {
            "triggerids": list(created_triggers.values()),
            "output": ["triggerid", "description", "priority", "value"],
        },
        auth,
    )
    for tr in monitored_triggers:
        val_str = "OK" if tr["value"] == "0" else "PROBLEM"
        sev = p_names.get(tr["priority"], tr["priority"])
        print(f"  Trigger: {tr['description']:<52} | Sev: {sev:<8} | Status: {val_str}")
    print("=" * 70)


if __name__ == "__main__":
    main()
