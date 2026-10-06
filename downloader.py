import os
import re
import sys
import json
import urllib.parse
import urllib.request
import unicodedata
from http.server import HTTPServer, SimpleHTTPRequestHandler
import webbrowser
import threading

import yt_dlp
import mutagen
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC, ID3NoHeaderError

APP_DIR = os.path.dirname(os.path.abspath(__file__))
MUSIC_DIR = os.path.dirname(APP_DIR)

def clean_youtube_url(url):
    """
    Cleans YouTube URLs with playlist, radio, or tracking parameters
    down to just the single video URL: https://www.youtube.com/watch?v=VIDEO_ID
    """
    if not url:
        return url
    url = url.strip()
    if 'youtube.com' in url or 'youtu.be' in url:
        parsed = urllib.parse.urlparse(url)
        # youtu.be/ID
        if 'youtu.be' in parsed.netloc:
            video_id = parsed.path.strip('/')
            if video_id:
                return f"https://www.youtube.com/watch?v={video_id}"
        # youtube.com/shorts/ID
        elif '/shorts/' in parsed.path:
            parts = parsed.path.split('/shorts/')
            if len(parts) > 1:
                video_id = parts[1].split('/')[0]
                if video_id:
                    return f"https://www.youtube.com/watch?v={video_id}"
        # youtube.com/watch?v=ID
        else:
            qs = urllib.parse.parse_qs(parsed.query)
            if 'v' in qs and qs['v']:
                video_id = qs['v'][0]
                return f"https://www.youtube.com/watch?v={video_id}"
    return url

# --- ARTIST DATABASE & INTELLIGENT NAME CLEANER ---
ARTIST_CANONICAL = {}
KNOWN_ARTISTS = set()

BUILTIN_ARTISTS = [
    # Top VN Artists
    "Đen", "Đen Vâu", "Vũ", "Vũ.", "Sơn Tùng M-TP", "M-TP",
    "Soobin", "Soobin Hoàng Sơn", "Binz", "B-Ray", "Masew", "Karik",
    "JustaTee", "Hoàng Thùy Linh", "Hòa Minzy", "Đức Phúc", "Erik", "Hương Ly",
    "Phan Mạnh Quỳnh", "Mr. Siro", "Jack", "J97", "K-ICM", "ICM", "Tăng Duy Tân",
    "AMEE", "MIN", "Obito", "MCK", "RPT MCK", "RPT Gonzo", "RPT Orijinn", "Low G",
    "Tlinh", "GREY D", "Wren Evans", "HIEUTHUHAI", "MONO", "Vũ Cát Tường",
    "Phương Mỹ Chi", "Đoàn Thúy Trang", "BigDaddy", "Emily", "Da LAB", "Miu Lê",
    "Trịnh Thăng Bình", "Bảo Anh", "Bích Phương", "Văn Mai Hương", "Trung Quân",
    "Bùi Anh Tuấn", "Quân A.P", "Noo Phước Thịnh", "Mỹ Tâm", "Hà Anh Tuấn",
    "DanhKa", "Diệu Kiên", "Võ Lê Mi", "Bìn", "H2K", "Hồng Quân", "Dế Choắt",
    "Andree", "Andree Right Hand", "Khắc Việt", "Nguyễn Khoa", "Lăng LD",
    "Lou Hoàng", "OnlyC", "Pháo", "Quang Hùng MasterD", "Rhymastic", "Ricky Star",
    "RTee", "Tage", "Tez", "Thành Draw", "Wowy", "Phùng Đề Mạc", "Feng Timo",
    "Âm Khuyết Thi Thính", "Đẳng Thập Ma Quân", "Rhyder", "Chillies", "Ngọt",
    "Holy Thắng", "Emcee L", "CoolKid", "Dear Jane", "911",
    # Top International Artists
    "Charlie Puth", "Alan Walker", "Taylor Swift", "Billie Eilish", "Ed Sheeran",
    "Dua Lipa", "Bruno Mars", "The Weeknd", "Coldplay", "Imagine Dragons",
    "Avicii", "Marshmello", "Martin Garrix", "TheFatRat", "Vicetone", "Maroon 5",
    "Justin Bieber", "Shawn Mendes", "Camila Cabello", "Ariana Grande", "ZAYN",
    "Sia", "Kesha", "Katy Perry", "Rihanna", "Eminem", "Post Malone", "Drake"
]

