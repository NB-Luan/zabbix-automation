# Interface Contracts: Zabbix Agent 2 UserParameter & CLI APIs

**Feature**: `001-vm2-extended-monitoring` | **Date**: 2026-11-15

This contract specification details the communication interface between Zabbix Agent 2 and the underlying shell monitoring scripts, as well as the CLI interface contracts for simulation and deployment tooling.

---

## 1. Zabbix Agent 2 UserParameter Contracts

### 1.1 `custom.nginx.[*]` Contract
- **Agent Configuration Directive**:
  ```apache
  UserParameter=custom.nginx.[*],/usr/local/bin/nginx_custom_metrics.sh "$1"
  ```
- **Supported Parameters**:
  - `response_ms`:
    - **Input**: Literal string `"response_ms"`
    - **Stdout**: Single integer representing response latency in milliseconds (e.g., `42`).
    - **Stderr**: Empty (`/dev/null`).
    - **Exit Code**: `0` (Always).
    - **Error Fallback**: Outputs `0` if service unreachable or connection times out.
  - `error_5xx`:
    - **Input**: Literal string `"error_5xx"`
    - **Stdout**: Single integer count of 5xx errors found in log (e.g., `0` or `12`).
    - **Stderr**: Empty (`/dev/null`).
    - **Exit Code**: `0` (Always).
    - **Error Fallback**: Outputs `0` if log is empty or unreadable.
  - `active_conn`:
    - **Input**: Literal string `"active_conn"`
    - **Stdout**: Single integer count of active connections (e.g., `3`).
    - **Stderr**: Empty (`/dev/null`).
    - **Exit Code**: `0` (Always).
    - **Error Fallback**: Outputs `0` if stub_status endpoint is unavailable.

### 1.2 `custom.sys.[*]` Contract
- **Agent Configuration Directive**:
  ```apache
  UserParameter=custom.sys.[*],/usr/local/bin/system_health_check.sh "$1"
  ```
- **Supported Parameters**:
  - `zombie_procs`:
    - **Input**: Literal string `"zombie_procs"`
    - **Stdout**: Single integer count of defunct processes (e.g., `0`).
    - **Stderr**: Empty (`/dev/null`).
    - **Exit Code**: `0` (Always).
  - `failed_units`:
    - **Input**: Literal string `"failed_units"`
    - **Stdout**: Single integer count of failed systemd units (e.g., `0`).
    - **Stderr**: Empty (`/dev/null`).
    - **Exit Code**: `0` (Always).
  - `disk_io_util`:
    - **Input**: Literal string `"disk_io_util"`
    - **Stdout**: Floating-point number formatted to one decimal place representing percentage utilization (e.g., `4.5` or `0.0`).
    - **Stderr**: Empty (`/dev/null`).
    - **Exit Code**: `0` (Always).

---

## 2. Interactive Incident Simulator CLI Contract (`tests/simulate_incident.sh`)

### 2.1 Interactive Mode (No Arguments)
- **Invocation**: `bash simulate_incident.sh`
- **Standard In**: Terminal key inputs `1`, `2`, `3`, or `0`.
- **Standard Out**: ASCII banner, status updates, countdown timers, and completion messages.

### 2.2 Non-Interactive Automated Flags
- **Invocation Syntax**: `simulate_incident.sh [FLAG]`
  - `--stress`: Runs Mode 1 (CPU/RAM stress) non-interactively for 60 seconds and exits 0.
  - `--storm`: Runs Mode 2 (1,000 HTTP requests) non-interactively and exits 0.
  - `--outage`: Runs Mode 3 (45-second Nginx shutdown & restart) non-interactively and exits 0.
  - `--help` / `-h`: Displays usage instructions and supported flags.

---

## 3. Remote Deployment Automation Contract (`deploy.ps1`)

### 3.1 Parameters and Environment Defaults
- **Script**: `deploy.ps1`
- **Syntax**: `.\deploy.ps1 [-TargetHost <IP>] [-User <Username>] [-KeyFile <Path>]`
  - `-TargetHost`: Target IPv4 address. Default: `192.168.56.21` (Constitution Principle II).
  - `-User`: SSH username. Default: `linux-moniter` (Constitution Principle II).
  - `-KeyFile`: Optional path to private SSH key. Defaults to standard user SSH profile (`~/.ssh/id_rsa` or SSH agent).
- **Execution Flow**:
  1. Validates local repository files.
  2. Creates remote staging folder `/tmp/zabbix_deploy/` via SSH.
  3. Copies files via `scp.exe -r`.
  4. Triggers remote execution of `deploy.sh`.
  5. Displays live test report from `zabbix_agent2 -t`.
  6. Returns exit code `0` on 100% test pass; returns exit code `1` if any key test fails.
