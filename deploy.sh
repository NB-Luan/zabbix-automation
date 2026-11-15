#!/usr/bin/env bash
# ==============================================================================
# deploy.sh - Remote Installation & Key Verification Helper for VM2
# Target: Ubuntu Server 26.04 LTS (VM2 web-server: 192.168.56.21)
# ==============================================================================
set -euo pipefail

STAGING_DIR="${STAGING_DIR:-/tmp/zabbix_deploy}"
INSTALL_BIN_DIR="/usr/local/bin"
ZABBIX_CONF_DIR="/etc/zabbix/zabbix_agent2.d"

run_sudo() {
    if sudo -n true 2>/dev/null; then
        sudo "$@"
    elif [ -n "${SUDO_PASS:-}" ]; then
        echo "$SUDO_PASS" | sudo -S -p '' "$@"
    else
        echo "[ERROR] sudo requires interactive authentication on VM2." >&2
        echo "To allow automated execution, please configure NOPASSWD by running on VM2:" >&2
        echo "  echo '$USER ALL=(ALL) NOPASSWD: ALL' | sudo tee /etc/sudoers.d/$USER" >&2
        echo "Alternatively, provide your password to deploy.ps1 via: -SudoPassword '<password>'" >&2
        exit 1
    fi
}

echo "=== [1/5] Sanitizing Line Endings (CRLF -> LF) ==="
if [ -d "$STAGING_DIR" ]; then
    find "$STAGING_DIR" -type f \( -name "*.sh" -o -name "*.conf" \) -exec sed -i 's/\r$//' {} +
else
    echo "[ERROR] Staging directory $STAGING_DIR not found!" >&2
    exit 1
fi

echo "=== [2/5] Installing Monitoring Scripts & Configurations ==="
run_sudo mkdir -p "$INSTALL_BIN_DIR" "$ZABBIX_CONF_DIR"

if [ -f "$STAGING_DIR/scripts/nginx_custom_metrics.sh" ]; then
    run_sudo cp "$STAGING_DIR/scripts/nginx_custom_metrics.sh" "$INSTALL_BIN_DIR/"
    run_sudo chmod 755 "$INSTALL_BIN_DIR/nginx_custom_metrics.sh"
    run_sudo chown root:root "$INSTALL_BIN_DIR/nginx_custom_metrics.sh"
    echo "  -> Installed: $INSTALL_BIN_DIR/nginx_custom_metrics.sh"
fi

if [ -f "$STAGING_DIR/scripts/system_health_check.sh" ]; then
    run_sudo cp "$STAGING_DIR/scripts/system_health_check.sh" "$INSTALL_BIN_DIR/"
    run_sudo chmod 755 "$INSTALL_BIN_DIR/system_health_check.sh"
    run_sudo chown root:root "$INSTALL_BIN_DIR/system_health_check.sh"
    echo "  -> Installed: $INSTALL_BIN_DIR/system_health_check.sh"
fi

if [ -f "$STAGING_DIR/configs/custom_monitor.conf" ]; then
    run_sudo cp "$STAGING_DIR/configs/custom_monitor.conf" "$ZABBIX_CONF_DIR/"
    run_sudo chmod 644 "$ZABBIX_CONF_DIR/custom_monitor.conf"
    run_sudo chown root:root "$ZABBIX_CONF_DIR/custom_monitor.conf"
    echo "  -> Installed: $ZABBIX_CONF_DIR/custom_monitor.conf"
fi

# Ensure zabbix user can read /var/log/nginx/access.log by adding it to adm group
run_sudo usermod -aG adm zabbix || true

if [ -f "$STAGING_DIR/tests/simulate_incident.sh" ]; then
    cp "$STAGING_DIR/tests/simulate_incident.sh" "$HOME/simulate_incident.sh"
    chmod 755 "$HOME/simulate_incident.sh"
    echo "  -> Installed: $HOME/simulate_incident.sh"
fi

echo "=== [3/5] Restarting Zabbix Agent 2 Service ==="
run_sudo systemctl restart zabbix-agent2
if run_sudo systemctl is-active --quiet zabbix-agent2; then
    echo "  -> zabbix-agent2 is active and running."
else
    echo "[ERROR] zabbix-agent2 failed to start!" >&2
    run_sudo systemctl status zabbix-agent2 --no-pager >&2 || true
    exit 1
fi

echo "=== [4/5] Executing Zabbix Agent 2 Key Verification ==="
KEYS=(
    "custom.nginx.response_ms"
    "custom.nginx.error_5xx"
    "custom.nginx.active_conn"
    "custom.sys.zombie_procs"
    "custom.sys.failed_units"
    "custom.sys.disk_io_util"
)

FAILED_COUNT=0
for key in "${KEYS[@]}"; do
    output=$(zabbix_agent2 -t "$key" 2>&1) || true
    if echo "$output" | grep -qE "\[(s|u|d)\|[0-9]+(\.[0-9]+)?\]"; then
        echo "  [PASS] $key => $output"
    else
        echo "  [FAIL] $key => $output" >&2
        FAILED_COUNT=$((FAILED_COUNT + 1))
    fi
done

echo "=== [5/5] Cleanup Staging Directory ==="
rm -rf "$STAGING_DIR"

if [ "$FAILED_COUNT" -eq 0 ]; then
    echo "=================================================================="
    echo "  SUCCESS: All 6 monitoring keys verified successfully on VM2!"
    echo "=================================================================="
    exit 0
else
    echo "=================================================================="
    echo "  FAILURE: $FAILED_COUNT key(s) failed verification on VM2!"
    echo "=================================================================="
    exit 1
fi
