# Hướng Dẫn Sử Dụng Công Cụ Tải Nhạc MP3 128kbps

Công cụ đã được cấu hình lưu vào thư mục **`downloadmp3`** và xuất âm thanh chất lượng chuẩn **MP3 128kbps** (tải nhanh, dung lượng gọn nhẹ, tự động làm sạch tên bài hát, nhúng thẻ ID3 và bìa thumbnail).

---

## 📁 Cấu trúc thư mục [downloadmp3](file:///d:/Noned/Music/downloadmp3)

```
d:\Noned\Music\downloadmp3\
├── TaiNhac_GiaoDienWeb.bat       <-- Nhấp đúp mở giao diện Web (Khuyên dùng)
├── TaiNhac_DongLenh.bat          <-- Nhấp đúp mở cửa sổ dòng lệnh (CLI)
├── downloader.py                 <-- Bộ xử lý lõi & máy chủ HTTP (cổng 8899)
├── cli.py                        <-- Giao diện dòng lệnh
├── HUONG_DAN_TAI_NHAC.md         <-- Hướng dẫn sử dụng tổng hợp
├── web\
│   └── index.html                <-- Giao diện Web Dark Mode
└── chrome_extension\             <-- Tiện ích mở rộng cho trình duyệt Chrome
    ├── manifest.json             <-- Cấu hình extension (Manifest V3)
    ├── content.js                <-- Nút tải trực tiếp trên YouTube
    ├── popup.html / popup.js     <-- Giao diện popup tùy chỉnh
    └── HUONG_DAN_CAI_EXTENSION.md<-- Hướng dẫn cài đặt tiện ích Chrome
```

---

## 🚀 3 Cách Sử Dụng Tiện Lợi:

### 1. Dùng Giao diện Web (Khuyên dùng - Đẹp & Trực quan)
- Nhấp đúp vào [**`TaiNhac_GiaoDienWeb.bat`**](file:///d:/Noned/Music/downloadmp3/TaiNhac_GiaoDienWeb.bat).
- Trình duyệt sẽ tự động mở giao diện tại `http://127.0.0.1:8899`.
- Thư mục lưu mặc định được chọn sẵn là **`downloadmp3`** (có thể chọn thư mục khác trong danh sách).
- Nhập tên bài hát hoặc dán link YouTube ➔ Bấm **Tìm kiếm** ➔ Bấm **Tải (128k)** ➔ Nhạc sẽ được nén MP3 128kbps và lưu vào máy.

### 2. Dùng Tiện ích mở rộng Chrome Extension (Tải 1-Click ngay trên YouTube)
- Bật máy chủ ngầm bằng cách chạy [**`TaiNhac_GiaoDienWeb.bat`**](file:///d:/Noned/Music/downloadmp3/TaiNhac_GiaoDienWeb.bat).
- Cài đặt tiện ích theo hướng dẫn tại [**`HUONG_DAN_CAI_EXTENSION.md`**](file:///d:/Noned/Music/downloadmp3/chrome_extension/HUONG_DAN_CAI_EXTENSION.md).
- Khi đang nghe nhạc trên YouTube, bấm trực tiếp nút **`[🎵 Tải MP3 128k]`** bên cạnh nút Like/Share để tải ngay về máy.

### 3. Dùng Cửa sổ Dòng lệnh (CLI)
- Nhấp đúp vào [**`TaiNhac_DongLenh.bat`**](file:///d:/Noned/Music/downloadmp3/TaiNhac_DongLenh.bat).
- Chọn thư mục lưu (mặc định phím Enter chọn `downloadmp3`).
- Nhập tên bài hát hoặc link YouTube và chọn bài muốn tải theo danh sách hiển thị.

---

## ⚙️ Yêu Cầu Môi Trường:
- **Python 3.10+** (kèm thư viện `yt-dlp` và `mutagen`).
- **FFmpeg** (đã được cài đặt và cấu hình trong PATH hệ thống).
