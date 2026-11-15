#!/usr/bin/env bash
# ==============================================================================
# system_health_check.sh - Linux Host Health Check Collector for Zabbix Agent 2
# Target: VM2 web-server (192.168.56.21)
# Subcommands: zombie_procs | failed_units | disk_io_util
# Fail-Safe Rule: MUST always return a valid numeric value (default 0 / 0.0) and exit 0
# ==============================================================================
set -u

# Ensure safe fallback in case of unexpected script abort
trap 'echo 0; exit 0' ERR

get_zombie_procs() {
    local zombies
    zombies=$(ps -eo stat= 2>/dev/null | awk '/^Z/ { c++ } END { print c + 0 }')
    if [[ "$zombies" =~ ^[0-9]+$ ]]; then
        echo "$zombies"
    else
        echo 0
    fi
}

get_failed_units() {
    local failed
    failed=$(systemctl list-units --state=failed --no-legend --no-pager 2>/dev/null | awk 'NF { c++ } END { print c + 0 }')
    if [[ "$failed" =~ ^[0-9]+$ ]]; then
        echo "$failed"
    else
        echo 0
    fi
}

get_disk_io_util() {
    local util="0.0"
    if command -v iostat >/dev/null 2>&1; then
        util=$(iostat -dx 1 2 2>/dev/null | awk '/^[vsh]d[a-z]|nvme/ { val = $NF } END { if (val != "") print val; else print "0.0" }' || echo "0.0")
    fi

    # Verify output is a valid integer or float
    if [[ "$util" =~ ^[0-9]+(\.[0-9]+)?$ ]]; then
        echo "$util"
    else
        echo "0.0"
    fi
}

case "${1:-}" in
    zombie_procs)
        get_zombie_procs
        ;;
    failed_units)
        get_failed_units
        ;;
    disk_io_util)
        get_disk_io_util
        ;;
    *)
        echo 0
        ;;
esac

exit 0
