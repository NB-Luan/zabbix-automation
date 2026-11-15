# Hệ Thống Giám Sát Mở Rộng & Tự Động Triển Khai Zabbix Platform

Dự án tự động hóa thu thập chỉ số chuyên sâu, cấu hình Zabbix Agent 2, thiết lập Items/Triggers qua Zabbix API và kiểm thử sự cố trên hạ tầng máy ảo Linux Ubuntu Server.

---

## 1. Kiến Trúc Hệ Thống (Network & Server Architecture)

Hệ thống được thiết kế theo mô hình 2 máy ảo phân tách vai trò:

| Máy ảo | Tên Host | Địa chỉ IP mặc định | Tài khoản SSH | Thành phần phần mềm chính | Vai trò |
|---|---|---|---|---|---|
| **VM1** | `zabbix-server` | `192.168.56.10` | `zabbix-server` | Zabbix Server 7.0 LTS, MySQL 8.4, Apache2 | Máy chủ giám sát trung tâm, lưu trữ dữ liệu, kích hoạt Trigger & Alert |
| **VM2** | `web-server` | `192.168.56.21` | `linux-moniter` | Nginx (port 80 & 8080), Zabbix Agent 2 | Máy chủ dịch vụ Web, thu thập chỉ số chuyên sâu & kiểm thử sự cố |

```text
+-----------------------------------+         SSH / SCP Deploy          +------------------------------------+
|         Workstation               | --------------------------------> |     VM2: web-server (192.168.56.21)|
|   (Windows / PowerShell / Linux)  |                                   |  - Nginx (Port 80: Web)            |
+-----------------------------------+                                   |  - stub_status (Port 8080: Status) |
                  |                                                     |  - Zabbix Agent 2                  |
                  | Zabbix JSON-RPC API                                 |  - Scripts: /usr/local/bin/        |
                  v                                                     +------------------------------------+
+-----------------------------------+                                                     ^
|   VM1: zabbix-server              |                                                     |
|   (192.168.56.10)                 | ---------------- Zabbix Agent Metrics Polling ------+
|  - Zabbix Server 7.0 LTS          |                       (Port 10050)
|  - MySQL 8.4 Database             |
|  - Apache2 Web Frontend           |
+-----------------------------------+
```

---

## 2. Cấu Trúc Thư Mục Dự Án

```text
zabbix-automation/
├── configs/
│   └── custom_monitor.conf        # Cấu hình UserParameter cho Zabbix Agent 2
├── scripts/
│   ├── nginx_custom_metrics.sh   # Thu thập: response_ms, error_5xx, active_conn
│   ├── system_health_check.sh    # Thu thập: zombie_procs, failed_units, disk_io_util
│   └── zabbix_api_setup.py       # Tự động tạo Items, Triggers, cấu hình Macro qua Zabbix API
├── tests/
│   └── simulate_incident.sh      # Kịch bản giả lập sự cố (CPU/RAM stress, HTTP storm, Nginx outage)
├── web_dashboard/                # Ứng dụng Web Dashboard thời gian thực & Chaos Lab (Flask + Tailwind + Chart.js)
│   ├── static/
│   │   ├── css/dashboard.css     # CSS giao diện NOC Dark Mode, hiệu ứng phát sáng & cảnh báo
│   │   └── js/dashboard.js       # Script biểu đồ Chart.js, cập nhật dữ liệu 5s & điều khiển SSH
│   ├── templates/
│   │   └── index.html            # Giao diện chính trung tâm giám sát NOC
│   ├── app.py                    # Backend Flask API kết nối Zabbix JSON-RPC & SSH VM2
│   └── requirements.txt          # Thư viện phụ thuộc Python (Flask, requests, paramiko)
├── .env.example                  # File mẫu cấu hình biến môi trường (IP, User, Port)
├── .gitattributes                # Quy tắc ép buộc chuẩn xuống dòng Linux LF cho toàn bộ script
├── .gitignore                    # Bộ lọc file tạm, file cá nhân và trạng thái nội bộ
├── deploy.ps1                    # Script tự động triển khai từ Windows (PowerShell)
├── deploy.sh                     # Script cài đặt, phân quyền và xác minh trên Ubuntu
└── README.md                     # Hướng dẫn sử dụng chi tiết cho thành viên nhóm
```

---

## 3. Danh Mục Chỉ Số Giám Sát & Triggers

