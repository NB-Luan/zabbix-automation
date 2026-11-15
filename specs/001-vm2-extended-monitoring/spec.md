# Feature Specification: VM2 Extended Monitoring and Automated Deployment

**Feature Branch**: `001-vm2-extended-monitoring`

**Created**: 2026-11-15

**Status**: Draft

**Input**: User description: "Xây dựng bộ công cụ giám sát mở rộng và tự động triển khai cho VM2 (web-server - 192.168.56.21): 1. Thu thập chỉ số Nginx chuyên sâu (scripts/nginx_custom_metrics.sh): đo thời gian phản hồi thực tế của trang chủ http://127.0.0.1:80/ theo mili-giây (response_ms), đếm số lỗi HTTP 5xx từ /var/log/nginx/access.log (error_5xx), và đọc số kết nối đang hoạt động từ http://127.0.0.1:8080/basic_status (active_conn). 2. Giám sát sức khỏe hệ thống Linux (scripts/system_health_check.sh): đếm tiến trình Zombie (zombie_procs), đếm dịch vụ systemd bị lỗi (failed_units), và đo phần trăm tải I/O ổ đĩa (disk_io_util). 3. Tích hợp Zabbix Agent 2 (configs/custom_monitor.conf): khai báo các UserParameter với tiền tố custom.nginx.* và custom.sys.* trỏ tới /usr/local/bin/. 4. Kịch bản giả lập sự cố & kiểm thử (tests/simulate_incident.sh): menu tương tác trên VM2 gồm 3 chế độ: (1) giả lập quá tải CPU/RAM 60 giây bằng stress-ng (tự cài đặt nếu thiếu), (2) giả lập bão 1000 HTTP requests vào Nginx, (3) dừng dịch vụ Nginx 45 giây để kích hoạt Trigger cảnh báo trên Zabbix rồi tự động khôi phục. 5. Tự động triển khai từ Windows (deploy.ps1 và deploy.sh): đẩy code sang VM2 qua SCP, lọc sạch ký tự \r (CRLF), cài đặt vào thư mục hệ thống Ubuntu, cấp quyền thực thi, khởi động lại zabbix-agent2 và tự động chạy zabbix_agent2 -t để xác minh từng key."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Extensible Nginx Metrics Collection with Fail-Safe Handling (Priority: P1)

As a Systems Administrator, I want to collect real-time web service metrics (HTTP response time, 5xx server errors, active concurrent connections) from Nginx on VM2, so that performance degradation and web application errors are immediately visible on Zabbix Server without causing "Unsupported item" poll failures when Nginx is inactive.

**Why this priority**: Web service health is the primary business workload on VM2. Real-time metrics and guaranteed numeric return values protect monitoring continuity.

**Independent Test**: Execute `scripts/nginx_custom_metrics.sh` directly on VM2 for `response_ms`, `error_5xx`, and `active_conn`. Verify it outputs positive numbers when Nginx is running, and outputs `0` with exit code 0 when Nginx is stopped.

**Acceptance Scenarios**:

1. **Given** Nginx is running on port 80 and stub status is accessible at `http://127.0.0.1:8080/basic_status`, **When** `scripts/nginx_custom_metrics.sh response_ms` is executed, **Then** it returns the HTTP response time in milliseconds as an integer/float value.
2. **Given** Nginx access logs contain HTTP requests with status codes in the 500-599 range, **When** `scripts/nginx_custom_metrics.sh error_5xx` is executed, **Then** it outputs the total count of 5xx errors recorded.
3. **Given** Nginx is stopped or unreachable, **When** any sub-metric (`response_ms`, `error_5xx`, `active_conn`) is polled, **Then** the script catches the failure and returns `0` with an exit code of 0, ensuring Zabbix Agent does not mark the item as unsupported.

---

### User Story 2 - Operating System Health & Stability Monitoring (Priority: P1)

As a DevOps Engineer, I want automated scripts to measure host OS instability (zombie process count, failed systemd units, disk I/O utilization percentage) on VM2, so that system resource exhaustion and background daemon crashes are detected before causing cascading outages.

**Why this priority**: System stability underpins web service performance; silent zombie process leaks or failing system units can degrade host capacity unnoticed.

**Independent Test**: Execute `scripts/system_health_check.sh` on VM2 with parameters `zombie_procs`, `failed_units`, and `disk_io_util`. Validate that each outputs a valid numerical figure within normal Linux bounds.

**Acceptance Scenarios**:

1. **Given** the Linux kernel process table, **When** `scripts/system_health_check.sh zombie_procs` is invoked, **Then** it returns the exact count of processes in the `Z` (Zombie/Defunct) state.
2. **Given** zero systemd services are currently failed, **When** `scripts/system_health_check.sh failed_units` is invoked, **Then** it outputs `0`. If one or more units fail, it outputs the count of failed units.
3. **Given** continuous block storage activity, **When** `scripts/system_health_check.sh disk_io_util` is invoked, **Then** it outputs the disk I/O utilization percentage (between `0` and `100.0`).
4. **Given** missing tools or unreadable system statistics, **When** any health parameter is polled, **Then** the script safely falls back to outputting `0` with an exit code of 0.

