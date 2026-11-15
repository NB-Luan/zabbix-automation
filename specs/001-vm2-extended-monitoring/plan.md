# Implementation Plan: VM2 Extended Monitoring and Automated Deployment

**Branch**: `001-vm2-extended-monitoring` | **Date**: 2026-11-15 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-vm2-extended-monitoring/spec.md`

## Summary

This feature delivers an automated custom monitoring and deployment solution for VM2 (`web-server` - `192.168.56.21`). It provides two high-performance Bash metric extraction scripts (`scripts/nginx_custom_metrics.sh` and `scripts/system_health_check.sh`) designed with strict fail-safe mechanisms to ensure Zabbix Agent 2 never encounters "Unsupported item" states. These metrics are registered in `configs/custom_monitor.conf`. An interactive incident simulation tool (`tests/simulate_incident.sh`) allows on-demand testing of CPU/RAM overload, HTTP traffic storms, and service outages. The entire package is deployed automatically from Windows via `deploy.ps1` and `deploy.sh`, which enforce Linux LF line endings and perform automated end-to-end verification using `zabbix_agent2 -t`.

## Technical Context

**Language/Version**: Bash 5.2+ (Target VM2, POSIX/ShellCheck compliant) | PowerShell 5.1/7+ (Workstation deployment).

**Primary Dependencies**:
- Target VM (Ubuntu 26.04 LTS): `zabbix-agent2`, `nginx`, `curl`, `gawk`, `procps` (`ps`), `systemd`, `sysstat` (`iostat`), `stress-ng`.
- Workstation (Windows): `OpenSSH` (`ssh.exe`, `scp.exe`), PowerShell.

**Storage**: Local Linux file system (`/usr/local/bin/`, `/etc/zabbix/zabbix_agent2.d/`, `/var/log/nginx/access.log`). No database on VM2.

**Testing**: `shellcheck` (static linting), `zabbix_agent2 -t <key>` (key resolution tests), and `tests/simulate_incident.sh` (end-to-end integration tests).

**Target Platform**: Ubuntu Server 26.04 LTS running as VM2 (`192.168.56.21`) with user `linux-moniter`.

**Project Type**: Infrastructure Automation / Monitoring Extension (IaC scripts, Agent configuration, PowerShell deployer).

**Performance Goals**:
- Metric extraction latency: < 500ms under normal conditions; hard timeout capped at 2 seconds.
- Total deployment execution: < 60 seconds over local host-only network.

**Constraints**:
- Strict adherence to Linux LF line endings (`\n`) for all deployed files.
- Zero ShellCheck warnings or errors.
- Guaranteed numeric returns (default `0` / `0.0`) on service failure or unreadable files.
- 100% automated remote deployment without manual SSH editing on the target VM.

**Scale/Scope**:
- 6 custom monitoring metrics (3 Nginx, 3 OS health).
- 2 metric collectors, 1 agent config, 1 incident simulator, 2 deployment scripts.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked post-Phase 1 design.*

| Principle / Rule | Evaluation | Status |
|---|---|---|
| **I. Linux Format & ShellCheck Compliance** | Files are created with LF line endings; `deploy.ps1` runs `sed -i 's/\r$//'` before installation; all Bash scripts are ShellCheck-clean. | **PASSED** |
| **II. Fixed Target Architecture & Network Topology** | VM2 is fixed to `192.168.56.21`, user `linux-moniter`, Nginx port 80 & 8080 (`/basic_status`), Zabbix Agent 2. | **PASSED** |
| **III. Fail-Safe Metric Collection (Zero Unsupported Items)** | All custom metric functions catch missing files, curl timeouts, and service downtime, returning `0` or `0.0` with exit code 0. | **PASSED** |
| **IV. Fully Automated Remote Deployment (Zero Manual Edits)** | `deploy.ps1` and `deploy.sh` handle staging, line sanitization, permission management, agent reload, and key verification with zero manual SSH editing. | **PASSED** |

## Project Structure

### Documentation (this feature)

```text
specs/001-vm2-extended-monitoring/
├── spec.md              # Requirements and user stories
├── plan.md              # This architecture & implementation plan
├── research.md          # Technical research and benchmarking decisions
├── data-model.md        # Entities, metrics catalogue, and state transitions
├── quickstart.md        # Step-by-step deployment and verification guide
├── checklists/
│   └── requirements.md  # Requirements completeness review
└── contracts/
    └── userparameter-contracts.md # Zabbix Agent 2 & CLI API interface contracts
```

### Source Code (repository root)

```text
zabbix-automation/
├── configs/
│   └── custom_monitor.conf        # Zabbix Agent 2 UserParameter configuration
├── scripts/
│   ├── nginx_custom_metrics.sh   # Nginx latency, 5xx errors, active connections
│   └── system_health_check.sh    # Zombie processes, failed units, disk I/O util
├── tests/
│   └── simulate_incident.sh      # Interactive incident and stress testing suite
├── deploy.ps1                    # Windows PowerShell orchestration script
└── deploy.sh                     # Remote staging, sanitization, and verification helper
```

**Structure Decision**: A clean root-level layout separating deployment orchestration (`deploy.ps1`, `deploy.sh`), agent configuration (`configs/`), monitoring collectors (`scripts/`), and test verification tooling (`tests/`).

## Complexity Tracking

> **Constitution Check has zero violations. No unjustified complexity introduced.**