### 3.1 Custom Items (Chu kỳ lấy mẫu: 15s)
* `custom.nginx.response_ms`: Thời gian phản hồi trang chủ Nginx tính bằng mili-giây (ms).
* `custom.nginx.error_5xx`: Số lỗi HTTP 5xx ghi nhận trong `/var/log/nginx/access.log`.
* `custom.nginx.active_conn`: Số kết nối đang hoạt động đọc từ `http://127.0.0.1:8080/basic_status`.
* `custom.sys.zombie_procs`: Số tiến trình Zombie (trạng thái `Z`) trên hệ điều hành.
* `custom.sys.failed_units`: Số dịch vụ systemd đang bị lỗi (`--state=failed`).
* `custom.sys.disk_io_util`: Tỷ lệ phần trăm tải I/O ổ đĩa (`%util`).

> **Cơ chế An toàn (Fail-Safe)**: Mọi script thu thập đều có bẫy lỗi (`trap`), đảm bảo khi Nginx dừng hoặc có lỗi xảy ra thì luôn trả về giá trị số hợp lệ (mặc định là `0` hoặc `0.0`), không bao giờ để Zabbix rơi vào trạng thái `ZBX_NOTSUPPORTED`.

### 3.2 Cảnh Báo Tự Động (Triggers)
* **High**: `last(/web-server/custom.nginx.error_5xx) > 0` (Phát hiện lỗi HTTP 5xx).
* **Average**: `last(/web-server/custom.sys.failed_units) > 0` (Có dịch vụ systemd bị dừng đột ngột).
* **Warning**: `last(/web-server/custom.nginx.response_ms) > 500` (Độ trễ trang web vượt quá 500ms).

---

## 4. Hướng Dẫn Cài Đặt & Chạy Thử Từ A-Z (Dành Cho Thành Viên Nhóm)

### Bước 1: Clone mã nguồn về máy
```bash
git clone https://github.com/NB-Luan/zabbix-automation.git
cd zabbix-automation
```

### Bước 2: Cấu hình môi trường (Nếu khác IP mặc định)
Dự án đã thiết lập sẵn các giá trị mặc định chuẩn phòng lab. Nếu dải IP máy ảo của bạn khác, hãy tạo file `.env` từ file mẫu:
```bash
# Windows PowerShell:
Copy-Item .env.example .env

# Linux / macOS:
cp .env.example .env
```
Mở file `.env` và chỉnh sửa các biến nếu cần:
```env
WEB_SERVER_IP=192.168.56.21
WEB_SERVER_USER=linux-moniter
ZABBIX_SERVER_IP=192.168.56.10
ZABBIX_API_USER=Admin
ZABBIX_API_PASS=zabbix
```

### Bước 3: Đẩy mã nguồn & Triển khai lên VM2 (`web-server`)

#### Cách A: Chạy từ Windows (Khuyến nghị)
Mở PowerShell tại thư mục dự án và chạy:
```powershell
.\deploy.ps1
```
*Script sẽ tự động:*
1. Đồng bộ file sang thư mục tạm `/tmp/zabbix_deploy/` trên VM2 qua SCP.
2. Khử sạch toàn bộ ký tự ngắt dòng Windows CRLF (`\r`) sang chuẩn Linux LF.
3. Cài đặt các script vào `/usr/local/bin/` và cấu hình vào `/etc/zabbix/zabbix_agent2.d/`.
4. Cấp quyền thực thi (`chmod 755`) và khởi động lại dịch vụ `zabbix-agent2`.
5. Tự động chạy `zabbix_agent2 -t` kiểm tra cả 6 key.

#### Cách B: Chạy trực tiếp từ máy ảo VM2 (hoặc máy Linux)
Nếu copy folder code trực tiếp sang VM2, chạy lệnh:
```bash
bash deploy.sh
```

---

### Bước 4: Thiết lập Items & Triggers trên Zabbix Server (VM1)
Chạy script Python để tự động kết nối Zabbix API, cấu hình Macro cổng 8080, tạo Items và Triggers:
```bash
python scripts/zabbix_api_setup.py
```
*Kết quả:* Toàn bộ Items và Triggers được tạo trên host `web-server` với trạng thái `Supported` và `OK`.

---

### Bước 5: Chạy Kịch Bản Giả Lập Sự Cố (Demo & Báo Cáo)
Trên máy ảo **VM2 (`web-server`)**, chạy công cụ mô phỏng sự cố:
```bash
# Vào VM2 qua SSH:
ssh linux-moniter@192.168.56.21

# Mở giao diện menu tương tác:
./simulate_incident.sh
```

