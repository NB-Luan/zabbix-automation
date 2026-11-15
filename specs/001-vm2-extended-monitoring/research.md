# Technical Research & Architecture Decisions: VM2 Extended Monitoring

**Feature**: `001-vm2-extended-monitoring` | **Date**: 2026-11-15

This document records the technical investigation, benchmarking, and architectural decisions made for the custom Zabbix Agent 2 monitoring scripts, incident simulator, and Windows-to-Ubuntu automated deployment pipeline.

---

## 1. Nginx Custom Metrics Collection (`scripts/nginx_custom_metrics.sh`)

### 1.1 HTTP Response Time (`response_ms`)
- **Decision**: Measure elapsed HTTP latency using `curl -o /dev/null -s -w "%{time_total}\n" --max-time 2 http://127.0.0.1:80/` and convert seconds to integer milliseconds using `awk '{printf "%.0f\n", $1 * 1000}'`.
- **Rationale**:
  - `curl` is pre-installed on Ubuntu 26.04 LTS and introduces zero external dependencies.
  - `--max-time 2` ensures execution never exceeds 2 seconds, well below the Zabbix Agent default timeout (3 seconds).
  - Outputting in integer milliseconds provides clean metric charting and simplifies trigger threshold definition in Zabbix Server.
- **Fail-Safe Mechanism**: If `curl` exits with a non-zero status (e.g., connection refused when Nginx is down) or output is empty, the script outputs `0` and exits with code 0.
- **Alternatives Considered**:
  - `wget`: Does not provide granular millisecond-level time write-out variables.
  - Python `urllib` / `requests`: Slower process startup overhead (~50-100ms) compared to native `curl` (<10ms).

### 1.2 HTTP 5xx Server Error Frequency (`error_5xx`)
- **Decision**: Scan `/var/log/nginx/access.log` using `awk` to match HTTP status codes between 500 and 599:
  ```bash
  awk '$9 ~ /^5[0-9]{2}$/ {count++} END {print count+0}' /var/log/nginx/access.log 2>/dev/null || echo 0
  ```
- **Rationale**:
  - In standard Nginx combined log format, field 9 (`$9`) represents the HTTP response code.
  - Matching on field 9 prevents false positives (e.g., URL parameters or user-agents that happen to contain "500").
  - `count+0` in `awk` guarantees an integer `0` is emitted even if no matching lines exist or the log is empty.
- **Fail-Safe Mechanism**: If the log file is missing or unreadable by user `zabbix`, the command returns `0` with exit code 0.

### 1.3 Active Connections from `stub_status` (`active_conn`)
- **Decision**: Query `http://127.0.0.1:8080/basic_status` with `curl -s --max-time 2` and extract the integer after `Active connections:`:
  ```bash
  curl -s --max-time 2 http://127.0.0.1:8080/basic_status | awk '/Active connections:/ {print $3}'
  ```
- **Rationale**:
  - Nginx's `ngx_http_stub_status_module` provides the exact current connection load.
  - Port 8080 is reserved for local metrics per Constitution Principle II.
- **Fail-Safe Mechanism**: Validates that the parsed output is non-empty and strictly numeric (`^[0-9]+$`). If validation fails, emits `0` and exits with code 0.

---

## 2. Linux System Health Monitoring (`scripts/system_health_check.sh`)

### 2.1 Zombie Process Detection (`zombie_procs`)
- **Decision**: Interrogate process state flags via `ps -eo stat=` and count states starting with `Z`:
  ```bash
  ps -eo stat= 2>/dev/null | grep -c '^Z' || echo 0
  ```
- **Rationale**:
  - `ps -eo stat=` omits column headers and prints state flags directly.
  - `grep -c '^Z'` returns the exact count of defunct/zombie threads and processes.
- **Fail-Safe Mechanism**: Returns `0` if `ps` fails.

### 2.2 Failed Systemd Units (`failed_units`)
- **Decision**: Query systemd manager for failed units using:
  ```bash
  systemctl list-units --state=failed --no-legend --no-pager 2>/dev/null | grep -c '[^[:space:]]' || echo 0
  ```
- **Rationale**:
  - `--state=failed --no-legend` suppresses table headers, borders, and footer text, leaving only lines corresponding to broken units.
  - Does not require root privileges for unit state queries.
- **Fail-Safe Mechanism**: Emits `0` if systemd daemon is unreachable or query errors occur.

