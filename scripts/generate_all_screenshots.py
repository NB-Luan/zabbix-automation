#!/usr/bin/env python3
"""
generate_all_screenshots.py
Clean, high-resolution screenshot generator for slides and documentation.
"""
import os
import shutil
import time
import requests
import paramiko
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_DIR = os.path.join(WORKSPACE, "docs", "screenshots")
ARTIFACT_DIR = r"C:\Users\Dang Luan\.gemini\antigravity\brain\3862747b-9843-4a1d-8c6d-f72ce92b42f6\screenshots"

os.makedirs(DOCS_DIR, exist_ok=True)
os.makedirs(ARTIFACT_DIR, exist_ok=True)

def save(driver, name):
    p1 = os.path.join(DOCS_DIR, name)
    p2 = os.path.join(ARTIFACT_DIR, name)
    driver.save_screenshot(p1)
    shutil.copy2(p1, p2)
    print(f"  [SAVED] {name} ({os.path.getsize(p1):,} bytes)")

def get_ssh():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    user_home = os.path.expanduser("~")
    kpath = os.path.join(user_home, ".ssh", "id_ed25519")
    pkey = paramiko.Ed25519Key.from_private_key_file(kpath)
    ssh.connect("192.168.56.21", username="linux-moniter", pkey=pkey, timeout=6)
    return ssh

def main():
    print("=" * 70)
    print("  GENERATE ALL PRESENTATION SCREENSHOTS")
    print("=" * 70)

    opts = Options()
    opts.add_argument('--headless')
    opts.add_argument('--window-size=1600,1050')
    opts.add_argument('--hide-scrollbars')
    opts.add_argument('--disable-gpu')
    driver = webdriver.Edge(options=opts)

    try:
        # 1. Dashboard Normal State
        print("\n[1/7] Chụp Web Dashboard - Trạng thái bình thường...")
        driver.get("http://localhost:5000/")
        time.sleep(4)
        save(driver, "01_noc_dashboard_normal.png")

        # 2. Zabbix Web UI - Hosts
        print("\n[2/7] Chụp Zabbix 7.0 - Quản lý Host...")
        driver.get("http://192.168.56.10/zabbix/")
        time.sleep(1)
        if driver.find_elements(By.ID, "name"):
            driver.find_element(By.ID, "name").clear()
            driver.find_element(By.ID, "name").send_keys("Admin")
            driver.find_element(By.ID, "password").clear()
            driver.find_element(By.ID, "password").send_keys("zabbix")
            driver.find_element(By.ID, "enter").click()
            time.sleep(2)
        driver.get("http://192.168.56.10/zabbix/zabbix.php?action=host.view")
        time.sleep(3)
        save(driver, "02_zabbix_web_hosts.png")

        # 3. Zabbix Web UI - Latest Data for web-server
        print("\n[3/7] Chụp Zabbix 7.0 - Dữ liệu mới nhất (Items & Metrics)...")
        driver.get("http://192.168.56.10/zabbix/zabbix.php?action=latest.view&hostids%5B0%5D=10680&filter_set=1")
        time.sleep(3)
        save(driver, "03_zabbix_web_latest_data.png")

        # 4. Chaos Storm Simulation & Live Terminal
        print("\n[4/7] Kích hoạt giả lập Bão 1.000 HTTP Requests & Chụp Terminal Console...")
        requests.post("http://localhost:5000/api/simulate", json={"mode": "storm"}, timeout=5)
        time.sleep(4.5)  # Đợi hoàn tất
        driver.get("http://localhost:5000/")
        time.sleep(2)
        # Cuộn để hiển thị bảng điều khiển và terminal rõ nhất
        driver.execute_script("document.getElementById('btnStorm').scrollIntoView({block: 'start'});")
        time.sleep(1)
        save(driver, "04_chaos_storm_terminal.png")

        # 5. Stop Nginx -> Active Problem
        print("\n[5/7] Giả lập sự cố dừng Nginx -> Chụp Dashboard cảnh báo đỏ...")
        ssh = get_ssh()
        ssh.exec_command("sudo systemctl stop nginx")
        ssh.close()
        print("  Dừng Nginx thành công. Đợi Zabbix phát hiện sự cố (25s)...")
        for i in range(25, 0, -5):
            print(f"  ...còn {i}s")
            time.sleep(5)
        driver.get("http://localhost:5000/")
        time.sleep(3)
        save(driver, "05_noc_dashboard_active_problem.png")

        # 6. Zabbix Web UI - Problems View
        print("\n[6/7] Chụp Zabbix 7.0 - Màn hình Cảnh báo Sự cố (Problems)...")
        driver.get("http://192.168.56.10/zabbix/zabbix.php?action=problem.view")
        time.sleep(3)
        save(driver, "06_zabbix_web_problems.png")

        # 7. Restart Nginx -> Recovery
        print("\n[7/7] Khôi phục dịch vụ Nginx -> Chụp Dashboard đã phục hồi...")
        ssh = get_ssh()
        ssh.exec_command("sudo systemctl start nginx")
        ssh.close()
        print("  Đã bật lại Nginx. Đợi Zabbix khôi phục (20s)...")
        for i in range(20, 0, -5):
            print(f"  ...còn {i}s")
            time.sleep(5)
        driver.get("http://localhost:5000/")
        time.sleep(3)
        save(driver, "07_noc_dashboard_recovered.png")

        print("\n" + "=" * 70)
        print("  TẤT CẢ 7 BƯỚC ĐÃ ĐƯỢC CHỤP THÀNH CÔNG VỚI ĐỘ PHÂN GIẢI CAO!")
        print(f"  Lưu tại: {DOCS_DIR}")
        print("=" * 70)

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
