#!/usr/bin/env bash
# ==============================================================================
# nginx_custom_metrics.sh - Nginx Custom Metric Collector for Zabbix Agent 2
# Target: VM2 web-server (192.168.56.21)
# Subcommands: response_ms | error_5xx | active_conn
# Fail-Safe Rule: MUST always return a valid numeric value (default 0) and exit 0
# ==============================================================================
set -u

# Ensure safe fallback in case of unexpected script abort
trap 'echo 0; exit 0' ERR

NGINX_URL="${NGINX_URL:-http://127.0.0.1:80/}"
STUB_STATUS_URL="${STUB_STATUS_URL:-http://127.0.0.1:8080/basic_status}"
ACCESS_LOG="${ACCESS_LOG:-/var/log/nginx/access.log}"

get_response_ms() {
    local raw_time
    raw_time=$(curl -o /dev/null -s -w "%{time_total}" --max-time 2 "$NGINX_URL" 2>/dev/null || true)
    if [[ -n "$raw_time" ]]; then
        awk -v t="$raw_time" 'BEGIN { printf "%.0f\n", t * 1000 }' 2>/dev/null || echo 0
    else
        echo 0
    fi
}

get_error_5xx() {
    if [[ ! -r "$ACCESS_LOG" ]]; then
        echo 0
        return 0
    fi

    # Field 9 is HTTP status code in standard Nginx combined log format
    awk '$9 ~ /^5[0-9]{2}$/ { count++ } END { print count + 0 }' "$ACCESS_LOG" 2>/dev/null || echo 0
}

get_active_conn() {
    local conn
    conn=$(curl -s --max-time 2 "$STUB_STATUS_URL" 2>/dev/null | awk '/Active connections:/ { print $3 }' || true)
    if [[ "$conn" =~ ^[0-9]+$ ]]; then
        echo "$conn"
    else
        echo 0
    fi
}

case "${1:-}" in
    response_ms)
        get_response_ms
        ;;
    error_5xx)
        get_error_5xx
        ;;
    active_conn)
        get_active_conn
        ;;
    *)
        echo 0
        ;;
esac

exit 0
