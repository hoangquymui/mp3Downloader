// Muif Downloader Content Script - Injects a download button directly onto YouTube video page
const SERVER_URL = 'http://127.0.0.1:8899';

function cleanYouTubeUrl(url) {
  if (!url) return '';
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
        return `https://www.youtube.com/watch?v=${videoId}`;
      }
    }
  } catch (e) {}
  return url;
}

function showYouTubeToast(message, isError = false) {
  let toast = document.getElementById('muif-floating-toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'muif-floating-toast';
    toast.style.cssText = `
      position: fixed;
      bottom: 30px;
      right: 30px;
      z-index: 999999;
      background: #111827;
      color: #fff;
      border: 1px solid #1db954;
      padding: 12px 18px;
      border-radius: 12px;
      font-size: 14px;
      font-weight: 600;
      box-shadow: 0 10px 25px rgba(0,0,0,0.6);
      display: flex;
      align-items: center;
      gap: 10px;
      transition: all 0.3s ease;
      transform: translateY(20px);
      opacity: 0;
    `;
    document.body.appendChild(toast);
  }

  toast.style.borderColor = isError ? '#ef4444' : '#1db954';
  toast.innerHTML = message;
  toast.style.transform = 'translateY(0)';
  toast.style.opacity = '1';

  setTimeout(() => {
    toast.style.transform = 'translateY(20px)';
    toast.style.opacity = '0';
  }, 4000);
}

function removeAccents(str) {
  if (!str) return '';
  return str
    .replace(/Đ/g, 'D')
    .replace(/đ/g, 'd')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '');
}

function injectDownloadButton() {
  if (!window.location.pathname.startsWith('/watch')) return;
  if (document.getElementById('muif-yt-download-btn')) return;

  const actionsContainer = document.querySelector('#top-level-buttons-computed') || 
                           document.querySelector('#actions-inner #top-level-buttons-computed') ||
                           document.querySelector('ytd-menu-renderer #top-level-buttons-computed');

  if (!actionsContainer) return;

  const btn = document.createElement('button');
  btn.id = 'muif-yt-download-btn';
  btn.innerHTML = `
    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z"/>
    </svg>
    <span>Tải MP3 128k</span>
  `;

  btn.style.cssText = `
    display: inline-flex;
    align-items: center;
    gap: 7px;
    background: linear-gradient(135deg, #1db954 0%, #10b981 100%);
    color: #0c0f17;
    font-weight: 700;
    font-size: 13px;
    padding: 0 16px;
    height: 36px;
    border-radius: 18px;
    border: none;
    cursor: pointer;
    margin-left: 10px;
    box-shadow: 0 2px 10px rgba(29, 185, 84, 0.35);
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    z-index: 10;
  `;

  btn.addEventListener('mouseenter', () => {
    btn.style.transform = 'translateY(-1px) scale(1.02)';
    btn.style.boxShadow = '0 4px 16px rgba(29, 185, 84, 0.55)';
  });
  btn.addEventListener('mouseleave', () => {
    btn.style.transform = 'none';
    btn.style.boxShadow = '0 2px 10px rgba(29, 185, 84, 0.35)';
  });

  btn.addEventListener('click', async () => {
    const videoUrl = cleanYouTubeUrl(window.location.href);
    const titleEl = document.querySelector('h1.ytd-watch-metadata yt-formatted-string') || 
                    document.querySelector('h1.ytd-watch-metadata') || 
                    document.querySelector('h1 yt-formatted-string');
    const uploaderEl = document.querySelector('#channel-name #text') || 
                       document.querySelector('ytd-channel-name yt-formatted-string') ||
                       document.querySelector('#owner #channel-name');

    let rawTitle = titleEl ? titleEl.textContent.trim() : document.title.replace(/\s*-\s*YouTube$/i, '').trim();
    rawTitle = rawTitle.replace(/^\s*\(\s*\d+\+?\s*\)\s*/, '').trim();
    const uploader = uploaderEl ? uploaderEl.textContent.trim() : '';

    btn.disabled = true;
    btn.style.opacity = '0.7';
    btn.innerHTML = `
      <span style="display:inline-block;animation:spin 0.8s linear infinite;">⏳</span>
      <span>Đang tải & nén 128k...</span>
    `;

    try {
      // 1. Get clean title
      let song = rawTitle;
      let artist = uploader;
      try {
        const cleanRes = await fetch(`${SERVER_URL}/api/clean_title`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ title: rawTitle, uploader: uploader })
        });
        const cleanData = await cleanRes.json();
        song = removeAccents(cleanData.song || rawTitle);
        artist = removeAccents(cleanData.artist || uploader || '');
      } catch (e) {}

      // 2. Trigger download
      const res = await fetch(`${SERVER_URL}/api/download`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url: videoUrl,
          folder: 'downloadmp3',
          title: song,
          artist: artist
        })
      });
      const data = await res.json();

      if (data.error) {
        showYouTubeToast("❌ Lỗi: " + data.error, true);
        btn.innerHTML = `<span>❌ Lỗi</span>`;
      } else {
        btn.style.background = '#10b981';
        btn.style.color = '#fff';
        btn.innerHTML = `<span>✅ Đã lưu MP3!</span>`;
        showYouTubeToast(`🎉 <b>Đã tải thành công:</b> ${data.filename}<br><small style="color:#94a3b8">Lưu trong: folder downloadmp3</small>`);
      }
    } catch (err) {
      showYouTubeToast("⚠️ Chưa bật server! Hãy mở file <b>TaiNhac_GiaoDienWeb.bat</b> trên máy tính.", true);
      btn.innerHTML = `<span>⚠️ Chưa bật server</span>`;
    } finally {
      setTimeout(() => {
        btn.disabled = false;
        btn.style.opacity = '1';
        btn.style.background = 'linear-gradient(135deg, #1db954 0%, #10b981 100%)';
        btn.style.color = '#0c0f17';
        btn.innerHTML = `
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z"/>
          </svg>
          <span>Tải MP3 128k</span>
        `;
      }, 4000);
    }
  });

  actionsContainer.appendChild(btn);
}

const observer = new MutationObserver(() => {
  injectDownloadButton();
});

observer.observe(document.body, { childList: true, subtree: true });
injectDownloadButton();

// Listen for messages from popup.js to provide accurate DOM video info
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'getVideoDetails') {
    const titleEl = document.querySelector('h1.ytd-watch-metadata yt-formatted-string') || 
                    document.querySelector('h1.ytd-watch-metadata') || 
                    document.querySelector('h1 yt-formatted-string');
    const uploaderEl = document.querySelector('#channel-name #text') || 
                       document.querySelector('ytd-channel-name yt-formatted-string') ||
                       document.querySelector('#owner #channel-name');
    
    let domTitle = titleEl ? titleEl.textContent.trim() : '';
    let domUploader = uploaderEl ? uploaderEl.textContent.trim() : '';
    sendResponse({ title: domTitle, uploader: domUploader });
  }
  return true;
});
