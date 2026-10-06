# mp3Downloader

Công cụ tải và chuẩn hóa nhạc MP3 128kbps từ YouTube về máy tính với 3 giao diện: **Web UI**, **Chrome Extension** (1-click) và **CLI (Dòng lệnh)**.

## ✨ Tính năng nổi bật
- **Chất lượng MP3 128kbps chuẩn**: Tải nhanh, nhẹ máy, phù hợp lưu trữ số lượng lớn.
- **Làm sạch tên bài hát thông minh**:
  - Tự động nhận diện Ca sĩ & Tên bài hát qua danh bạ ca sĩ tích hợp sẵn.
  - Định dạng chuẩn: `Tên ca sĩ - Tên bài hát.mp3` (tiếng Việt không dấu).
  - Loại bỏ hoàn toàn các rác tiêu đề YouTube (`Official MV`, `Audio`, `Lyrics`, emojis, `[Hot TikTok]`, số đếm thông báo, v.v.).
- **Nhúng thẻ ID3 & Ảnh bìa**: Tự động gắn tag Title, Artist và nhúng ảnh thumbnail YouTube làm Cover Art.
- **Đa nền tảng giao diện**:
  - 🌐 **Web UI**: Giao diện Dark Mode trực quan tại `http://127.0.0.1:8899`.
  - 🧩 **Chrome Extension**: Nút bấm tải 1-chạm tích hợp trực tiếp trên trang video YouTube.
  - 💻 **CLI**: Giao diện dòng lệnh tương tác nhanh.

## 🚀 Cài đặt & Sử dụng

### 1. Yêu cầu hệ thống
- Python 3.10+
- FFmpeg (đã thêm vào PATH hệ thống)
- Các thư viện Python cần thiết:
  ```bash
  pip install yt-dlp mutagen
  ```

### 2. Khởi chạy
- **Web UI (Khuyên dùng)**: Nhấp đúp vào `TaiNhac_GiaoDienWeb.bat` hoặc chạy:
  ```bash
  python downloader.py
  ```
- **Dòng lệnh (CLI)**: Nhấp đúp vào `TaiNhac_DongLenh.bat` hoặc chạy:
  ```bash
  python cli.py
  ```
- **Cài đặt Chrome Extension**: Xem hướng dẫn tại `chrome_extension/HUONG_DAN_CAI_EXTENSION.md`.