for a in BUILTIN_ARTISTS:
    ARTIST_CANONICAL[a.lower().strip()] = a.strip()
    KNOWN_ARTISTS.add(a.lower().strip())

# Load tencasi.txt from local or parent directory
for p in [os.path.join(APP_DIR, "tencasi.txt"), os.path.join(MUSIC_DIR, "Muif", "tencasi.txt")]:
    if os.path.exists(p):
        try:
            with open(p, "r", encoding="utf-8") as f:
                for line in f:
                    name = line.strip()
                    if not name or name.startswith("#"):
                        continue
                    ARTIST_CANONICAL[name.lower()] = name
                    KNOWN_ARTISTS.add(name.lower())
                    parts = re.split(r"\s*(?:ft\.?|feat\.?|featuring|\bx\b|&|,)\s*", name, flags=re.IGNORECASE)
                    for pt in parts:
                        pt_clean = pt.strip()
                        if pt_clean and len(pt_clean) > 1:
                            if pt_clean.lower() not in ARTIST_CANONICAL:
                                ARTIST_CANONICAL[pt_clean.lower()] = pt_clean
                            KNOWN_ARTISTS.add(pt_clean.lower())
        except Exception:
            pass
        break

def remove_accents(text):
    if not text:
        return ""
    text = text.replace("Đ", "D").replace("đ", "d")
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))

def clean_uploader_name(uploader):
    if not uploader:
        return ""
    up = unicodedata.normalize('NFC', uploader.strip())
    up = re.sub(r'(?i)\s*(?:official\s*(?:channel|music|audio)?|vevo|topic|entertainment|channel|media|records|studio|music)\s*$', '', up)
    up = re.sub(r'(?i)^\s*(?:kênh|channel)\s*', '', up)
    up = re.sub(r'[\-_|•]$', '', up).strip()
    return up

def is_artist_string(text, uploader=""):
    if not text:
        return False
    t_clean = text.lower().strip(" .-_,:;|")
    if not t_clean:
        return False

    if t_clean in KNOWN_ARTISTS:
        return True

    c_up = clean_uploader_name(uploader).lower()
    if c_up and (c_up == t_clean or c_up in t_clean or t_clean in c_up):
        return True

    collab_parts = re.split(r"\s*(?:ft\.?|feat\.?|featuring|\bx\b|&|,)\s*", t_clean)
    if len(collab_parts) > 1:
        matched = sum(1 for p in collab_parts if p.strip() in KNOWN_ARTISTS or (c_up and p.strip() == c_up))
        if matched >= 1:
            return True

    if re.search(r'(?i)\b(?:ca\s*sĩ|singer|artist|st\s*:|sáng\s*tác)\b', t_clean):
        return True

    return False

def contains_song_keywords(text):
    return bool(re.search(r'(?i)\b(?:remix|lofi|acoustic|version|cover|mashup|karaoke|beat|instrumental|soundtrack|ost)\b', text))

def to_title_case_smart(s):
    if not s:
        return ""
    
    known_case_map = {
        'gen': 'GEN', 'z': 'Z', 'edm': 'EDM', 'mv': 'MV', 'dj': 'DJ',
        'm-tp': 'M-TP', 'mck': 'MCK', 'amee': 'AMEE', 'min': 'MIN',
        'gducky': 'GDucky', 'j97': 'J97', 'rpt': 'RPT', 'k-icm': 'K-ICM',
        'icm': 'ICM', '24kgoldn': '24kGoldn', 'b-ray': 'B-Ray', 'ost': 'OST',
        'hd': 'HD', 'hq': 'HQ', 'qnt': 'QNT', 't.r.i': 'T.R.I', 'grey d': 'GREY D'
    }
    lower_words = {'ft.', 'feat.', 'x', '&', 'vs', 'by'}

    words = s.split()
    res = []
    for w in words:
        clean_w = re.sub(r'^[^\wÀ-ỹ]+|[^\wÀ-ỹ]+$', '', w)
        w_lower = clean_w.lower()

        if w.lower() in lower_words:
            res.append(w.lower())
        elif w_lower in known_case_map:
            target_case = known_case_map[w_lower]
            res.append(w.replace(clean_w, target_case))
        else:
            m = re.match(r"^([^a-zA-ZÀ-ỹ0-9]*)([a-zA-ZÀ-ỹ0-9])(.*)$", w)
            if m:
                lead, first_c, rest = m.groups()
                res.append(lead + first_c.upper() + rest.lower())
            else:
                res.append(w)
    return " ".join(res)

