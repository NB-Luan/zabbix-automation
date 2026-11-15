import json
import urllib.request

ZABBIX_URL = "http://192.168.56.10/zabbix/api_jsonrpc.php"
ZABBIX_USER = "Admin"
ZABBIX_PASS = "zabbix"


def api_call(method, params, auth=None):
    payload = {"jsonrpc": "2.0", "method": method, "params": params, "id": 1}
    if auth:
        payload["auth"] = auth
    req = urllib.request.Request(
        ZABBIX_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json-rpc"},
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))["result"]


def main():
    auth = api_call("user.login", {"username": ZABBIX_USER, "password": ZABBIX_PASS})

    items = api_call(
        "item.get",
        {
            "hostids": ["10680"],
            "search": {"key_": "custom."},
            "output": ["itemid", "name", "key_", "lastvalue", "lastclock", "state", "error"],
        },
        auth,
    )

    triggers = api_call(
        "trigger.get",
        {
            "hostids": ["10680"],
            "output": ["triggerid", "description", "priority", "value", "state"],
        },
        auth,
    )

    print("=== MONITORED ITEMS ===")
    for item in sorted(items, key=lambda x: x["key_"]):
        st = "Supported" if item["state"] == "0" else f"Unsupported ({item['error']})"
        print(f"Key: {item['key_']:<25} | ID: {item['itemid']:<6} | Value: {item['lastvalue']:<8} | State: {st}")

    print("\n=== ACTIVE CUSTOM TRIGGERS ===")
    p_names = {"2": "Warning", "3": "Average", "4": "High"}
    custom_trigs = [t for t in triggers if t["triggerid"] in ["25276", "25277", "25278"]]
    for trig in custom_trigs:
        val_str = "OK" if trig["value"] == "0" else "PROBLEM"
        sev = p_names.get(trig["priority"], trig["priority"])
        print(f"Trigger: {trig['description']:<55} | ID: {trig['triggerid']:<6} | Severity: {sev:<8} | Status: {val_str}")


if __name__ == "__main__":
    main()