Menu tương tác gồm 3 chế độ:
* **Phím 1 (`--stress`)**: Giả lập quá tải CPU & 70% RAM trong 60 giây bằng `stress-ng` (tự động cài nếu thiếu).
* **Phím 2 (`--storm`)**: Giả lập bão 1.000 HTTP requests vào Nginx với độ đồng thời 10.
* **Phím 3 (`--outage`)**: Dừng Nginx 45 giây để kích hoạt Trigger trên Zabbix Server, sau đó tự động khôi phục dịch vụ.

#### Quan sát kết quả trên Zabbix Web:
Truy cập: **`http://192.168.56.10/zabbix`** (User: `Admin` / Pass: `zabbix`) -> Vào mục **Monitoring** -> **Problems** để xem Trigger chuyển trạng thái màu đỏ (**PROBLEM**) trong lúc có sự cố và tự động chuyển về xanh (**RESOLVED**) khi hệ thống khôi phục.

---

## 5. Xử Lý Sự Cố Thường Gặp (Troubleshooting)

1. **Lỗi `sudo: interactive authentication is required` khi chạy deploy**:
   - Nếu user `linux-moniter` yêu cầu mật khẩu sudo, chạy lệnh sau 1 lần trên VM2 để bật quyền không hỏi mật khẩu:
     ```bash
     echo "$USER ALL=(ALL) NOPASSWD: ALL" | sudo tee /etc/sudoers.d/$USER
     ```
   - Hoặc truyền mật khẩu qua tham số: `.\deploy.ps1 -SudoPassword '<mat_khau>'`.

2. **Lỗi SSH kết nối từ chối (Permission denied)**:
   - Copy SSH public key từ máy Windows sang VM2:
     ```powershell
     type $env:USERPROFILE\.ssh\id_ed25519.pub | ssh linux-moniter@192.168.56.21 "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
     ```

---

## 6. Giao Diện Web Dashboard Giám Sát Thời Gian Thực (NOC Dashboard)

Dự án cung cấp một ứng dụng Web Dashboard trực quan và hiện đại chạy trên nền **Python Flask**, **TailwindCSS** và **Chart.js** nằm trong thư mục `web_dashboard/`.

### 6.1 Các Tính Năng Nổi Bật
* **Giao diện NOC Dark Mode**: Thiết kế tối ưu cho trung tâm điều hành mạng, tự động cập nhật dữ liệu từ Zabbix Server mỗi 5 giây mà không cần tải lại trang.
* **6 Thẻ Chỉ Số KPI Thời Gian Thực**:
  * Độ trễ phản hồi Web (`response_ms`)
  * Số kết nối đang hoạt động (`active_conn`)
  * Số lỗi HTTP 5xx (`error_5xx`)
  * Số tiến trình Zombie (`zombie_procs`)
  * Số dịch vụ systemd bị hỏng (`failed_units`)
  * Tải I/O ổ đĩa (`disk_io_util`)
* **2 Biểu Đồ Đường Realtime**: Trực quan hóa độ biến thiên thời gian thực của độ trễ và lưu lượng kết nối.
* **Bảng Cảnh Báo Trạng Thái Sự Cố (Active Problems)**: Tự động phát hiện và hiển thị các cảnh báo đang kích hoạt từ Zabbix Server, chuyển hiệu ứng đèn đỏ nhấp nháy khi có sự cố.
* **Bảng Điều Khiển Giả Lập Sự Cố Từ Xa (Interactive Chaos Lab)**: Tích hợp 3 nút kích hoạt các kịch bản kiểm thử trực tiếp lên VM2 qua kết nối SSH:
  1. **Bão 1.000 HTTP Requests (`--storm`)**
  2. **Quá tải CPU/RAM 60 giây (`--stress`)**
  3. **Dừng Nginx 45 giây (`--outage`)**
  Kèm theo **Live Terminal Console** hiển thị log phản hồi thời gian thực từ VM2 ngay trên trang web.

### 6.2 Hướng Dẫn Cài Đặt & Chạy Web Dashboard
1. Cài đặt các thư viện cần thiết:
   ```bash
   pip install -r web_dashboard/requirements.txt
   ```
2. Khởi chạy ứng dụng Dashboard:
   ```bash
   python web_dashboard/app.py
   ```
3. Mở trình duyệt và truy cập:
   ```text
   http://localhost:5000
   ```
   *(Hoặc từ máy khác trong cùng mạng LAN: `http://<IP_MAY_BAN>:5000`)*
