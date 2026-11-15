<!--
Sync Impact Report:
- Version change: 0.0.0 (Template) → 1.0.0
- List of modified principles:
  - [PRINCIPLE_1_NAME] → I. Linux Format & ShellCheck Compliance (NON-NEGOTIABLE)
  - [PRINCIPLE_2_NAME] → II. Fixed Target Architecture & Network Topology
  - [PRINCIPLE_3_NAME] → III. Fail-Safe Metric Collection (Zero Unsupported Items)
  - [PRINCIPLE_4_NAME] → IV. Fully Automated Remote Deployment (Zero Manual Edits)
- Added sections:
  - Platform & Environment Standards
  - Development Workflow & Quality Gates
- Removed sections:
  - [PRINCIPLE_5_NAME] (Removed unused placeholder slot; four core principles ratified)
- Follow-up TODOs: None
-->

# SYSTEM MONITORING WITH ZABBIX PLATFORM Constitution

## Core Principles

### I. Linux Format & ShellCheck Compliance (NON-NEGOTIABLE)
Mọi file kịch bản Bash (`.sh`) và file cấu hình (`.conf`, `.cnf`, `.yaml`) được tạo hoặc chỉnh sửa trên Windows **BẮT BUỘC** phải sử dụng định dạng xuống dòng chuẩn Linux LF (`\n`), tuyệt đối không sử dụng định dạng Windows CRLF (`\r\n`).
- Tất cả script Bash phải vượt qua kiểm tra cú pháp và chất lượng mã nguồn bằng `shellcheck` với mức lỗi nghiêm trọng (severity: error/warning) bằng 0 trước khi triển khai.
- Script phải tuân thủ chuẩn cấu trúc POSIX/Bash an toàn, khai báo `set -euo pipefail` hoặc có cơ chế bẫy lỗi (`trap`) phù hợp.
- **Lý do**: File có ký tự `\r` (CRLF) trên Linux sẽ gây lỗi cú pháp nghiêm trọng `^M: command not found` hoặc lỗi phân giải tham số cấu hình. ShellCheck đảm bảo tính ổn định và bảo mật của mã kịch bản.

### II. Fixed Target Architecture & Network Topology
Mọi kịch bản tự động hóa, cấu hình dịch vụ và template giám sát **BẮT BUỘC** tuân thủ tuyệt đối cấu trúc mạng và thông số môi trường cố định sau:
- **VM1 (`zabbix-server`)**:
  - Địa chỉ IP: `192.168.56.10`
  - SSH User: `zabbix-server`
  - Stack phần mềm: Zabbix Server 7.0 LTS, Cơ sở dữ liệu MySQL 8.4, Web Frontend trên Apache2.
- **VM2 (`web-server`)**:
  - Địa chỉ IP: `192.168.56.21`
  - SSH User: `linux-moniter`
  - Stack phần mềm: Web server Nginx (cổng 80 phục vụ web, cổng 8080 cấu hình module `stub_status`), Giám sát máy khách: Zabbix Agent 2.
- **Lý do**: Kiến trúc hạ tầng cố định đảm bảo tính lặp lại của kịch bản triển khai tự động hóa và ngăn ngừa xung đột cổng hoặc quyền truy cập.

### III. Fail-Safe Metric Collection (Zero Unsupported Items)
Tất cả các kịch bản thu thập chỉ số giám sát phục vụ `UserParameter` **BẮT BUỘC** phải có cơ chế xử lý ngoại lệ an toàn (fail-safe error handling).
- Khi dịch vụ đích bị dừng, endpoint không phản hồi, kết nối bị từ chối hoặc gặp dữ liệu bất thường, kịch bản **BẮT BUỘC** luôn trả về giá trị số hợp lệ (giá trị mặc định an toàn là `0`, hoặc mã lỗi dạng số đã định nghĩa), tuyệt đối không để script trả về chuỗi rỗng, crash hoặc exit với mã lỗi không được xử lý khiến Zabbix Server chuyển trạng thái item sang `Not supported`.
- Kịch bản giám sát phải đặt giới hạn thời gian thực thi (timeout tối đa 3 giây) để không làm nghẽn tiến trình của Zabbix Agent.
- **Lý do**: Tránh làm gián đoạn chu kỳ thu thập dữ liệu và giữ cho dashboard/trigger trên Zabbix Server luôn hoạt động liên tục mà không sinh cảnh báo sai lệch về hệ thống giám sát.