### 2.3 Disk I/O Utilization Percentage (`disk_io_util`)
- **Decision**: Extract `%util` from `iostat` (from `sysstat` package) sampling over 1 second:
  ```bash
  iostat -dx 1 2 2>/dev/null | awk '/^[vsh]d[a-z]|nvme/ {util=$NF} END {if (util != "") print util; else print "0.0"}'
  ```
- **Rationale**:
  - Running `iostat` with `1 2` discards the first cumulative sample since boot and uses the second real-time 1-second delta.
  - Supports virtual disk identifiers (`sda`, `vda`, `hda`, `nvme0n1`).
- **Fail-Safe Mechanism**: If `iostat` is not installed or device cannot be detected, outputs `0.0` with exit code 0.

---

## 3. Zabbix Agent 2 Configuration (`configs/custom_monitor.conf`)

### 3.1 Namespace & Parameter Mapping
- **Decision**: Implement flexible UserParameter syntax with single-argument routing:
  ```apache
  # Nginx Custom Metrics
  UserParameter=custom.nginx.[*],/usr/local/bin/nginx_custom_metrics.sh "$1"

  # System Health Metrics
  UserParameter=custom.sys.[*],/usr/local/bin/system_health_check.sh "$1"
  ```
- **Rationale**:
  - Allows adding new sub-metrics without modifying `/etc/zabbix/zabbix_agent2.d/` configurations.
  - Quotation around `"$1"` prevents shell injection.
  - Matches the user specification keys: `custom.nginx.response_ms`, `custom.nginx.error_5xx`, `custom.nginx.active_conn`, `custom.sys.zombie_procs`, `custom.sys.failed_units`, `custom.sys.disk_io_util`.

---

## 4. Incident Simulator Suite (`tests/simulate_incident.sh`)

### 4.1 Mode 1: CPU & RAM Stress (60 seconds)
- **Decision**: Check for `stress-ng`. If absent, automatically run `sudo apt-get update -y && sudo apt-get install -y stress-ng`. Then execute:
  ```bash
  stress-ng --cpu 2 --vm 1 --vm-bytes 70% --timeout 60s --metrics-brief
  ```
- **Rationale**: Generates measurable CPU and memory saturation to trip system load triggers in Zabbix without causing kernel panic or VM lockup.

### 4.2 Mode 2: 1,000 HTTP Request Storm
- **Decision**: Use an optimized Bash loop or `seq 1000 | xargs -n 1 -P 10 curl -s -o /dev/null http://127.0.0.1:80/`.
- **Rationale**: Concurrent curl requests simulate burst traffic and increase active connection count without requiring external load generator tools.

### 4.3 Mode 3: Nginx Service Outage (45 seconds)
- **Decision**: Execute `sudo systemctl stop nginx`, sleep for 45 seconds, execute `sudo systemctl start nginx`, and verify `systemctl is-active nginx`.
- **Rationale**: A 45-second interruption is sufficient for standard Zabbix 30-second poll cycles to trigger "Nginx is down" alarms and verify the automatic recovery trigger.

---

## 5. Automated Deployment Pipeline (`deploy.ps1` & `deploy.sh`)

### 5.1 Windows Orchestration (`deploy.ps1`)
- **Decision**: Pure PowerShell script utilizing native Windows OpenSSH (`scp.exe`, `ssh.exe`).
- **Steps**:
  1. Verify local source files exist.
  2. Stage files to target VM2 at `/tmp/zabbix_deploy/` via `scp -r`.
  3. Invoke `deploy.sh` remotely via `ssh linux-moniter@192.168.56.21 "bash /tmp/zabbix_deploy/deploy.sh"`.
  4. Capture and display exit status and test report.

### 5.2 Remote Staging & Sanitization (`deploy.sh`)
- **Decision**: Runs directly on VM2 as `linux-moniter`:
  1. Sanitizes line endings for all staged `.sh` and `.conf` files: `sed -i 's/\r$//' /tmp/zabbix_deploy/...`
  2. Copies scripts to `/usr/local/bin/` with `chmod 755`.
  3. Copies config to `/etc/zabbix/zabbix_agent2.d/custom_monitor.conf`.
  4. Restarts `zabbix-agent2` via `sudo systemctl restart zabbix-agent2`.
  5. Performs end-to-end verification using `zabbix_agent2 -t <key>` for all 6 items.
  6. Cleans up `/tmp/zabbix_deploy/`.