def format_artist_casing(artist_str):
    if not artist_str:
        return ""
    a_lower = artist_str.lower().strip()
    if a_lower in ARTIST_CANONICAL:
        return ARTIST_CANONICAL[a_lower]

    res = artist_str
    for k in sorted(ARTIST_CANONICAL.keys(), key=lambda x: -len(x)):
        if len(k) <= 2:
            continue
        canon = ARTIST_CANONICAL[k]
        pattern = re.compile(rf"\b{re.escape(k)}\b", flags=re.IGNORECASE)
        res = pattern.sub(canon, res)
    return res

def clean_song_name(raw_title, uploader=""):
    """
    Cleans junk video title into 'Song Name' and 'Artist Name' with 100% precision.
    """
    if not raw_title:
        return "", ""

    # Normalize Unicode to NFC
    title = unicodedata.normalize('NFC', raw_title.strip())

    # 1. Clean YouTube tab notification badge e.g. (461), (1), (99+)
    title = re.sub(r"^\s*\(\s*\d+\+?\s*\)\s*", "", title)

    # 2. Clean track / playlist numbering prefix e.g. 461), 01., 01 -, #01, #1, Track 1:
    title = re.sub(r"^\s*#\s*\d{1,4}\b\s*", "", title)
    title = re.sub(r"^\s*\d{1,4}\s*[\)\:\.\-]\s*", "", title)
    title = re.sub(r"(?i)^\s*(?:track|bài|tập|vol|ep|part)\s*\.?\s*\d+\s*[\:\.\-]?\s*", "", title)

    # 3. Standardize M/V and M-V before separator conversion
    title = re.sub(r"(?i)\bM[/_-]V\b", "MV", title)

    # 4. Standardize decorative brackets like 【...】, 『...』
    title = re.sub(r"[【『〖〔《‹«]", "[", title)
    title = re.sub(r"[】』〗〕》›»]", "]", title)

    # 5. Remove junk emojis & decorative symbols
    title = re.sub(r"[♫♪🎧🔥✨💥🌟✔❤💖🌸👑🌹💯🍀⚡🔔💎🚀🌈🌻🎵🎶🔊🎤📻🎬📽►◄▶▼▲◆◇■□●○~～★☆]", "", title)

    # 6. Remove album and OST junk tags
    title = re.sub(r'(?i)\s*(?:từ|from|trích\s*từ)\s+album\s*["\'“”«»][^"\'“”«»]+["\'“”«»]', '', title)
    title = re.sub(r'(?i)\s*(?:từ|from|trích\s*từ)\s+album\s+.*$', '', title)
    title = re.sub(r'(?i)\s*(?:in|trích|từ)\s+album\b.*$', '', title)

    # 7. Standardize dashes and separators
    title = re.sub(r"[\u2010\u2012\u2013\u2014\u2212]", "-", title)
    title = re.sub(r"\s*[\|丨¦‖/]\s*", " - ", title)
    title = re.sub(r"\s*—\s*", " - ", title)
    title = re.sub(r"\s*–\s*", " - ", title)

    # 8. Remove all common YouTube junk patterns
    junk_patterns = [
        # Official / Video / Audio / Lyrics tags
        r"[\(\[\{]\s*(?:official\s*(?:music\s*)?video|official\s*mv|official\s*audio|official\s*lyrics?\s*video|official\s*visualizer|mv\s*official|official\s*video|music\s*video|\bmv\b|\baudio\b|lyrics?\s*video|lyric\s*video|\blyrics?\b|\blời\s*bài\s*hát\b|visualizer|4k(?:\s*60fps)?|1080p|\bhd\b|full\s*hd|\bhq\b|high\s*quality|audio\s*hq|full\s*(?:song|version|audio))\s*[\)\]\}]",
        r"(?i)\b(official\s*(?:music\s*)?video|official\s*lyrics?\s*video|official\s*audio|mv\s*official|official\s*visualizer|official\s*video)\b",
        # TikTok & Viral clutter
        r"[\(\[\{]\s*(?:bản\s*(?:hot|chuẩn|cực\s*cháy|trend)?\s*tiktok|hot\s*tiktok|trend\s*tiktok|tóp\s*tóp|viral\s*tiktok|nhạc\s*remix\s*hot\s*nhất\s*\d*|nhạc\s*cưới\s*remix\s*hay\s*nhất\s*\d*|nhạc\s*cực\s*bốc\s*\d*|bản\s*remix\s*(?:nghe\s*là\s*phê|nghe\s*là\s*ghiền|cực\s*căng|cực\s*cháy|gây\s*nghiện))\s*[\)\]\}]",
        r"(?i)\b(bản\s*(?:hot|chuẩn|trend)?\s*tiktok|hot\s*tiktok|trend\s*tiktok|bản\s*remix\s*nghe\s*là\s*phê|nghe\s*là\s*ghiền|bass\s*cực\s*căng|cực\s*cháy|nhạc\s*cực\s*bốc\s*\d*)\b",
        # Prod. by tags
        r"[\(\[\{]\s*Prod\.\s*(?:by)?\s*[^\]\)\}]*[\)\]\}]",
        r"(?i)\bProd\.\s*(?:by)?\s*[a-zA-Z0-9_\s]+(?=[\-\|\)\]\}]|$)",
        # Empty brackets
        r"[\(\[\{]\s*[\)\]\}]",
    ]
    for p in junk_patterns:
        title = re.sub(p, "", title, flags=re.IGNORECASE)

    # 9. Clean secondary English translation in parentheses if main Vietnamese title exists
    def clean_paren_translation(m):
        content = m.group(1).strip()
        if re.search(r'(?i)\b(remix|lofi|acoustic|version|feat|ft\.|live|cover|mashup|beat|karaoke)\b', content):
            return m.group(0)
        if len(content.split()) <= 2 and len(content) <= 6:
            return m.group(0)
        if re.match(r"^[A-Za-z\s']{6,45}$", content):
            return ""
        return m.group(0)

    title = re.sub(r"\s*\(([^\)]+)\)", clean_paren_translation, title)

    # Clean multiple spaces and dangling punctuation
    title = re.sub(r"\s+", " ", title).strip(" -_,:;|")

    # 10. Extract featured artist from brackets
    extracted_feat = ""
    feat_match = re.search(r"[\(\[]\s*(?:ft\.?|feat\.?|featuring)\s*([^\)\]]+)[\)\]]", title, flags=re.IGNORECASE)
    if feat_match:
        extracted_feat = feat_match.group(1).strip()
        title = title[:feat_match.start()] + title[feat_match.end():]
        title = re.sub(r"\s+", " ", title).strip(" -_,:;|")

    # 11. Split into parts by " - "
    song_name = title
    artist_name = clean_uploader_name(uploader) or ""

    if " - " in title:
        raw_parts = [p.strip(" -_,:;|") for p in title.split(" - ") if p.strip(" -_,:;|")]
        valid_parts = []
        for p in raw_parts:
            if re.match(r"(?i)^(?:official|audio|lyrics?|video|mv|visualizer|m/v|hd|4k)$", p):
                continue
            valid_parts.append(p)

        if len(valid_parts) == 1:
            song_name = valid_parts[0]
        elif len(valid_parts) >= 2:
            p0 = valid_parts[0]
            p1 = valid_parts[1]

            # Check if inline ft. is inside p1
            if not extracted_feat:
                inline_feat_m = re.search(r"\s+(?:ft\.?|feat\.?|featuring)\s+(.+)$", p1, flags=re.IGNORECASE)
                if inline_feat_m:
                    extracted_feat = inline_feat_m.group(1).strip()
                    p1 = p1[:inline_feat_m.start()].strip()

            p0_is_artist = is_artist_string(p0, uploader)
            p1_is_artist = is_artist_string(p1, uploader)
            p0_has_song_kw = contains_song_keywords(p0)
            p1_has_song_kw = contains_song_keywords(p1)

            if p0_is_artist and not p1_is_artist:
                # Format: Artist - Song
                artist_name = p0
                song_name = p1
            elif p1_is_artist and not p0_is_artist:
                # Format: Song - Artist
                artist_name = p1
                song_name = p0
            elif p0_has_song_kw and not p1_has_song_kw:
                song_name = p0
                artist_name = p1
            elif p1_has_song_kw and not p0_has_song_kw:
                artist_name = p0
                song_name = p1
            else:
                song_name = p0
                artist_name = p1

            if len(valid_parts) > 2:
                for extra in valid_parts[2:]:
                    if contains_song_keywords(extra):
                        song_name += f" ({extra})"

    # 12. Attach extracted featured artist to artist_name
    if extracted_feat:
        if artist_name and extracted_feat.lower() not in artist_name.lower():
            artist_name = f"{artist_name} ft. {extracted_feat}"
        elif not artist_name:
            artist_name = extracted_feat

    # Clean prefixes and edge punctuation
    def clean_prefix(s):
        s = re.sub(r"^\s*\(\s*\d+\+?\s*\)\s*", "", s)
        s = re.sub(r"^\s*#\s*\d{1,4}\b\s*", "", s)
        s = re.sub(r"^\s*\d{1,4}\s*[\)\:\.\-]\s*", "", s)
        s = re.sub(r"^\s*\d{1,3}\s*[\-\_]\s+", "", s)
        return s.strip(" -_,:;|")

    song_name = clean_prefix(song_name)
    artist_name = clean_prefix(artist_name)

    # Smart title casing
    song_name = to_title_case_smart(song_name)
    artist_name = to_title_case_smart(artist_name)

    # Format artist canonical casing (e.g. Sơn Tùng M-TP, BigDaddy, JustaTee, B-Ray)
    artist_name = format_artist_casing(artist_name)

    # Chuyển đổi toàn bộ sang tiếng Việt không dấu
    song_name = remove_accents(song_name)
    artist_name = remove_accents(artist_name)

    # Sanitize invalid Windows chars
    for ch in r'\/:*?"<>|':
        song_name = song_name.replace(ch, "")
        artist_name = artist_name.replace(ch, "")

    return song_name.strip(), artist_name.strip()