### IV. Fully Automated Remote Deployment (Zero Manual Edits)
Toàn bộ quy trình sao chép mã nguồn, cấu hình và kích hoạt dịch vụ từ môi trường phát triển Windows sang các máy ảo Ubuntu **BẮT BUỘC** phải được tự động hóa 100% qua SCP và SSH.
- Tuyệt đối không chỉnh sửa cấu hình thủ công trực tiếp bằng tay trên máy ảo.
- Mọi thay đổi phải xuất phát từ file nguồn lưu trữ trong repository, sau đó đẩy lên máy ảo bằng kịch bản triển khai (automation deployment scripts).
- **Lý do**: Đảm bảo nguyên tắc Infrastructure as Code (IaC), tính nhất quán giữa môi trường mã nguồn và máy chủ chạy thực tế, cho phép tái lập môi trường bất kỳ lúc nào.

## Platform & Environment Standards

- **Hệ điều hành mục tiêu**: Ubuntu Server 26.04 LTS (kiến trúc x86_64).
- **Phân quyền thực thi**: Các thao tác thay đổi file hệ thống hoặc khởi động lại dịch vụ (`systemctl`) phải được cấp quyền thông qua `sudo` không yêu cầu mật khẩu tương tác (sudoers entry) hoặc được cấu hình đặc quyền hợp lệ cho user `zabbix-server` và `linux-moniter`.
- **Bảo mật kết nối**: Ưu tiên sử dụng SSH Key-based Authentication giữa môi trường Windows và các VM để phục vụ các script tự động hóa không bị gián đoạn do prompt mật khẩu.

## Development Workflow & Quality Gates

Mọi tính năng và kịch bản mới phải vượt qua 4 chốt kiểm soát chất lượng (Quality Gates) trước khi đưa vào vận hành:
1. **Gate 1 - Line Ending Gate**: Kiểm tra tệp tin không chứa ký tự `\r` (LF-only check).
2. **Gate 2 - Static Analysis Gate**: Kiểm tra cú pháp script Bash bằng `shellcheck`.
3. **Gate 3 - Resilience Gate**: Kiểm tra hành vi của script giám sát trong cả 2 kịch bản: (a) khi dịch vụ hoạt động bình thường, và (b) khi dịch vụ bị dừng có chủ đích (phải trả về `0` và exit code 0).
4. **Gate 4 - Deployment Gate**: Kiểm tra tính năng triển khai qua SCP/SSH thành công và dịch vụ `zabbix-agent2` / `zabbix-server` reload cấu hình trơn tru.

## Governance

Bản Hiến pháp này là văn bản quy định cao nhất chi phối toàn bộ quy trình đặc tả (spec), lập kế hoạch (plan), phân chia công việc (tasks) và lập trình (implement) của dự án SYSTEM MONITORING WITH ZABBIX PLATFORM.
- **Quy trình sửa đổi**: Bất kỳ sự thay đổi nào đối với các nguyên tắc cốt lõi (Core Principles) hoặc topo hạ tầng phải được ghi chép lý do, cập nhật thông qua lệnh `/speckit-constitution`, và tăng số hiệu phiên bản theo quy tắc SemVer:
  - **MAJOR (X.0.0)**: Thay đổi phá vỡ tương thích, thay đổi nền tảng hệ điều hành hoặc kiến trúc mạng cơ sở.
  - **MINOR (1.X.0)**: Bổ sung nguyên tắc mới, thêm dịch vụ giám sát hoặc mở rộng các chốt kiểm soát chất lượng.
  - **PATCH (1.0.X)**: Đính chính diễn đạt, giải thích rõ ngữ nghĩa hoặc sửa đổi nhỏ không ảnh hưởng logic.
- **Tuân thủ**: Toàn bộ các bước tạo spec (`/speckit-specify`) và lập kế hoạch (`/speckit-plan`) phải chủ động tham chiếu các nguyên tắc trong tài liệu này.

**Version**: 1.0.0 | **Ratified**: 2026-11-15 | **Last Amended**: 2026-11-15
