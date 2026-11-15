# Quickstart Validation Guide: VM2 Extended Monitoring

**Feature**: `001-vm2-extended-monitoring` | **Date**: 2026-11-15

This guide provides step-by-step instructions to deploy, verify, and execute incident simulations for the VM2 monitoring extension.

---

## 1. Prerequisites

Before running the deployment, ensure the following conditions are met:
1. **Host Connectivity**: Windows development workstation can ping VM2 at `192.168.56.21`.
2. **SSH Access**: SSH key authentication or credentials are configured for user `linux-moniter@192.168.56.21`.
3. **VM2 Services**: `nginx` and `zabbix-agent2` services are installed on VM2.

---

## 2. Automated Deployment Execution

From the Windows workstation PowerShell terminal, run:

```powershell
# Execute the full automated deployment pipeline to VM2
.\deploy.ps1
```

### Expected Output
- Local files validated.
- SCP file transfer completed to `/tmp/zabbix_deploy/`.
- Remote line ending sanitization (LF conversion) completed.
- Scripts installed to `/usr/local/bin/` with `0755` permissions.
- Configuration deployed to `/etc/zabbix/zabbix_agent2.d/custom_monitor.conf`.
- `zabbix-agent2` restarted successfully.
- Verification summary showing all 6 keys tested and passing:
  ```text
  [PASS] custom.nginx.response_ms  => [s|XX]
  [PASS] custom.nginx.error_5xx    => [u|0]
  [PASS] custom.nginx.active_conn  => [u|1]
  [PASS] custom.sys.zombie_procs   => [u|0]
  [PASS] custom.sys.failed_units   => [u|0]
  [PASS] custom.sys.disk_io_util   => [d|X.X]
  Deployment completed successfully!
  ```

---

## 3. Manual Metric Verification on VM2

Log in to VM2 via SSH to test individual keys:

```bash
ssh linux-moniter@192.168.56.21
```

### Test 1: Active Web Metrics (Normal Operation)
```bash
zabbix_agent2 -t custom.nginx.response_ms
zabbix_agent2 -t custom.nginx.active_conn
zabbix_agent2 -t custom.nginx.error_5xx
```
*Expected Outcome*: All return numerical values with return code 0.

### Test 2: System Health Metrics
```bash
zabbix_agent2 -t custom.sys.zombie_procs
zabbix_agent2 -t custom.sys.failed_units
zabbix_agent2 -t custom.sys.disk_io_util
```
*Expected Outcome*: Return process counts, failed units count, and disk I/O percentage.

### Test 3: Fail-Safe Handling (Simulated Outage)
```bash
# Temporarily stop Nginx
sudo systemctl stop nginx

# Poll custom metrics
zabbix_agent2 -t custom.nginx.response_ms
zabbix_agent2 -t custom.nginx.active_conn

# Expected: Output is 0, exit code is 0 (No "Unsupported item" error)

# Restore Nginx
sudo systemctl start nginx
```

---

## 4. Running Incident Simulation Suite

On VM2, launch the interactive simulation tool:

```bash
~/simulate_incident.sh
```

### Scenario Execution:
1. **Option 1 (CPU/RAM Stress)**:
   - Type `1` and press `Enter`.
   - Observe 60-second stress countdown. Check CPU utilization graph on Zabbix Server dashboard.
2. **Option 2 (HTTP Request Storm)**:
   - Type `2` and press `Enter`.
   - Sends 1,000 requests. Check active connection surge in Zabbix charts.
3. **Option 3 (Nginx Service Outage)**:
   - Type `3` and press `Enter`.
   - Nginx stops for 45s. Verify Zabbix Server triggers "Nginx service is down" alarm.
   - Script restarts Nginx automatically at 45s. Verify trigger resolves to OK.
