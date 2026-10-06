import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

APP_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, APP_DIR)

from downloader import MUSIC_DIR, search_tracks, download_and_process, remove_accents

def main():
    print("=" * 60)
    print("   🎵 MUIF MUSIC DOWNLOADER - TẢI NHẠC MP3 (128 KBPS)")
    print("=" * 60)

    # 1. Select Folder
    all_folders = [d for d in sorted(os.listdir(MUSIC_DIR)) 
                   if os.path.isdir(os.path.join(MUSIC_DIR, d)) and not d.startswith('.')]
    if "downloadmp3" in all_folders:
        all_folders.remove("downloadmp3")
        folders = ["downloadmp3"] + all_folders
    else:
        folders = ["downloadmp3"] + all_folders

    print("\n📁 Danh sách thư mục lưu nhạc:")
    for idx, f in enumerate(folders, 1):
        def_tag = " (Mặc định)" if f == "downloadmp3" else ""
        print(f"  [{idx}] {f}{def_tag}")
    print(f"  [0] + Tạo thư mục mới")

    chosen_folder = "downloadmp3"
    while True:
        choice = input("\n👉 Chọn số thứ tự thư mục (mặc định [1] -> downloadmp3): ").strip()
        if not choice or choice == "1":
            chosen_folder = folders[0]
            break
        if choice == "0":
            new_f = input("Nhập tên thư mục mới muốn tạo: ").strip()
            if new_f:
                chosen_folder = new_f
                break
        elif choice.isdigit() and 1 <= int(choice) <= len(folders):
            chosen_folder = folders[int(choice) - 1]
            break
        print("Lựa chọn không hợp lệ, vui lòng nhập lại.")

    print(f"--> Thư mục đích: [{chosen_folder}]")

    while True:
        print("\n" + "-" * 50)
        query = input("🔍 Nhập tên bài hát hoặc dán link YouTube (gõ 'q' để thoát): ").strip()
        if not query or query.lower() == 'q':
            print("Tạm biệt!")
            break

        print(f"Đang tìm kiếm bài hát: '{query}'...")
        results = search_tracks(query, limit=5)
        if not results:
            print("❌ Không tìm thấy bài hát phù hợp.")
            continue

        print("\nDanh sách kết quả tìm được:")
        for idx, t in enumerate(results, 1):
            disp = f"{t['clean_artist']} - {t['clean_song']}" if t['clean_artist'] else t['clean_song']
            print(f"  [{idx}] {disp}  [{t['duration']}]")
            print(f"      (Nguồn: {t['raw_title']})")

        sel = input("\n👉 Chọn bài muốn tải [1-5] (mặc định [1], gõ 'c' để hủy): ").strip()
        if sel.lower() == 'c':
            continue
        pick_idx = 0
        if sel.isdigit() and 1 <= int(sel) <= len(results):
            pick_idx = int(sel) - 1

        chosen = results[pick_idx]
        chosen_disp = f"{chosen['clean_artist']} - {chosen['clean_song']}" if chosen['clean_artist'] else chosen['clean_song']
        print(f"\nĐã chọn: {chosen_disp}")

        custom_s = input(f"Sửa tên bài hát (Enter để giữ '{chosen['clean_song']}'): ").strip()
        if not custom_s: custom_s = chosen['clean_song']
        custom_s = remove_accents(custom_s)

        custom_a = input(f"Sửa tên nghệ sĩ (Enter để giữ '{chosen['clean_artist']}'): ").strip()
        if not custom_a: custom_a = chosen['clean_artist']
        custom_a = remove_accents(custom_a)

        print(f"\n🚀 Đang tải và nén MP3 128kbps...")
        try:
            res = download_and_process(chosen['url'], chosen_folder, custom_s, custom_a, chosen['thumbnail'])
            print(f"✅ THÀNH CÔNG (128kbps)! File đã lưu tại:")
            print(f"   📂 {res['path']}")
        except Exception as e:
            print(f"❌ Lỗi khi tải: {e}")

if __name__ == "__main__":
    main()
