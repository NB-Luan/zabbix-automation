#!/usr/bin/env python3
"""
create_guide_docx.py
Tạo tài liệu Word (.docx) hướng dẫn chi tiết thực hành chạy dự án trong VS Code
và kịch bản thuyết trình đồ án giám sát Zabbix 7.0 & NOC Dashboard.
"""
import os
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

OUTPUT_FILE = r"D:\Dang Luan\Documents\Study\Projects\Linux\Code\zabbix-automation\HUONG_DAN_THUYET_TRINH_VA_CHAY_DU_AN_VSCODE.docx"

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'''
        <w:tcMar {nsdecls("w")}>
            <w:top w:w="{top}" w:type="dxa"/>
            <w:bottom w:w="{bottom}" w:type="dxa"/>
            <w:left w:w="{left}" w:type="dxa"/>
            <w:right w:w="{right}" w:type="dxa"/>
        </w:tcMar>
    ''')
    tcPr.append(tcMar)

def add_code_block(doc, code_text):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    set_cell_background(cell, "F1F5F9")
    set_cell_margins(cell, top=120, bottom=120, left=200, right=200)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.15
    run = p.add_run(code_text.strip())
    run.font.name = "Consolas"
    run.font.size = Pt(9.5)
    run.font.color.rgb = RGBColor(15, 23, 42)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

def add_callout(doc, title, text, bg_hex="ECFDF5", border_hex="10B981"):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    set_cell_background(cell, bg_hex)
    set_cell_margins(cell, top=120, bottom=120, left=200, right=200)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    r_title = p.add_run(title + "\n")
    r_title.bold = True
    r_title.font.name = "Calibri"
    r_title.font.size = Pt(11)
    r_title.font.color.rgb = RGBColor(15, 23, 42)
    
    r_text = p.add_run(text)
    r_text.font.name = "Calibri"
    r_text.font.size = Pt(10)
    r_text.font.color.rgb = RGBColor(51, 65, 85)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