def search_tracks(query, limit=5):
    query = query.strip()
    is_url = query.startswith(('http://', 'https://'))
    
    if is_url:
        clean_url = clean_youtube_url(query)
        search_target = clean_url
        extract_flat = False
    else:
        clean_url = query
        search_target = f"ytsearch{limit}:{query}"
        extract_flat = True

    ydl_opts = {
        'quiet': True,
        'extract_flat': extract_flat,
        'skip_download': True,
        'no_warnings': True,
        'noplaylist': True,
    }
    
    results = []
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(search_target, download=False)
            if is_url:
                entries = [info] if info else []
            else:
                entries = info.get('entries') if 'entries' in info else [info]

            for e in entries:
                if not e: continue
                raw_title = e.get('title', '')
                uploader = e.get('uploader') or e.get('channel') or ''
                duration = e.get('duration') or 0
                mins, secs = divmod(int(duration), 60)
                dur_str = f"{mins}:{secs:02d}" if duration else "--:--"
                
                clean_s, clean_a = clean_song_name(raw_title, uploader)
                url = e.get('webpage_url') or e.get('url') or f"https://www.youtube.com/watch?v={e.get('id')}"
                url = clean_youtube_url(url)

                thumbnail = e.get('thumbnail')
                if not thumbnail and e.get('thumbnails'):
                    thumbnail = e.get('thumbnails')[-1].get('url')

                results.append({
                    "id": e.get('id'),
                    "raw_title": raw_title,
                    "clean_song": clean_s,
                    "clean_artist": clean_a,
                    "clean_filename": f"{clean_a} - {clean_s}.mp3" if clean_a else f"{clean_s}.mp3",
                    "url": url,
                    "duration": dur_str,
                    "uploader": uploader,
                    "thumbnail": thumbnail or ""
                })
                # If direct single URL, break after 1 entry
                if is_url:
                    break
        except Exception as err:
            print("Search error:", err)
    return results