---

### User Story 3 - Zabbix Agent 2 UserParameter Integration (Priority: P2)

As a Monitoring Engineer, I want a modular Zabbix Agent 2 configuration file registering custom UserParameter directives for Nginx and system metrics under standardized key namespaces, so that Zabbix Server can monitor them via native active or passive item checks.

**Why this priority**: Seamless integration with Zabbix Agent 2 enables Zabbix Server templates to discover and trigger alarms on the collected custom metrics.

**Independent Test**: Load `configs/custom_monitor.conf` into `/etc/zabbix/zabbix_agent2.d/` and run `zabbix_agent2 -t custom.nginx.response_ms` and `zabbix_agent2 -t custom.sys.zombie_procs` to verify the agent resolves and executes the underlying scripts properly.

**Acceptance Scenarios**:

1. **Given** `configs/custom_monitor.conf` is installed in `/etc/zabbix/zabbix_agent2.d/`, **When** Zabbix Agent 2 is queried with key `custom.nginx.response_ms`, **Then** it routes execution to `/usr/local/bin/nginx_custom_metrics.sh response_ms` and returns a valid value.
2. **Given** the agent is queried with key `custom.sys.failed_units`, **When** execution completes, **Then** it routes to `/usr/local/bin/system_health_check.sh failed_units` and returns the integer count.

---

### User Story 4 - Incident Simulation & Alert Validation Suite (Priority: P2)

As a QA and Operations Tester, I want an interactive terminal incident simulator on VM2 that can trigger synthetic stress (CPU/RAM exhaustion, high-volume HTTP request storms, temporary Nginx shutdown), so that Zabbix alarm thresholds, notification triggers, and recovery behaviors can be systematically tested and validated.

**Why this priority**: Verifying that alerting triggers fire accurately during simulated stress proves that the monitoring infrastructure is functional and reliable before going live.

**Independent Test**: Launch `tests/simulate_incident.sh` on VM2 and select each menu option to confirm it safely generates the expected load or outage, runs for the designated duration, and cleans up after itself without manual intervention.

**Acceptance Scenarios**:

1. **Given** the operator selects option 1 (CPU/RAM Stress), **When** confirmed, **Then** the script ensures `stress-ng` is present (installing it via `apt-get` non-interactively if missing) and applies 60 seconds of compute and memory stress, automatically terminating when the timer expires.
2. **Given** the operator selects option 2 (HTTP Request Storm), **When** confirmed, **Then** the script dispatches 1,000 HTTP requests to `http://127.0.0.1:80/` and displays completion statistics.
3. **Given** the operator selects option 3 (Nginx Service Outage), **When** confirmed, **Then** the script stops the Nginx service for exactly 45 seconds to trigger Zabbix Server alarm triggers, then automatically starts Nginx and verifies service recovery.

---

### User Story 5 - Automated Remote Deployment & Cross-Platform Verification (Priority: P1)

As a Release Operator on Windows, I want an end-to-end automated deployment pipeline (`deploy.ps1` and supporting `deploy.sh`) that synchronizes code to VM2 over SCP, strips Windows carriage return (`\r`) artifacts, installs scripts with appropriate permissions, reloads Zabbix Agent 2, and runs key validation checks, so that the monitoring system can be reliably deployed and updated without manual SSH operations.

**Why this priority**: Required by the project Constitution (Principle I & Principle IV) to eliminate human deployment errors and prevent CRLF script corruption on Ubuntu.

**Independent Test**: Run `deploy.ps1` from Windows PowerShell against VM2 (`192.168.56.21`). Confirm the entire sync, sanitization, installation, and `zabbix_agent2 -t` verification succeeds with zero manual input on the target host.

**Acceptance Scenarios**:

1. **Given** source files edited on a Windows environment containing potential CRLF line endings, **When** `deploy.ps1` transfers them to VM2, **Then** every script and config is sanitized to pure Linux LF line endings before installation.
2. **Given** scripts are staged on VM2, **When** deployment executes, **Then** scripts are copied to `/usr/local/bin/` with `chmod 755`, configs are placed in `/etc/zabbix/zabbix_agent2.d/`, and `zabbix-agent2` is restarted.
3. **Given** the deployment completes installation, **When** post-deployment verification runs, **Then** it tests each key (`custom.nginx.response_ms`, `custom.nginx.error_5xx`, `custom.nginx.active_conn`, `custom.sys.zombie_procs`, `custom.sys.failed_units`, `custom.sys.disk_io_util`) and outputs a structured pass/fail report.

---

### Edge Cases

