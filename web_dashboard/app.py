#!/usr/bin/env python3
"""
app.py - Real-Time NOC Web Dashboard for Zabbix Monitoring & Remote Chaos Testing
Platform: Flask + TailwindCSS + Chart.js
"""
import datetime
import json
import os
import threading
import time
import urllib.request
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

# ==============================================================================
# Configuration & Environment
# ==============================================================================
def load_env():
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    if os.path.isfile(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    if k and k not in os.environ:
                        os.environ[k] = v

load_env()

ZABBIX_SERVER_IP = os.environ.get("ZABBIX_SERVER_IP", "192.168.56.10")
ZABBIX_API_URL = os.environ.get("ZABBIX_API_URL", f"http://{ZABBIX_SERVER_IP}/zabbix/api_jsonrpc.php")
ZABBIX_API_USER = os.environ.get("ZABBIX_API_USER", "Admin")
ZABBIX_API_PASS = os.environ.get("ZABBIX_API_PASS", "zabbix")
TARGET_HOST_NAME = os.environ.get("TARGET_HOST_NAME", "web-server")

WEB_SERVER_IP = os.environ.get("WEB_SERVER_IP", "192.168.56.21")
WEB_SERVER_USER = os.environ.get("WEB_SERVER_USER", "linux-moniter")
WEB_SERVER_PORT = int(os.environ.get("WEB_SERVER_PORT", "22"))
SSH_KEY_FILE = os.environ.get("SSH_KEY_FILE", "")

zabbix_auth_token = None
cached_host_id = None

# Background Simulation State
sim_state = {
    "is_running": False,
    "current_task": None,
    "start_time": None,
    "logs": [f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Dashboard initialized. Ready for operations."]
}
sim_lock = threading.Lock()


# ==============================================================================
# Zabbix JSON-RPC API Client
# ==============================================================================
def call_zabbix_api(method: str, params: dict, retry: bool = True):
    global zabbix_auth_token
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": int(time.time() * 1000) % 100000
    }
    if zabbix_auth_token and method != "user.login":
        payload["auth"] = zabbix_auth_token

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        ZABBIX_API_URL,
        data=data,
        headers={"Content-Type": "application/json-rpc"}
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            if "error" in res:
                # If session invalid, relogin once
                if retry and ("Session terminated" in str(res["error"]) or "Not authorized" in str(res["error"])):
                    login_zabbix()
                    return call_zabbix_api(method, params, retry=False)
                raise RuntimeError(str(res["error"]))
            return res.get("result")
    except Exception as e:
        if retry and "401" in str(e):
            login_zabbix()
            return call_zabbix_api(method, params, retry=False)
        raise e


def login_zabbix():
    global zabbix_auth_token
    res = call_zabbix_api("user.login", {"username": ZABBIX_API_USER, "password": ZABBIX_API_PASS}, retry=False)
    zabbix_auth_token = res
    return res


def get_target_host_id():
    global cached_host_id
    if cached_host_id:
        return cached_host_id
    hosts = call_zabbix_api("host.get", {"filter": {"host": [TARGET_HOST_NAME]}})
    if hosts:
        cached_host_id = hosts[0]["hostid"]
        return cached_host_id
    return None


# ==============================================================================
# SSH Command Runner
# ==============================================================================
def get_ssh_key():
    import paramiko
    if SSH_KEY_FILE and os.path.isfile(SSH_KEY_FILE):
        for key_class in [paramiko.Ed25519Key, paramiko.RSAKey]:
            try:
                return key_class.from_private_key_file(SSH_KEY_FILE)
            except Exception:
                pass

    user_home = os.path.expanduser("~")
    for fname, key_class in [
        (".ssh/id_ed25519", paramiko.Ed25519Key),
        (".ssh/id_rsa", paramiko.RSAKey)
    ]:
        kpath = os.path.join(user_home, fname)
        if os.path.isfile(kpath):
            try:
                return key_class.from_private_key_file(kpath)
            except Exception:
                pass
    return None


def execute_ssh_remote_task(cmd: str, task_name: str):
    import paramiko
    global sim_state
    
    with sim_lock:
        sim_state["is_running"] = True
        sim_state["current_task"] = task_name
        sim_state["start_time"] = time.time()
        sim_state["logs"].append(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [SSH] Connecting to {WEB_SERVER_USER}@{WEB_SERVER_IP}:{WEB_SERVER_PORT}...")

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        pkey = get_ssh_key()
        client.connect(
            hostname=WEB_SERVER_IP,
            port=WEB_SERVER_PORT,
            username=WEB_SERVER_USER,
            pkey=pkey,
            timeout=8
        )
        with sim_lock:
            sim_state["logs"].append(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [SSH] Connected. Executing: {cmd}")

        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)

        for line in iter(stdout.readline, ""):
            line_str = line.strip()
            if line_str:
                with sim_lock:
                    sim_state["logs"].append(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {line_str}")

        exit_code = stdout.channel.recv_exit_status()
        with sim_lock:
            status_text = "SUCCESS" if exit_code == 0 else f"FAILED (Exit Code: {exit_code})"
            sim_state["logs"].append(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [TASK FINISHED] {task_name}: {status_text}")
    except Exception as e:
        with sim_lock:
            sim_state["logs"].append(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [ERROR] SSH Exception: {str(e)}")
    finally:
        try:
            client.close()
        except Exception:
            pass
        with sim_lock:
            sim_state["is_running"] = False
            sim_state["current_task"] = None


# ==============================================================================
# Web Routes
# ==============================================================================
@app.route("/")
def index():
    return render_template(
        "index.html",
        host_name=TARGET_HOST_NAME,
        web_server_ip=WEB_SERVER_IP,
        zabbix_server_ip=ZABBIX_SERVER_IP
    )


@app.route("/api/metrics")
def api_metrics():
    try:
        host_id = get_target_host_id()
        if not host_id:
            return jsonify({"status": "error", "message": f"Host '{TARGET_HOST_NAME}' not found"}), 404

        items = call_zabbix_api("item.get", {
            "hostids": [host_id],
            "search": {"key_": "custom."},
            "output": ["key_", "lastvalue", "lastclock", "state"]
        })

        metrics = {
            "response_ms": 0,
            "active_conn": 0,
            "error_5xx": 0,
            "zombie_procs": 0,
            "failed_units": 0,
            "disk_io_util": 0.0,
            "updated_at": datetime.datetime.now().strftime("%H:%M:%S")
        }

        for it in items:
            key = it["key_"]
            val = it.get("lastvalue", "0")
            if "response_ms" in key:
                try: metrics["response_ms"] = int(val)
                except ValueError: metrics["response_ms"] = 0
            elif "active_conn" in key:
                try: metrics["active_conn"] = int(val)
                except ValueError: metrics["active_conn"] = 0
            elif "error_5xx" in key:
                try: metrics["error_5xx"] = int(val)
                except ValueError: metrics["error_5xx"] = 0
            elif "zombie_procs" in key:
                try: metrics["zombie_procs"] = int(val)
                except ValueError: metrics["zombie_procs"] = 0
            elif "failed_units" in key:
                try: metrics["failed_units"] = int(val)
                except ValueError: metrics["failed_units"] = 0
            elif "disk_io_util" in key:
                try: metrics["disk_io_util"] = round(float(val), 2)
                except ValueError: metrics["disk_io_util"] = 0.0

        return jsonify({"status": "ok", "data": metrics})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/problems")
def api_problems():
    try:
        host_id = get_target_host_id()
        if not host_id:
            return jsonify({"status": "ok", "problems": []})

        raw_problems = call_zabbix_api("problem.get", {
            "hostids": [host_id],
            "output": ["eventid", "name", "severity", "clock", "r_clock"]
        })

        severity_map = {
            "0": "Not classified",
            "1": "Information",
            "2": "Warning",
            "3": "Average",
            "4": "High",
            "5": "Disaster"
        }

        now = int(time.time())
        problems = []
        for p in raw_problems:
            duration_sec = now - int(p.get("clock", now))
            mins, secs = divmod(duration_sec, 60)
            hours, mins = divmod(mins, 60)
            duration_str = f"{hours}h {mins}m {secs}s" if hours > 0 else f"{mins}m {secs}s"

            time_str = datetime.datetime.fromtimestamp(int(p.get("clock", now))).strftime("%H:%M:%S")
            problems.append({
                "id": p["eventid"],
                "name": p["name"],
                "severity_code": p["severity"],
                "severity": severity_map.get(p["severity"], "Warning"),
                "duration": duration_str,
                "time": time_str
            })

        return jsonify({"status": "ok", "problems": problems, "count": len(problems)})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/simulate", methods=["POST"])
def api_simulate():
    data = request.get_json(silent=True) or {}
    mode = data.get("mode")

    cmd_map = {
        "storm": ("~/simulate_incident.sh --storm", "HTTP Request Storm (1,000 reqs)"),
        "stress": ("~/simulate_incident.sh --stress", "CPU & RAM Stress (60 seconds)"),
        "outage": ("~/simulate_incident.sh --outage", "Nginx Outage (45s stop & auto-recover)")
    }

    if mode not in cmd_map:
        return jsonify({"status": "error", "message": f"Invalid mode '{mode}'"}), 400

    with sim_lock:
        if sim_state["is_running"]:
            return jsonify({
                "status": "busy",
                "message": f"Another task ({sim_state['current_task']}) is currently executing!"
            }), 409

    cmd, title = cmd_map[mode]
    t = threading.Thread(target=execute_ssh_remote_task, args=(cmd, title), daemon=True)
    t.start()

    return jsonify({"status": "started", "task": title})


@app.route("/api/logs")
def api_logs():
    with sim_lock:
        return jsonify({
            "is_running": sim_state["is_running"],
            "current_task": sim_state["current_task"],
            "logs": sim_state["logs"][-60:]
        })


@app.route("/api/logs/clear", methods=["POST"])
def api_logs_clear():
    with sim_lock:
        sim_state["logs"] = [f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Terminal logs cleared."]
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    print("=" * 70)
    print("  Starting Zabbix Monitoring Web Dashboard")
    print(f"  Zabbix Server: {ZABBIX_API_URL}")
    print(f"  Target Host  : {TARGET_HOST_NAME} ({WEB_SERVER_IP})")
    print("  Dashboard URL: http://localhost:5000")
    print("=" * 70)
    app.run(host="0.0.0.0", port=5000, debug=False)
