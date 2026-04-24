// ── API 基础封装 ──
const API = {
  async request(url, options = {}) {
    const res = await fetch(url, {
      headers: { 'Content-Type': 'application/json' },
      credentials: 'same-origin',
      ...options,
    });
    return res.json();
  },
  get:    (url)        => API.request(url),
  post:   (url, data)  => API.request(url, { method: 'POST',   body: JSON.stringify(data) }),
  put:    (url, data)  => API.request(url, { method: 'PUT',    body: JSON.stringify(data) }),
  delete: (url)        => API.request(url, { method: 'DELETE' }),
};

// ── Toast 提示 ──
function toast(msg, type = 'success', duration = 2800) {
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.textContent = msg;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), duration);
}

// ── 星级评分组件 ──
function initStars(container, onRate) {
  const stars = container.querySelectorAll('.star');
  let current = 0;
  stars.forEach((s, i) => {
    s.addEventListener('mouseenter', () => {
      stars.forEach((x, j) => x.classList.toggle('active', j <= i));
    });
    s.addEventListener('mouseleave', () => {
      stars.forEach((x, j) => x.classList.toggle('active', j < current));
    });
    s.addEventListener('click', () => {
      current = i + 1;
      stars.forEach((x, j) => x.classList.toggle('active', j < current));
      onRate(current);
    });
  });
}

// ── 分页渲染 ──
function renderPagination(container, currentPage, totalPages, onPageChange) {
  container.innerHTML = '';
  if (totalPages <= 1) return;
  const prev = document.createElement('div');
  prev.className = 'page-btn';
  prev.textContent = '‹';
  prev.onclick = () => currentPage > 1 && onPageChange(currentPage - 1);
  container.appendChild(prev);

  const start = Math.max(1, currentPage - 2);
  const end   = Math.min(totalPages, currentPage + 2);
  for (let i = start; i <= end; i++) {
    const btn = document.createElement('div');
    btn.className = `page-btn${i === currentPage ? ' active' : ''}`;
    btn.textContent = i;
    btn.onclick = () => i !== currentPage && onPageChange(i);
    container.appendChild(btn);
  }

  const next = document.createElement('div');
  next.className = 'page-btn';
  next.textContent = '›';
  next.onclick = () => currentPage < totalPages && onPageChange(currentPage + 1);
  container.appendChild(next);
}

// ── 电影卡片 HTML ──
function movieCardHTML(m) {
  const poster = m.poster_url && !m.poster_url.startsWith('/static')
    ? `<img src="${m.poster_url}" alt="${m.title}"
            style="width:100%;height:100%;object-fit:cover;display:block"
            onerror="this.style.display='none'">`
    : '<span style="font-size:48px">🎬</span>';

  return `
    <div class="movie-card fade-in" onclick="location.href='/movie/${m.movie_id}'">
      <div class="movie-poster">${poster}</div>
      <div class="movie-info">
        <div class="movie-title">${m.title}</div>
        <div class="movie-meta">
          <span class="movie-rating">★ ${m.avg_rating || '暂无'}</span>
          <span style="margin-left:8px;color:var(--text2)">${m.year || ''}</span>
        </div>
        <div style="margin-top:6px">
          ${(m.genres || '').split('|').slice(0,2).map(g =>
            `<span class="badge badge-genre">${g}</span>`
          ).join(' ')}
        </div>
      </div>
    </div>`;
}

// ── 登出 ──
async function logout() {
  await API.post('/api/user/logout');
  location.href = '/login';
}

// ── 检查登录状态 ──
async function checkLogin() {
  const res = await API.get('/api/user/profile');
  if (res.code !== 200) {
    location.href = '/login';
    return null;
  }
  return res.data;
}