- **Nginx Inactive during polling**: `curl` commands to `127.0.0.1:80` or `127.0.0.1:8080` will fail with connection refused or timeout. The script must intercept standard error, output `0`, and exit 0.
- **Access log permissions or missing log file**: If `/var/log/nginx/access.log` does not exist or has rotated (`access.log.1`), the script must check file readability and return `0` instead of failing.
- **Disk I/O tool availability**: If `iostat` (from `sysstat`) is unavailable, fallback reading from `/proc/diskstats` or safe default `0.0` must prevent script failure.
- **SSH/SCP authentication interruption**: If network connection drops or credentials fail during deployment, `deploy.ps1` must catch the exception, display a clear diagnostic error, and terminate without leaving partial configurations active.
- **Non-interactive privilege escalation**: All deployment and simulation commands requiring `sudo` on VM2 must support non-interactive execution for user `linux-moniter`.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `scripts/nginx_custom_metrics.sh` MUST support parameter `response_ms` and calculate the HTTP request latency to `http://127.0.0.1:80/` in milliseconds.
- **FR-002**: `scripts/nginx_custom_metrics.sh` MUST support parameter `error_5xx` and return the total count of HTTP status codes matching `5xx` from `/var/log/nginx/access.log`.
- **FR-003**: `scripts/nginx_custom_metrics.sh` MUST support parameter `active_conn` and parse the current active connections from the Nginx status endpoint at `http://127.0.0.1:8080/basic_status`.
- **FR-004**: `scripts/nginx_custom_metrics.sh` MUST always return a valid numeric value (defaulting to `0`) and exit with status 0 upon encountering any error or service outage.
- **FR-005**: `scripts/system_health_check.sh` MUST support parameter `zombie_procs` and report the current number of processes in `Z` state.
- **FR-006**: `scripts/system_health_check.sh` MUST support parameter `failed_units` and report the number of failed systemd units on the host.
- **FR-007**: `scripts/system_health_check.sh` MUST support parameter `disk_io_util` and report the disk utilization percentage for the primary storage device.
- **FR-008**: `scripts/system_health_check.sh` MUST implement fail-safe handling and return `0` or `0.0` on unexpected parse errors, exiting with status 0.
- **FR-009**: `configs/custom_monitor.conf` MUST define `UserParameter` mappings for `custom.nginx.[*]` pointing to `/usr/local/bin/nginx_custom_metrics.sh "$1"`.
- **FR-010**: `configs/custom_monitor.conf` MUST define `UserParameter` mappings for `custom.sys.[*]` pointing to `/usr/local/bin/system_health_check.sh "$1"`.
- **FR-011**: `tests/simulate_incident.sh` MUST provide an interactive CLI menu allowing selection among CPU/RAM stress, HTTP request storm, and temporary Nginx service shutdown.
- **FR-012**: `tests/simulate_incident.sh` MUST verify `stress-ng` availability and automatically install it via package manager if not found before starting Mode 1.
- **FR-013**: `tests/simulate_incident.sh` MUST automatically restart Nginx after the 45-second outage in Mode 3 and verify that Nginx is active before exiting.
- **FR-014**: `deploy.ps1` MUST transfer project artifacts (`scripts/`, `configs/`, `tests/`, and deployment helpers) to VM2 (`192.168.56.21`) using SCP and SSH with target user `linux-moniter`.
- **FR-015**: The deployment pipeline MUST enforce conversion of all file line endings to Linux LF format (`\n`) and set executable permissions (`chmod 755`) on `/usr/local/bin/`.
- **FR-016**: The deployment pipeline MUST trigger `zabbix-agent2` service restart and execute validation tests using `zabbix_agent2 -t` for all six custom keys, returning a summarized verification status.

### Key Entities

- **Custom Metric**: A discrete data item collected by a monitoring script, identified by a unique Zabbix UserParameter key (e.g., `custom.nginx.response_ms`), yielding an integer or floating-point value.
- **Incident Scenario**: A controlled synthetic stress or outage event executed on VM2 with defined boundaries (duration, load intensity, recovery criteria).
- **Deployment Manifest**: The collection of scripts, configuration directives, and target installation paths deployed to VM2.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of custom metric queries via `zabbix_agent2 -t` return valid numerical data without throwing "Unsupported item" or non-zero exit codes.
- **SC-002**: Automated deployment from Windows to VM2 completes within 60 seconds over standard host-only network connections.
- **SC-003**: In simulated outage conditions (Nginx stopped), all Nginx custom metric calls respond within 3 seconds, returning `0` and preventing monitoring poll stalls.
- **SC-004**: 100% of deployed `.sh` and `.conf` files on VM2 pass line ending checks (zero CRLF characters) and pass ShellCheck validation with zero errors.
- **SC-005**: The incident simulation tool recovers system state to normal operations 100% of the time upon completing or interrupting any stress scenario.

## Assumptions

- **Target Host Environment**: VM2 is accessible at `192.168.56.21` with SSH user `linux-moniter` possessing passwordless sudo privileges for system service restarts and package installation.
- **Web Server Configuration**: Nginx is configured on VM2 with virtual host on port 80 and `stub_status` enabled on port 8080 at location `/basic_status`.
- **Network Reachability**: Host-only network connectivity between the Windows host and VM2 is operational.
- **Agent Prerequisites**: `zabbix-agent2` is installed on VM2 and configured to include config files from `/etc/zabbix/zabbix_agent2.d/*.conf`.
