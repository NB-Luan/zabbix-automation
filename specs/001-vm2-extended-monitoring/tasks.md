# Tasks: VM2 Extended Monitoring and Automated Deployment

**Input**: Design documents from `specs/001-vm2-extended-monitoring/` (`spec.md`, `plan.md`, `data-model.md`, `contracts/userparameter-contracts.md`, `research.md`, `quickstart.md`)

**Prerequisites**: `plan.md`, `spec.md`, `constitution.md`

**Organization**: Tasks are grouped strictly by user story to enable independent implementation and testing of each story.

## Format: `- [ ] [TaskID] [P?] [Story?] Description with file path`

- **[P]**: Can run in parallel (different files, no blocking dependencies)
- **[Story]**: User story identifier (`[US1]`, `[US2]`, `[US3]`, `[US4]`, `[US5]`)
- Every task includes an explicit, exact file path

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Repository initialization, directory layout, and line ending policy enforcement

- [X] T001 Create project directory structure for scripts/, configs/, and tests/ in repository root
- [X] T002 [P] Configure .gitattributes in repository root to enforce Linux LF line endings on all .sh, .conf, and .yaml files
- [X] T003 [P] Create initial root .gitignore in repository root to exclude temporary deployment artifacts and editor cache

---

## Phase 2: Foundational (Deployment Helper Skeleton & Staging Logic)

**Purpose**: Core staging infrastructure on VM2 required for automated deployment and testing

**⚠️ CRITICAL**: Must be functional before user story deployment can proceed

- [X] T004 Implement remote deployment helper script deploy.sh with staging directory setup (/tmp/zabbix_deploy/) and LF sanitization via sed
- [X] T005 Implement permission management (chmod 0755) and zabbix-agent2 systemctl restart logic in deploy.sh

**Checkpoint**: Foundation ready - monitoring collectors, configs, and tests can now be implemented

---

## Phase 3: User Story 1 - Extensible Nginx Metrics Collection (Priority: P1) 🎯 MVP

**Goal**: Collect real-time `response_ms`, `error_5xx`, and `active_conn` from Nginx with fail-safe error handling (default `0`).

**Independent Test**: Execute `scripts/nginx_custom_metrics.sh` on VM2 with parameters `response_ms`, `error_5xx`, and `active_conn`. Verify valid numeric output when Nginx is running; verify output is `0` with exit code 0 when Nginx is stopped.

### Implementation for User Story 1

- [X] T006 [P] [US1] Implement response_ms measurement using curl --max-time 2 and awk in scripts/nginx_custom_metrics.sh
- [X] T007 [P] [US1] Implement error_5xx counting from /var/log/nginx/access.log with awk status matching in scripts/nginx_custom_metrics.sh
- [X] T008 [P] [US1] Implement active_conn parser from http://127.0.0.1:8080/basic_status using curl and awk in scripts/nginx_custom_metrics.sh
- [X] T009 [US1] Implement fail-safe argument dispatcher and error traps ensuring guaranteed 0 return and exit code 0 on errors in scripts/nginx_custom_metrics.sh

**Checkpoint**: User Story 1 is fully functional and testable independently.

---

## Phase 4: User Story 2 - Operating System Health & Stability Monitoring (Priority: P1)

**Goal**: Collect Linux OS health metrics (`zombie_procs`, `failed_units`, `disk_io_util`) with guaranteed numeric return values.

**Independent Test**: Execute `scripts/system_health_check.sh` on VM2 with parameters `zombie_procs`, `failed_units`, and `disk_io_util`. Validate integer and floating-point outputs with exit code 0.

### Implementation for User Story 2

- [X] T010 [P] [US2] Implement zombie_procs process state parsing via ps -eo stat= in scripts/system_health_check.sh
- [X] T011 [P] [US2] Implement failed_units counting using systemctl list-units --state=failed in scripts/system_health_check.sh
- [X] T012 [P] [US2] Implement disk_io_util sampling using iostat -dx 1 2 with fallback in scripts/system_health_check.sh
- [X] T013 [US2] Implement fail-safe argument routing and numeric fallback defaults in scripts/system_health_check.sh

**Checkpoint**: User Stories 1 AND 2 are both functional and independently testable.

---

## Phase 5: User Story 3 - Zabbix Agent 2 UserParameter Integration (Priority: P2)

**Goal**: Register custom metrics under `custom.nginx.*` and `custom.sys.*` pointing to `/usr/local/bin/`.

**Independent Test**: Deploy `configs/custom_monitor.conf` to `/etc/zabbix/zabbix_agent2.d/` and test key resolution using `zabbix_agent2 -t custom.nginx.response_ms` and `zabbix_agent2 -t custom.sys.zombie_procs`.

### Implementation for User Story 3

- [X] T014 [US3] Create Zabbix Agent 2 configuration file configs/custom_monitor.conf defining custom.nginx.[*] and custom.sys.[*] UserParameter directives

