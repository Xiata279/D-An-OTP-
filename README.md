# LuânEm Tool - Ultimate Spam OTP (v3.0)

Dự án nghiên cứu bảo mật và kiểm thử API OTP (Đồ án sinh viên).
Phiên bản nâng cấp giao diện **Glassmorphism** và hệ thống Anti-Block mới nhất.

## Tính năng nổi bật
- **Giao diện Sinh viên IT**: Đẹp, hiện đại, tối giản.
- **Hệ thống thật (Real-time)**:
  - Log hiển thị trực tiếp từ tiến trình spam.
  - Thống kê (Sent/Success/Fail) chính xác 100%.
- **Anti-Block**: Tự động random User-Agent (iPhone, Android, PC...) để tránh bị chặn.
- **Đa luồng (Multi-thread)**: Tốc độ xử lý nhanh, tối ưu tài nguyên.

## Cài đặt & Chạy
1. Cài đặt [Python 3.12+](https://www.python.org/downloads/).
2. Chạy file `run.bat` để tự động cài thư viện và mở tool.
   - Hoặc chạy lệnh thủ công:
     ```bash
     pip install -r requirements.txt
     python app.py
     ```
3. Truy cập: `http://127.0.0.1:5000`

## Cấu trúc dự án
- `app.py`: Backend Flask xử lý API và luồng spam.
- `spam_otp.py`: Module core chứa logic gửi request đến các dịch vụ (Shopee, Viettel, TV360...).
- `templates/index.html`: Giao diện người dùng (HTML5 + Glassmorphism).
- `static/`: Chứa file CSS và JS.

## Tác giả
- **LuânEm** (Dev)

---
*Lưu ý: Tool chỉ phục vụ mục đích học tập và kiểm thử. Không sử dụng để quấy rối người khác.*