def main():
    doc = Document()

    # Set page margins (1 inch)
    for section in doc.sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.9)
        section.right_margin = Inches(0.9)

    # --------------------------------------------------------------------------
    # HEADER / TIÊU ĐỀ CHÍNH
    # --------------------------------------------------------------------------
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(0)
    p_title.paragraph_format.space_after = Pt(4)
    run_title = p_title.add_run("CẨM NANG THỰC HÀNH & KỊCH BẢN THUYẾT TRÌNH ĐỒ ÁN")
    run_title.bold = True
    run_title.font.name = "Calibri"
    run_title.font.size = Pt(18)
    run_title.font.color.rgb = RGBColor(30, 58, 138) # Dark Blue

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_after = Pt(16)
    run_sub = p_sub.add_run("Hệ Thống Tự Động Hóa Giám Sát Nginx & Hạ Tầng Linux Với Zabbix 7.0 và Web NOC Dashboard\nThao Tác Hoàn Toàn Trong VS Code Terminal & Trình Duyệt Web")
    run_sub.font.name = "Calibri"
    run_sub.font.size = Pt(12)
    run_sub.font.italic = True
    run_sub.font.color.rgb = RGBColor(71, 85, 105)

    doc.add_paragraph().paragraph_format.space_after = Pt(2)

    # --------------------------------------------------------------------------
    # PHẦN 1: CHUẨN BỊ TRƯỚC KHI THUYẾT TRÌNH
    # --------------------------------------------------------------------------
    h1 = doc.add_heading(level=1)
    r1 = h1.add_run("PHẦN 1: CHUẨN BỊ MÔI TRƯỜNG TRONG VS CODE (5 PHÚT TRƯỚC GIỜ G)")
    r1.font.name = "Calibri"
    r1.font.size = Pt(14)
    r1.bold = True
    r1.font.color.rgb = RGBColor(30, 58, 138)

    p_prep = doc.add_paragraph()
    p_prep.add_run("Khi ngồi vào bàn chuẩn bị thuyết trình, bạn thực hiện đúng 4 bước thiết lập sau để mọi thứ sẵn sàng:")

    # Bước 1.1
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.2)
    r = p.add_run("Bước 1: Khởi động 2 máy ảo trên VMware / VirtualBox\n")
    r.bold = True
    p.add_run("• Bật máy ảo ")
    p.add_run("VM1 (zabbix-server - 192.168.56.10)").bold = True
    p.add_run(": Máy chủ giám sát Zabbix 7.0.\n• Bật máy ảo ")
    p.add_run("VM2 (web-server - 192.168.56.21)").bold = True
    p.add_run(": Máy chủ dịch vụ Web Nginx cài Zabbix Agent 2.\n")
    p.add_run("=> Sau khi bật lên, thu nhỏ cửa sổ VMware xuống thanh taskbar, ")
    p.add_run("KHÔNG CẦN đụng vào cửa sổ VMware nữa").bold = True
    p.add_run(" vì ta sẽ điều khiển hoàn toàn trong VS Code.")

    # Bước 1.2
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.2)
    r = p.add_run("Bước 2: Mở thư mục dự án trong VS Code\n")
    r.bold = True
    p.add_run("• Mở VS Code -> Chọn ")
    p.add_run("File -> Open Folder...").bold = True
    p.add_run(" -> Chọn thư mục:\n  ")
    p.add_run("D:\\Dang Luan\\Documents\\Study\\Projects\\Linux\\Code\\zabbix-automation").italic = True

    # Bước 1.3
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.2)
    r = p.add_run("Bước 3: Mở và Tách đôi Terminal trong VS Code (Split Terminal)\n")
    r.bold = True
    p.add_run("• Nhấn tổ hợp phím ")
    p.add_run("Ctrl + `").bold = True
    p.add_run(" (hoặc chọn menu Terminal -> New Terminal) để mở Terminal phía dưới VS Code.\n")
    p.add_run("• Bấm nút ")
    p.add_run("Split Terminal (biểu tượng chia đôi màn hình | )").bold = True
    p.add_run(" ở góc trên thanh công cụ Terminal của VS Code để có 2 nửa cửa sổ Terminal cạnh nhau:\n")
    p.add_run("  - Nửa bên trái (Terminal 1 - Chạy Dashboard): ").bold = True
    p.add_run("Gõ lệnh bật máy chủ Web Dashboard:\n")
    add_code_block(doc, "python web_dashboard/app.py")
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.2)
    p.add_run("    (Khi thấy hiện dòng chữ 'Running on http://127.0.0.1:5000' là xong, cứ để đó chạy ngầm).\n")
    p.add_run("  - Nửa bên phải (Terminal 2 - SSH sang máy ảo VM2): ").bold = True
    p.add_run("Gõ lệnh kết nối trực tiếp vào máy ảo Linux:\n")
    add_code_block(doc, "ssh linux-moniter@192.168.56.21")
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.2)
    p.add_run("    (Do máy đã cấu hình sẵn SSH Key nên gõ lệnh này là vào thẳng dấu nhắc lệnh Linux 'linux-moniter@web-server:~$').")

    # Bước 1.4
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.2)
    r = p.add_run("Bước 4: Mở sẵn 2 Tab trình duyệt Web trên máy tính\n")
    r.bold = True
    p.add_run("• Tab 1: Web Zabbix Server chuẩn: ")
    p.add_run("http://192.168.56.10/zabbix").bold = True
    p.add_run(" (User: Admin / Pass: zabbix).\n• Tab 2: NOC Web Dashboard của nhóm: ")
    p.add_run("http://localhost:5000").bold = True
    p.add_run(" (Mở trực tiếp, không cần đăng nhập).")

    add_callout(doc, "TỔNG KẾT BỐ CỤC MÀN HÌNH KHI THUYẾT TRÌNH:", 
                "• Nửa màn hình bên trái: Cửa sổ VS Code (đang mở Terminal SSH vào VM2).\n"
                "• Nửa màn hình bên phải: Trình duyệt mở Tab NOC Dashboard (localhost:5000) và Tab Zabbix Web.\n"
                "Cách bố trí này tạo ấn tượng cực kỳ chuyên nghiệp như một Kỹ sư DevOps/NOC thực thụ đang làm việc!", 
                "EFF6FF", "3B82F6")

    # --------------------------------------------------------------------------
    # PHẦN 2: KỊCH BẢN THUYẾT TRÌNH CHI TIẾT TỪNG BƯỚC
    # --------------------------------------------------------------------------
    h2 = doc.add_heading(level=1)
    r2 = h2.add_run("PHẦN 2: KỊCH BẢN THUYẾT TRÌNH TỪNG BƯỚC (NÓI GÌ - LÀM GÌ - MẮT NHÌN ĐÂU)")
    r2.font.name = "Calibri"
    r2.font.size = Pt(14)
    r2.bold = True
    r2.font.color.rgb = RGBColor(30, 58, 138)

    # Giai đoạn 1
    doc.add_heading("1. Giai Đoạn 1: Mở Đầu & Giới Thiệu Hạ Tầng 2 Máy Ảo Linux (1.5 phút)", level=2)
    p = doc.add_paragraph()
    p.add_run("Hành động trên VS Code Terminal (Terminal 2 - VM2):").bold = True
    p.add_run("\nGõ lệnh kiểm tra trạng thái dịch vụ trên VM2:")
    add_code_block(doc, "sudo systemctl status nginx zabbix-agent2 --no-pager")

    p = doc.add_paragraph()
    p.add_run("Mắt nhìn vào đâu: ").bold = True
    p.add_run("Nhìn vào màn hình Terminal thấy 2 dòng màu xanh lá cây ")
    p.add_run("Active: active (running)").bold = True
    p.add_run(" của dịch vụ Nginx và Zabbix Agent 2.")

    p = doc.add_paragraph()
    p.add_run("Lời nói với thầy:").bold = True
    p_say = doc.add_paragraph()
    p_say.paragraph_format.left_indent = Inches(0.3)
    p_say.add_run('"Kính thưa thầy, đề tài của nhóm em là Xây dựng hệ thống tự động hóa giám sát chuyên sâu máy chủ Nginx và hạ tầng Linux bằng Zabbix 7.0 kết hợp Web NOC Dashboard.\n'
              'Đầu tiên, hệ thống của nhóm em hoạt động trên 2 máy ảo phân tách vai trò rõ ràng:\n'
              '- Máy ảo VM1 (192.168.56.10): Là Zabbix Server 7.0 trung tâm chịu trách nhiệm phân tích và kích hoạt cảnh báo.\n'
              '- Máy ảo VM2 (192.168.56.21): Là máy chủ dịch vụ Web Nginx cài đặt Zabbix Agent 2.\n'
              'Như thầy thấy trên màn hình Terminal VS Code kết nối SSH vào VM2, cả 2 dịch vụ Nginx và Zabbix Agent 2 đều đang chạy ở trạng thái active (running)."').italic = True

    # Giai đoạn 2
    doc.add_heading("2. Giai Đoạn 2: Cho Thầy Xem Các Script Thu Thập Chuyên Sâu Tự Viết (1.5 phút)", level=2)
    p = doc.add_paragraph()
    p.add_run("Hành động trên VS Code Terminal (Terminal 2 - VM2):").bold = True
    p.add_run("\nGõ lần lượt 3 lệnh sau:")
    add_code_block(doc, "# 1. Xem cấu hình UserParameter của Agent 2:\ncat /etc/zabbix/zabbix_agent2.d/custom_monitor.conf\n\n# 2. Xem file script trong thư mục hệ thống:\nls -la /usr/local/bin/nginx_custom_metrics.sh /usr/local/bin/system_health_check.sh\n\n# 3. Test lấy chỉ số thực tế bằng chính Zabbix Agent 2:\nzabbix_agent2 -t custom.nginx.active_conn\nzabbix_agent2 -t custom.nginx.response_ms")

    p = doc.add_paragraph()
    p.add_run("Mắt nhìn vào đâu: ").bold = True
    p.add_run("Nhìn vào dòng kết quả trả về của lệnh test: ")
    p.add_run("custom.nginx.active_conn [s|1]").bold = True
    p.add_run(" và ")
    p.add_run("custom.nginx.response_ms [s|1]").bold = True
    p.add_run(" (hoặc số ms). Kết quả trả về là số thực tế, không bị lỗi ZBX_NOTSUPPORTED.")

    p = doc.add_paragraph()
    p.add_run("Lời nói với thầy:").bold = True
    p_say = doc.add_paragraph()
    p_say.paragraph_format.left_indent = Inches(0.3)
    p_say.add_run('"Thưa thầy, điểm cốt lõi của đề tài là nhóm em đã tự lập trình các bộ script chuyên sâu đặt tại /usr/local/bin/:\n'
              '- custom.nginx.response_ms: Đo độ trễ phản hồi trang web tính bằng mili-giây.\n'
              '- custom.nginx.active_conn: Đếm kết nối đang hoạt động từ stub_status cổng 8080.\n'
              '- custom.nginx.error_5xx: Đếm lỗi HTTP 5xx từ access log.\n'
              '- custom.sys.zombie_procs & failed_units: Phát hiện tiến trình Zombie và dịch vụ systemd bị hỏng.\n'
              'Em vừa cho Agent 2 chạy thử trực tiếp, kết quả trả về tức thì dạng số nguyên, chứng minh các script thu thập hoạt động chuẩn xác trên nhân Linux."').italic = True

    # Giai đoạn 3
    doc.add_heading("3. Giai Đoạn 3: Trình Diễn Zabbix Server 7.0 & Web NOC Dashboard (1.5 phút)", level=2)
    p = doc.add_paragraph()
    p.add_run("Hành động trên Trình duyệt Web:").bold = True
    p.add_run("\n• Bấm sang Tab Zabbix Web: ")
    p.add_run("http://192.168.56.10/zabbix").bold = True
    p.add_run(" -> Vào mục Monitoring -> Hosts.\n• Bấm sang Tab NOC Dashboard của nhóm: ")
    p.add_run("http://localhost:5000").bold = True
    p.add_run(".")

    p = doc.add_paragraph()
    p.add_run("Mắt nhìn vào đâu:").bold = True
    p.add_run("\n• Trên Zabbix Web: Nhìn thấy host ")
    p.add_run("web-server (192.168.56.21:10050)").bold = True
    p.add_run(" có biểu tượng đèn ")
    p.add_run("ZBX màu xanh lá").bold = True
    p.add_run(" (kết nối Agent 2 thông suốt).\n• Trên Web Dashboard: Nhìn thấy khung banner màu xanh ngọc: ")
    p.add_run('"Tất Cả Hệ Thống Hoạt Động Bình Thường (0 Active Alerts)"').bold = True
    p.add_run(", 6 thẻ chỉ số KPI có số liệu và 2 biểu đồ đường Chart.js đang chạy.")

    p = doc.add_paragraph()
    p.add_run("Lời nói với thầy:").bold = True
    p_say = doc.add_paragraph()
    p_say.paragraph_format.left_indent = Inches(0.3)
    p_say.add_run('"Để quản lý giám sát, nhóm em đã viết script Python zabbix_api_setup.py gọi Zabbix JSON-RPC API tự động thêm host và thiết lập các ngưỡng cảnh báo Trigger (High, Average, Warning).\n'
              'Ngoài ra, nhóm em tự xây dựng thêm ứng dụng Web NOC Dashboard thời gian thực (nền tảng Flask + TailwindCSS + Chart.js). Cứ mỗi 5 giây, web tự động đồng bộ dữ liệu từ Zabbix Server mà không cần tải lại trang. Hiện tại hệ thống đang ở trạng thái an toàn tuyệt đối với 0 cảnh báo."').italic = True

    # Giai đoạn 4
    doc.add_heading("4. Giai Đoạn 4: Màn Trình Diễn Đắt Giá Nhất - Kích Hoạt Sự Cố & Quan Sát Đổi Màu (2 phút)", level=2)
    p = doc.add_paragraph()
    p.add_run("Đây là phần thuyết phục thầy nhất! Bạn cuộn chuột xuống phần ").bold = True
    p.add_run("Bảng Điều Khiển Giả Lập Sự Cố Từ Xa").bold = True
    p.add_run(" trên Dashboard (http://localhost:5000). Toàn bộ quá trình chia làm 4 nhịp rõ ràng:")

    # Thao tác A
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.2)
    p.add_run("A. Thao tác 1: Bấm nút Bão Request (Nút màu xanh dương --storm)\n").bold = True
    p.add_run("• Bạn bấm vào nút: ")
    p.add_run('"Bão 1.000 HTTP Requests"').bold = True
    p.add_run(".\n• ")
    p.add_run("Mắt nhìn vào đâu: ").bold = True
    p.add_run("Nhìn ngay vào ô Terminal màu đen bên dưới web. Thấy các dòng chữ chạy ra: Connecting to SSH -> Dispatching 1,000 requests -> ")
    p.add_run("[PASS] Mode 2 completed -> [TASK FINISHED]: SUCCESS").bold = True
    p.add_run(" trong đúng 4 giây. Hai biểu đồ đường phía trên giật nảy lên một nhịp rồi ổn định.\n• ")
    p.add_run("Nói với thầy: ").bold = True
    p.add_run('"Nhóm em vừa kích hoạt từ xa đợt bão 1.000 request đồng thời qua SSH, Nginx vẫn xử lý mượt mà và Zabbix ghi nhận lưu lượng tức thời."').italic = True

    # Thao tác B
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.2)
    p.add_run("B. Thao tác 2: Tạo Sự Cố Để Hệ Thống Đổi Màu Từ XANH Sang ĐỎ\n").bold = True
    p.add_run("• Bạn bấm vào nút: ")
    p.add_run('"Dừng Nginx 45 Giây (Bật Alert)"').bold = True
    p.add_run(" (Nút màu đỏ --outage).\n  (Hoặc trên Terminal VM2 gõ lệnh tạo lỗi 500: ")
    p.add_run("'127.0.0.1 - - [17/Nov/2026:20:31:00 +0700] \"GET /error500 HTTP/1.1\" 500 0 \"-\" \"curl\"' | sudo tee -a /var/log/nginx/access.log").italic = True
    p.add_run(")\n• ")
    p.add_run("Mắt nhìn vào đâu (Chờ khoảng 15-20 giây):").bold = True
    p.add_run("\n  1. Khung banner màu xanh trên cùng Dashboard ")
    p.add_run("LẬP TỨC CHUYỂN SANG MÀU ĐỎ NHẤP NHÁY PHÁT SÁNG (alert-pulse)").bold = True
    p.add_run(", hiện dòng chữ to: ")
    p.add_run('"CẢNH BÁO: Phát hiện sự cố đang hoạt động trên Web Server!"').bold = True
    p.add_run("\n  2. Xuất hiện thẻ chi tiết sự cố màu đỏ: ")
    p.add_run("HIGH: Nginx HTTP 5xx errors detected on web-server").bold = True
    p.add_run(".\n  3. Chuyển sang Tab Zabbix Web mục Problems: Thấy xuất hiện dòng chữ đỏ cam ")
    p.add_run("PROBLEM").bold = True
    p.add_run(".\n• ")
    p.add_run("Chỉ tay vào màn hình nói với thầy: ").bold = True
    p.add_run('"Thưa thầy, khi sự cố xảy ra, trong vòng 15 giây lấy mẫu, Zabbix Server lập tức bắt được lỗi, kích hoạt Trigger mức độ HIGH màu đỏ trên cả Zabbix lẫn giao diện NOC Dashboard!"').italic = True

    # Thao tác C
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.2)
    p.add_run("C. Thao tác 3: Tự Động Khôi Phục Hệ Thống Từ ĐỎ Trở Về XANH\n").bold = True
    p.add_run("• Bạn ")
    p.add_run("KHÔNG CẦN LÀM GÌ CẢ, CHỈ VIỆC NGỒI ĐỢI").bold = True
    p.add_run("! Hết 45 giây, script trên VM2 tự động bật lại Nginx.\n  (Nếu gõ lệnh 500 ở trên thì gõ xóa log: ")
    p.add_run("sudo truncate -s 0 /var/log/nginx/access.log").italic = True
    p.add_run(").\n• ")
    p.add_run("Mắt nhìn vào đâu (Chờ khoảng 15-20 giây tiếp theo):").bold = True
    p.add_run("\n  1. Trên Dashboard: Đèn đỏ nhấp nháy ")
    p.add_run("TỰ ĐỘNG TẮT").bold = True
    p.add_run(", banner chuyển lại về ")
    p.add_run("MÀU XANH AN TOÀN: 'Tất Cả Hệ Thống Hoạt Động Bình Thường (0 Active Alerts)'").bold = True
    p.add_run(".\n  2. Trên Zabbix Web mục Problems: Dòng chữ đỏ PROBLEM chuyển thành ")
    p.add_run("RESOLVED").bold = True
    p.add_run(".\n• ")
    p.add_run("Chốt câu kết ấn tượng với thầy: ").bold = True
    p.add_run('"Thầy có thể thấy sau khi dịch vụ phục hồi, hệ thống tự động xóa cảnh báo và trở về trạng thái xanh an toàn mà không cần con người can thiệp thủ công. Điều này chứng minh vòng đời tự động hóa khép kín: Đo đạc -> Bắt lỗi -> Cảnh báo -> Tự khôi phục!"').italic = True

    # --------------------------------------------------------------------------
    # PHẦN 3: BẢNG TRA CỨU TÀI KHOẢN & PHÍM TẮT VS CODE
    # --------------------------------------------------------------------------
    doc.add_page_break()
    h3 = doc.add_heading(level=1)
    r3 = h3.add_run("PHẦN 3: BẢNG TRA CỨU TÀI KHOẢN, MẬT KHẨU & PHÍM TẮT VS CODE")
    r3.font.name = "Calibri"
    r3.font.size = Pt(14)
    r3.bold = True
    r3.font.color.rgb = RGBColor(30, 58, 138)

    # Table 1: Credentials
    table = doc.add_table(rows=1, cols=4)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = table.rows[0].cells
    headers = ["Thành phần", "Địa chỉ truy cập (IP / URL)", "Tài khoản (Username)", "Mật khẩu (Password)"]
    for i, h in enumerate(headers):
        hdr[i].text = h
        hdr[i].paragraphs[0].runs[0].bold = True
        hdr[i].paragraphs[0].runs[0].font.name = "Calibri"
        hdr[i].paragraphs[0].runs[0].font.size = Pt(10)
        hdr[i].paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
        set_cell_background(hdr[i], "1E3A8A")
        set_cell_margins(hdr[i], top=100, bottom=100, left=150, right=150)

    creds = [
        ("Zabbix Server 7.0 (Web UI)", "http://192.168.56.10/zabbix", "Admin (chữ A viết hoa)", "zabbix"),
        ("Máy ảo VM2 (Web Server)", "192.168.56.21:22", "linux-moniter", "1 (hoặc SSH Key)"),
        ("Máy ảo VM1 (Zabbix Server)", "192.168.56.10:22", "zabbix-server", "1 (hoặc SSH Key)"),
        ("NOC Web Dashboard", "http://localhost:5000", "Không cần đăng nhập", "Không cần mật khẩu"),
    ]

    for item in creds:
        row = table.add_row().cells
        for i, val in enumerate(item):
            row[i].text = val
            row[i].paragraphs[0].runs[0].font.name = "Calibri"
            row[i].paragraphs[0].runs[0].font.size = Pt(9.5)
            set_cell_background(row[i], "F8FAFC" if creds.index(item) % 2 == 0 else "FFFFFF")
            set_cell_margins(row[i], top=80, bottom=80, left=120, right=120)

    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    # Phím tắt VS Code
    p_sc = doc.add_paragraph()
    p_sc.add_run("Các phím tắt cực kỳ tiện dụng trong VS Code:").bold = True
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.2)
    p.add_run("• ")
    p.add_run("Ctrl + ` (phím dấu huyền cạnh số 1)").bold = True
    p.add_run(": Đóng / Mở bảng Terminal dưới đáy VS Code.\n• ")
    p.add_run("Ctrl + Shift + 5").bold = True
    p.add_run(": Chia đôi Terminal (Split Terminal) thành 2 cửa sổ cạnh nhau.\n• ")
    p.add_run("Ctrl + C").bold = True
    p.add_run(": Dừng tiến trình đang chạy trong Terminal (ví dụ dừng Dashboard nếu muốn khởi động lại).\n• ")
    p.add_run("clear").bold = True
    p.add_run(" (hoặc Ctrl + L): Xóa sạch màn hình Terminal cho gọn gàng.")

    # --------------------------------------------------------------------------
    # PHẦN 4: TOP 6 CÂU HỎI VẤN ĐÁP THẦY HAY HỎI & CÂU TRẢ LỜI MẪU
    # --------------------------------------------------------------------------
    h4 = doc.add_heading(level=1)
    r4 = h4.add_run("PHẦN 4: TOP 6 CÂU HỎI PHẢN BIỆN CỦA THẦY & CÂU TRẢ LỜI CHUẨN KỸ THUẬT")
    r4.font.name = "Calibri"
    r4.font.size = Pt(14)
    r4.bold = True
    r4.font.color.rgb = RGBColor(30, 58, 138)

    qa_list = [
        ("Câu hỏi 1: Nhóm em dùng Zabbix Agent 1 hay Agent 2? Hai phiên bản này khác nhau thế nào?",
         'Trả lời: "Dạ thưa thầy, nhóm em sử dụng Zabbix Agent 2. Điểm cải tiến vượt trội là Agent 2 được viết bằng ngôn ngữ Go thay vì C như Agent 1. Nhờ đó, Agent 2 hỗ trợ cơ chế đa luồng (concurrency) tốt hơn, tiêu thụ ít tài nguyên CPU/RAM hơn và hỗ trợ kiến trúc plugin linh hoạt để mở rộng giám sát."'),
        
        ("Câu hỏi 2: Các file script đo đạc và cấu hình Agent nằm ở đâu trên máy ảo Linux?",
         'Trả lời: "Dạ thưa thầy:\n- File khai báo 6 UserParameter nằm tại: /etc/zabbix/zabbix_agent2.d/custom_monitor.conf trên VM2.\n- Các file shell script thực thi nằm trong thư mục: /usr/local/bin/nginx_custom_metrics.sh và /usr/local/bin/system_health_check.sh, được cấp quyền chmod 755 và thuộc quyền sở hữu của user zabbix."'),
        
        ("Câu hỏi 3: Nếu dịch vụ Nginx bị chết đột ngột, script của nhóm có làm Zabbix bị treo hoặc dính lỗi ZBX_NOTSUPPORTED không?",
         'Trả lời: "Dạ không thưa thầy. Nhóm em đã áp dụng cơ chế An toàn (Fail-Safe) với bẫy lỗi trap \'echo 0; exit 0\' ERR. Lệnh curl chỉ timeout trong 2 giây rồi thoát, luôn đảm bảo trả về giá trị số mặc định là 0 cùng mã thoát exit 0. Nhờ đó, Zabbix Server không bao giờ bị rơi vào trạng thái ZBX_NOTSUPPORTED."'),
        
        ("Câu hỏi 4: Làm sao Zabbix Server biết được các Item và Trigger này? Em cấu hình thủ công từng cái à?",
         'Trả lời: "Dạ không thưa thầy. Nhóm em tự động hóa 100% bằng script Python scripts/zabbix_api_setup.py gọi Zabbix JSON-RPC API. Script này tự đăng nhập Admin, tìm host web-server, cấu hình Macro cổng 8080 cho stub_status, và tự tạo toàn bộ 6 Items cùng 3 Triggers (High, Average, Warning) theo chu kỳ 15 giây."'),
        
        ("Câu hỏi 5: Giao diện Web NOC Dashboard (localhost:5000) nhóm em làm bằng gì và hoạt động ra sao?",
         'Trả lời: "Dạ thưa thầy, Dashboard được viết bằng Python Flask ở backend và TailwindCSS + Chart.js ở frontend. Cứ mỗi 5 giây, ứng dụng tự động gọi AJAX tới Zabbix JSON-RPC API để cập nhật 6 thẻ chỉ số và 2 biểu đồ đường thời gian thực. Khi Zabbix có sự cố, banner trên web tự đổi sang màu đỏ nhấp nháy phát sáng (alert-pulse) để cảnh báo cho kỹ sư trực ca."'),
        
        ("Câu hỏi 6: Tính năng Chaos Lab (giả lập sự cố) trên Dashboard kết nối tới máy ảo bằng cách nào?",
         'Trả lời: "Dạ thưa thầy, khi người dùng bấm nút trên web, backend Flask sử dụng thư viện Paramiko để mở một kết nối SSH an toàn (sử dụng khóa SSH Ed25519) tới VM2 (192.168.56.21). Nó kích hoạt script /home/linux-moniter/simulate_incident.sh trên VM2 và truyền log thực thi thời gian thực về khung Live Terminal Console trên trình duyệt web."')
    ]

    for q, a in qa_list:
        p_q = doc.add_paragraph()
        p_q.paragraph_format.space_before = Pt(8)
        p_q.paragraph_format.space_after = Pt(2)
        r_q = p_q.add_run(q)
        r_q.bold = True
        r_q.font.name = "Calibri"
        r_q.font.size = Pt(11)
        r_q.font.color.rgb = RGBColor(180, 83, 9) # Amber Brown

        p_a = doc.add_paragraph()
        p_a.paragraph_format.left_indent = Inches(0.2)
        p_a.paragraph_format.space_after = Pt(6)
        r_a = p_a.add_run(a)
        r_a.font.name = "Calibri"
        r_a.font.size = Pt(10)
        r_a.font.color.rgb = RGBColor(30, 41, 59)

    # Lưu tài liệu
    doc.save(OUTPUT_FILE)
    print(f"[SUCCESS] Tạo thành công file: {OUTPUT_FILE} ({os.path.getsize(OUTPUT_FILE):,} bytes)")

if __name__ == "__main__":
    main()