def download_and_process(video_url, target_folder, custom_title, custom_artist, thumbnail_url=None):
    video_url = clean_youtube_url(video_url)
    folder_path = os.path.join(MUSIC_DIR, target_folder)
    os.makedirs(folder_path, exist_ok=True)

    custom_title = remove_accents(custom_title)
    custom_artist = remove_accents(custom_artist)
    filename_base = f"{custom_artist} - {custom_title}".strip(" -_") if custom_artist else custom_title.strip(" -_")
    filename_base = remove_accents(filename_base)
    for ch in r'\/:*?"<>|':
        filename_base = filename_base.replace(ch, "")
    
    final_mp3_path = os.path.join(folder_path, f"{filename_base}.mp3")
    temp_prefix = f"temp_{int(os.getpid())}"
    temp_template = os.path.join(folder_path, f"{temp_prefix}.%(ext)s")

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': temp_template,
        'noplaylist': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '128',
        }],
        'writethumbnail': True,
        'quiet': False,
        'no_warnings': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])

    temp_mp3 = os.path.join(folder_path, f"{temp_prefix}.mp3")
    if not os.path.exists(temp_mp3):
        for f in os.listdir(folder_path):
            if f.startswith(temp_prefix) and f.endswith(".mp3"):
                temp_mp3 = os.path.join(folder_path, f)
                break

    if not os.path.exists(temp_mp3):
        raise FileNotFoundError("Không tìm thấy file MP3 sau khi tải.")

    # 1. Update ID3 tags
    try:
        try:
            audio = EasyID3(temp_mp3)
        except ID3NoHeaderError:
            audio = mutagen.File(temp_mp3, easy=True)
            audio.add_tags()
        
        audio["title"] = custom_title
        if custom_artist:
            audio["artist"] = custom_artist
        audio.save()
    except Exception as e:
        print("ID3 tag error:", e)

    # 2. Embed thumbnail
    temp_thumb = None
    for ext in ['.jpg', '.jpeg', '.png', '.webp']:
        cand = os.path.join(folder_path, f"{temp_prefix}{ext}")
        if os.path.exists(cand):
            temp_thumb = cand
            break

    if temp_thumb:
        try:
            raw_id3 = ID3(temp_mp3)
            with open(temp_thumb, 'rb') as f:
                img_data = f.read()
            mime = "image/jpeg" if temp_thumb.endswith(('.jpg', '.jpeg')) else "image/png"
            raw_id3.add(APIC(
                encoding=3,
                mime=mime,
                type=3,
                desc='Cover',
                data=img_data
            ))
            raw_id3.save()
            os.remove(temp_thumb)
        except Exception as e:
            print("Thumbnail embed error:", e)

    # 3. Final rename
    if os.path.exists(final_mp3_path):
        os.remove(final_mp3_path)
    os.rename(temp_mp3, final_mp3_path)

    return {
        "success": True,
        "filename": os.path.basename(final_mp3_path),
        "folder": target_folder,
        "path": final_mp3_path,
        "bitrate": "128kbps"
    }

class MusicAppHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.join(APP_DIR, "web"), **kwargs)

    def _send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')

    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/folders":
            all_folders = [d for d in os.listdir(MUSIC_DIR) 
                           if os.path.isdir(os.path.join(MUSIC_DIR, d)) and not d.startswith('.')]
            if "downloadmp3" in all_folders:
                all_folders.remove("downloadmp3")
                folders = ["downloadmp3"] + sorted(all_folders)
            else:
                folders = sorted(all_folders)

            self.send_response(200)
            self._send_cors_headers()
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({"folders": folders}).encode('utf-8'))
        elif parsed.path == "/api/status":
            self.send_response(200)
            self._send_cors_headers()
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "running", "version": "1.0"}).encode('utf-8'))
        else:
            super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        content_len = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_len).decode('utf-8')
        data = json.loads(body) if body else {}

        if parsed.path == "/api/search":
            query = data.get("query", "").strip()
            if not query:
                self.send_error(400, "Query cannot be empty")
                return
            results = search_tracks(query)
            self.send_response(200)
            self._send_cors_headers()
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({"results": results}).encode('utf-8'))

        elif parsed.path == "/api/clean_title":
            raw_title = data.get("title", "")
            uploader = data.get("uploader", "")
            clean_s, clean_a = clean_song_name(raw_title, uploader)
            self.send_response(200)
            self._send_cors_headers()
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({
                "song": clean_s,
                "artist": clean_a,
                "filename": f"{clean_a} - {clean_s}.mp3" if clean_a else f"{clean_s}.mp3"
            }).encode('utf-8'))

        elif parsed.path == "/api/download":
            url = data.get("url")
            folder = data.get("folder") or "downloadmp3"
            title = data.get("title") or "Unknown"
            artist = data.get("artist") or ""
            thumb = data.get("thumbnail")

            try:
                res = download_and_process(url, folder, title, artist, thumb)
                self.send_response(200)
                self._send_cors_headers()
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps(res).encode('utf-8'))
            except Exception as err:
                self.send_response(500)
                self._send_cors_headers()
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(err)}).encode('utf-8'))

def run_server(port=8899):
    server_address = ('127.0.0.1', port)
    httpd = HTTPServer(server_address, MusicAppHandler)
    url = f"http://127.0.0.1:{port}"
    print(f"\n🎵 Muif Music Downloader (128kbps) Server đang chạy tại: {url}")
    print("👉 Mở trình duyệt để sử dụng. Nhấn Ctrl+C để dừng server.\n")
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nĐã tắt server.")

if __name__ == "__main__":
    port = 8899
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
    run_server(port)
