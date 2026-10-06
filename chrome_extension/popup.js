const SERVER_URL = 'http://127.0.0.1:8899';

let currentTab = null;
let currentVideoId = null;

function cleanYouTubeUrl(url) {
  if (!url) return { cleanUrl: '', videoId: '' };
  url = url.trim();
  try {
    if (url.includes('youtube.com') || url.includes('youtu.be')) {
      const u = new URL(url);
      let videoId = '';
      if (u.hostname.includes('youtu.be')) {
        videoId = u.pathname.replace(/^\//, '');
      } else if (u.pathname.includes('/shorts/')) {
        videoId = u.pathname.split('/shorts/')[1].split('/')[0];
      } else {
        videoId = u.searchParams.get('v') || '';
      }
      if (videoId) {
        return {
          cleanUrl: `https://www.youtube.com/watch?v=${videoId}`,
          videoId: videoId
        };
      }
    }
  } catch (e) {}
  return { cleanUrl: url, videoId: '' };
}

async function checkServer() {
  const dot = document.getElementById('statusDot');
  const txt = document.getElementById('statusText');
  const alertEl = document.getElementById('serverAlert');
  const btn = document.getElementById('downloadBtn');

  try {
    const res = await fetch(`${SERVER_URL}/api/status`);
    if (res.ok) {
      dot.className = 'status-dot online';
      txt.textContent = 'Server Online';
      alertEl.style.display = 'none';
      return true;
    }
  } catch (e) {}

  dot.className = 'status-dot';
  txt.textContent = 'Server Offline';
  alertEl.style.display = 'block';
  btn.disabled = true;
  return false;
}

async function loadFolders() {
  try {
    const res = await fetch(`${SERVER_URL}/api/folders`);
    const data = await res.json();
    const sel = document.getElementById('folderSelect');
    sel.innerHTML = '';
    data.folders.forEach(f => {
      const opt = document.createElement('option');
      opt.value = f;
      opt.textContent = (f === 'downloadmp3') ? '📁 downloadmp3 (Mặc định)' : `📁 ${f}`;
      if (f === 'downloadmp3') opt.selected = true;
      sel.appendChild(opt);
    });
    updateFilePreview();
  } catch (e) {
    console.error("Lỗi lấy folders:", e);
  }
}

function removeAccents(str) {
  if (!str) return '';
  return str
    .replace(/Đ/g, 'D')
    .replace(/đ/g, 'd')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '');
}

function updateFilePreview() {
  const song = removeAccents(document.getElementById('songInput').value.trim()) || 'Ten Bai Hat';
  const artist = removeAccents(document.getElementById('artistInput').value.trim());
  const folder = document.getElementById('folderSelect').value || 'downloadmp3';
  const fname = artist ? `${artist} - ${song}.mp3` : `${song}.mp3`;
  document.getElementById('filePreview').textContent = `[${folder}] / ${fname}`;
}

document.getElementById('songInput').addEventListener('input', updateFilePreview);
document.getElementById('artistInput').addEventListener('input', updateFilePreview);
document.getElementById('folderSelect').addEventListener('change', updateFilePreview);

async function initTabInfo() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  currentTab = tab;

  if (!tab || !tab.url || (!tab.url.includes('youtube.com/watch') && !tab.url.includes('youtu.be/'))) {
    document.getElementById('videoTitleOrig').textContent = '⚠️ Không phải video YouTube!';
    document.getElementById('toastMsg').textContent = 'Hãy mở một bài hát trên YouTube để tải.';
    document.getElementById('downloadBtn').disabled = true;
    return;
  }

  const { cleanUrl, videoId } = cleanYouTubeUrl(tab.url);
  currentTab.cleanUrl = cleanUrl;
  currentVideoId = videoId;

  // Set thumbnail
  if (videoId) {
    document.getElementById('videoThumb').src = `https://i.ytimg.com/vi/${videoId}/mqdefault.jpg`;
  }

  // Lấy tiêu đề và uploader trực tiếp từ DOM trang YouTube
  let rawTitle = '';
  let uploader = '';

  try {
    const response = await chrome.tabs.sendMessage(tab.id, { action: 'getVideoDetails' });
    if (response && response.title) {
      rawTitle = response.title.trim();
      uploader = response.uploader ? response.uploader.trim() : '';
    }
  } catch (e) {
    // Fallback nếu content script chưa phản hồi
  }

  if (!rawTitle) {
    rawTitle = tab.title || '';
    rawTitle = rawTitle.replace(/\s*-\s*YouTube$/i, '').trim();
    rawTitle = rawTitle.replace(/^\s*\(\s*\d+\+?\s*\)\s*/, '').trim();
  } else {
    rawTitle = rawTitle.replace(/^\s*\(\s*\d+\+?\s*\)\s*/, '').trim();
  }

  document.getElementById('videoTitleOrig').textContent = rawTitle;

  // Ask backend to clean title
  try {
    const res = await fetch(`${SERVER_URL}/api/clean_title`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: rawTitle, uploader: uploader })
    });
    const data = await res.json();
    document.getElementById('songInput').value = removeAccents(data.song || rawTitle);
    document.getElementById('artistInput').value = removeAccents(data.artist || uploader || '');
  } catch (e) {
    document.getElementById('songInput').value = removeAccents(rawTitle);
  }
  updateFilePreview();
}

document.getElementById('downloadBtn').addEventListener('click', async () => {
  if (!currentTab || !currentTab.cleanUrl) return;

  const btn = document.getElementById('downloadBtn');
  const btnText = document.getElementById('btnText');
  const btnSvg = document.getElementById('btnSvg');
  const toast = document.getElementById('toastMsg');

  const song = removeAccents(document.getElementById('songInput').value.trim());
  const artist = removeAccents(document.getElementById('artistInput').value.trim());
  const folder = document.getElementById('folderSelect').value;

  btn.disabled = true;
  btnSvg.style.display = 'none';
  btnText.innerHTML = '<span class="spinner"></span> Đang tải & nén 128k...';
  toast.className = 'toast-msg';
  toast.textContent = '⏳ Đang trích xuất audio chất lượng cao...';

  try {
    const res = await fetch(`${SERVER_URL}/api/download`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        url: currentTab.cleanUrl,
        folder: folder,
        title: song,
        artist: artist
      })
    });
    const data = await res.json();

    if (data.error) {
      toast.className = 'toast-msg error';
      toast.textContent = '❌ Lỗi: ' + data.error;
      btn.disabled = false;
      btnSvg.style.display = 'inline-block';
      btnText.textContent = 'Thử lại';
    } else {
      toast.className = 'toast-msg success';
      toast.textContent = `🎉 Hoàn thành: ${data.filename}`;
      btnSvg.style.display = 'none';
      btnText.textContent = '✅ Đã tải về máy!';
      setTimeout(() => {
        btn.disabled = false;
        btnSvg.style.display = 'inline-block';
        btnText.textContent = 'Tải lại bài này';
      }, 3500);
    }
  } catch (err) {
    toast.className = 'toast-msg error';
    toast.textContent = '❌ Không thể kết nối với server: ' + err;
    btn.disabled = false;
    btnSvg.style.display = 'inline-block';
    btnText.textContent = 'Thử lại';
  }
});

// Run
(async () => {
  const isUp = await checkServer();
  if (isUp) {
    await loadFolders();
    await initTabInfo();
  }
})();
