#!/usr/bin/env bash
# ==============================================================================
# simulate_incident.sh - Incident Simulation & Stress Testing Suite
# Target: VM2 web-server (192.168.56.21)
# Modes:
#   1. CPU/RAM Stress (60 seconds via stress-ng)
#   2. HTTP Request Storm (1,000 requests to Nginx port 80)
#   3. Nginx Service Outage (45 seconds stop & auto-recovery)
# ==============================================================================
set -euo pipefail

cleanup() {
    echo -e "\n[CLEANUP] Interrupted or exiting. Ensuring system returns to normal state..."
    # Terminate any rogue stress-ng processes
    pkill -f stress-ng >/dev/null 2>&1 || true
    # Guarantee Nginx is started
    if ! sudo systemctl is-active --quiet nginx 2>/dev/null; then
        echo "[CLEANUP] Restarting Nginx service..."
        sudo systemctl start nginx || true
    fi
}
trap cleanup EXIT INT TERM

ensure_stress_ng() {
    if ! command -v stress-ng >/dev/null 2>&1; then
        echo "[INFO] 'stress-ng' tool is missing. Installing non-interactively via apt..."
        sudo apt-get update -y && sudo apt-get install -y stress-ng
        echo "[INFO] 'stress-ng' installed successfully."
    fi
}

run_mode1() {
    echo "=================================================================="
    echo "  MODE 1: Simulating CPU & RAM Overload for 60 seconds"
    echo "=================================================================="
    ensure_stress_ng
    echo "[INFO] Starting stress-ng (2 CPU workers, 70% RAM allocation, 60s timeout)..."
    stress-ng --cpu 2 --vm 1 --vm-bytes 70% --timeout 60s --metrics-brief
    echo "[PASS] Mode 1 completed. System load will normalize shortly."
}

run_mode2() {
    echo "=================================================================="
    echo "  MODE 2: Simulating HTTP Request Storm (1,000 Requests)"
    echo "=================================================================="
    local target_url="http://127.0.0.1:80/"
    echo "[INFO] Dispatching 1,000 HTTP requests to $target_url with concurrency 10..."
    seq 1000 | xargs -n 1 -P 10 curl -s -o /dev/null "$target_url" || true
    echo "[PASS] Mode 2 completed. 1,000 requests processed."
}

run_mode3() {
    echo "=================================================================="
    echo "  MODE 3: Simulating Nginx Service Outage (45 seconds)"
    echo "=================================================================="
    echo "[INFO] Stopping Nginx service now..."
    sudo systemctl stop nginx

    echo "[INFO] Nginx is STOPPED. Zabbix Server trigger should fire within 30-45s."
    for ((i=45; i>0; i--)); do
        printf "\r  -> Outage duration remaining: %2d seconds..." "$i"
        sleep 1
    done
    echo ""

    echo "[INFO] Recovering Nginx service..."
    sudo systemctl start nginx

    if sudo systemctl is-active --quiet nginx; then
        echo "[PASS] Nginx service successfully restored and active!"
    else
        echo "[FAIL] Failed to restore Nginx service automatically!" >&2
        exit 1
    fi
}

show_menu() {
    clear 2>/dev/null || true
    echo "=================================================================="
    echo "      ZABBIX MONITORING - INCIDENT SIMULATOR (VM2 web-server)     "
    echo "=================================================================="
    echo " 1) Simulate CPU & RAM Overload (60s stress-ng)"
    echo " 2) Simulate HTTP Request Storm (1,000 GET requests)"
    echo " 3) Simulate Nginx Service Outage (45s stop & auto-recover)"
    echo " 0) Exit"
    echo "=================================================================="
    printf "Please select an option [0-3]: "
}

# Handle non-interactive command-line arguments
if [[ $# -gt 0 ]]; then
    case "$1" in
        --stress)
            run_mode1
            exit 0
            ;;
        --storm)
            run_mode2
            exit 0
            ;;
        --outage)
            run_mode3
            exit 0
            ;;
        --help|-h)
            echo "Usage: $0 [--stress | --storm | --outage | --help]"
            exit 0
            ;;
        *)
            echo "Unknown argument: $1" >&2
            echo "Usage: $0 [--stress | --storm | --outage | --help]" >&2
            exit 1
            ;;
    esac
fi

# Interactive menu loop
while true; do
    show_menu
    read -r choice
    echo ""
    case "$choice" in
        1)
            run_mode1
            read -r -p "Press Enter to return to menu..."
            ;;
        2)
            run_mode2
            read -r -p "Press Enter to return to menu..."
            ;;
        3)
            run_mode3
            read -r -p "Press Enter to return to menu..."
            ;;
        0)
            echo "Exiting incident simulator."
            exit 0
            ;;
        *)
            echo "Invalid selection. Please choose 0, 1, 2, or 3."
            sleep 1
            ;;
    esac
done