**Checkpoint**: UserParameter configurations mapped and resolvable by Zabbix Agent 2.

---

## Phase 6: User Story 4 - Incident Simulation & Alert Validation Suite (Priority: P2)

**Goal**: Interactive CLI tool on VM2 simulating CPU/RAM overload (60s), 1000 HTTP request storm, and temporary Nginx outage (45s).

**Independent Test**: Execute `bash tests/simulate_incident.sh` on VM2 and verify each scenario runs for its allocated duration and cleans up system state properly.

### Implementation for User Story 4

- [X] T015 [P] [US4] Implement stress-ng prerequisite check and automated installation logic in tests/simulate_incident.sh
- [X] T016 [P] [US4] Implement Mode 1 (CPU/RAM stress 60s) with countdown timer in tests/simulate_incident.sh
- [X] T017 [P] [US4] Implement Mode 2 (1,000 HTTP request storm to Nginx port 80) in tests/simulate_incident.sh
- [X] T018 [P] [US4] Implement Mode 3 (Nginx 45-second outage with automatic service restart verification) in tests/simulate_incident.sh
- [X] T019 [US4] Implement interactive CLI menu, non-interactive CLI flags (--stress, --storm, --outage), and SIGINT cleanup trap in tests/simulate_incident.sh

**Checkpoint**: Incident simulator verified for both interactive and automated stress testing.

---

## Phase 7: User Story 5 - Automated Remote Deployment Pipeline (Priority: P1)

**Goal**: Windows PowerShell deployer (`deploy.ps1`) providing fully automated SCP sync, CRLF sanitization, service reload, and `zabbix_agent2 -t` verification report.

**Independent Test**: Execute `.\deploy.ps1` from Windows PowerShell against VM2 (`192.168.56.21`) and verify zero manual operations required.

### Implementation for User Story 5

- [X] T020 [US5] Implement Windows PowerShell deployer deploy.ps1 with connection validation, SCP sync to /tmp/zabbix_deploy/, and remote execution
- [X] T021 [US5] Implement automated zabbix_agent2 -t key verification test harness in deploy.sh

**Checkpoint**: 100% automated end-to-end deployment pipeline operational.

---

## Phase 8: Polish & Cross-Cutting Quality Gates

**Purpose**: Comprehensive validation of Constitution Principles I-IV before release

- [X] T022 [P] Perform ShellCheck static analysis on scripts/nginx_custom_metrics.sh, scripts/system_health_check.sh, tests/simulate_incident.sh, and deploy.sh
- [X] T023 [P] Verify pure Linux LF line endings (no CRLF) across all repository .sh, .conf, and .ps1 files
- [X] T024 Execute quickstart.md end-to-end deployment validation scenarios against VM2

---

## Dependencies & Execution Order

### Phase Dependencies

```text
Phase 1: Setup (T001-T003)
   │
   ▼
Phase 2: Foundational (T004-T005)
   │
   ├──────────────────────────┬──────────────────────────┐
   ▼                          ▼                          ▼
Phase 3: US1 (T006-T009)   Phase 4: US2 (T010-T013)   Phase 6: US4 (T015-T019)
   │                          │                          │
   └─────────────┬────────────┘                          │
                 ▼                                       │
Phase 5: US3 Config (T014)                               │
                 │                                       │
                 ▼                                       │
Phase 7: US5 Deployment Pipeline (T020-T021) ◄───────────┘
                 │
                 ▼
Phase 8: Polish & Quality Gates (T022-T024)
```

### Parallel Opportunities

- **Within Phase 1**: T002 (.gitattributes) and T003 (.gitignore) can execute in parallel.
- **Within Phase 3 (US1)**: Metric extraction functions T006, T007, and T008 can be written in parallel.
- **Within Phase 4 (US2)**: Health checking functions T010, T011, and T012 can be written in parallel.
- **Across Stories**: Phase 3 (US1), Phase 4 (US2), and Phase 6 (US4) can be developed concurrently once Phase 2 is complete.
- **Within Phase 8**: ShellCheck linting (T022) and line ending verification (T023) can run in parallel.

---

## Implementation Strategy

### MVP First (User Story 1 Only)
1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational (T004-T005)
3. Complete Phase 3: User Story 1 (T006-T009)
4. Validate Nginx metrics collection independently on VM2.

### Incremental Delivery
1. Foundation + US1 → Basic Nginx Monitoring (MVP).
2. Add US2 → Comprehensive Linux System Health Monitoring.
3. Add US3 → Zabbix Agent 2 UserParameter Registration.
4. Add US4 → Incident Simulation & Trigger Testing Suite.
5. Add US5 → Automated Windows Deployment Pipeline (`deploy.ps1`).
6. Run Phase 8 Quality Gates → Final Verification & Sign-off.
