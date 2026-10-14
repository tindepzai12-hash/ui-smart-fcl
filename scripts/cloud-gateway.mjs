import http from 'node:http';
import { createHash, createHmac, randomBytes, timingSafeEqual } from 'node:crypto';

const COOKIE = '__Host-ui-smart';
const digest = value => createHash('sha256').update(value).digest();
const equal = (a, b) => timingSafeEqual(digest(a), digest(b));
const loginPage = (message = '') => `<!doctype html><html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Đăng nhập · U&I SMART</title><style>
*{box-sizing:border-box}body{margin:0;min-height:100vh;display:grid;place-items:center;background:#f1f5f9;color:#172b46;font:16px/1.6 system-ui,sans-serif;padding:24px}main{width:min(100%,440px);background:white;border:1px solid #dbe3ed;border-radius:20px;padding:36px;box-shadow:0 16px 60px #142e4810}small{color:#64748b}h1{font-size:28px;margin:6px 0}p{color:#52647a}label{display:block;font-weight:600;margin-top:24px}input,button{width:100%;padding:13px 15px;font:inherit;border-radius:10px;margin-top:8px}input{border:1px solid #a4b4c8}button{border:0;background:#174c8d;color:white;cursor:pointer;font-weight:600}input:focus,button:focus-visible{outline:3px solid #8dbbff;outline-offset:2px}.error{color:#b42318}footer{margin-top:24px;border-top:1px solid #e2e8f0;padding-top:18px;font-size:13px;color:#64748b}
</style><script src="/__cloud/login.js" defer></script><main><small>FCL DOCUMENT WORKBENCH</small><h1>U&I SMART</h1><p>Đăng nhập để làm việc với hồ sơ chứng từ.</p><p id="login-error" role="alert" class="error">${message}</p><form method="post" action="/__cloud/login"><label for="password">Mật khẩu truy cập</label><input id="password" name="password" type="password" autocomplete="current-password" required autofocus maxlength="256"><button>Đăng nhập</button></form><footer>Bản demo Render Free. Dữ liệu tải lên có thể mất khi máy chủ ngủ hoặc khởi động lại. Hãy tải bản sao lưu trước khi rời phiên.</footer></main></html>`;

const loginScript = `document.querySelector('form').addEventListener('submit',async event=>{
  event.preventDefault();const form=event.currentTarget,button=form.querySelector('button'),error=document.querySelector('#login-error');
  button.disabled=true;button.textContent='Đang đăng nhập…';error.textContent='';
  try{const response=await fetch('/__cloud/login',{method:'POST',body:new URLSearchParams(new FormData(form)),credentials:'same-origin'});
    if(response.ok&&response.redirected){window.location.replace('/');return;}
    error.textContent=response.status===429?'Thử sai quá nhiều lần. Hãy chờ 10 phút rồi thử lại.':'Mật khẩu chưa đúng. Hãy kiểm tra lại.';
  }catch{error.textContent='Chưa kết nối được máy chủ. Vui lòng thử lại.';}
  button.disabled=false;button.textContent='Đăng nhập';
});`;

export function createGateway({ password, secret, backendPort, secure = true, now = Date.now }) {
  if (!password || password.length < 16 || !secret || secret.length < 32) {
    throw new Error('Set a strong UI_SMART_PASSWORD (16+ characters) and UI_SMART_SESSION_SECRET (32+ characters).');
  }
  const cookieName = secure ? COOKIE : 'ui-smart-dev';
  const failures = new Map();
  const sign = payload => createHmac('sha256', secret).update(payload + digest(password).toString('hex')).digest('base64url');
  const cookie = (token, age) => `${cookieName}=${token}; Path=/; HttpOnly; SameSite=Strict; Max-Age=${age}${secure ? '; Secure' : ''}`;
  function validSession(req) {
    const token = (req.headers.cookie || '').split(';').map(v => v.trim()).find(v => v.startsWith(cookieName + '='))?.slice(cookieName.length + 1);
    if (!token || token.length > 400) return false;
    const [payload, signature, extra] = token.split('.');
    if (!payload || !signature || extra || !equal(sign(payload), signature)) return false;
    try {
      const { exp } = JSON.parse(Buffer.from(payload, 'base64url').toString());
      return Number.isFinite(exp) && exp > now() && exp <= now() + 8 * 60 * 60 * 1000;
    } catch { return false; }
  }
  function send(res, status, body, html = false, headers = {}) {
    res.writeHead(status, {
      'Content-Type': html ? 'text/html; charset=utf-8' : 'application/json; charset=utf-8',
      'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff',
      'Referrer-Policy': 'no-referrer', 'X-Frame-Options': 'DENY',
      'Content-Security-Policy': "default-src 'none'; script-src 'self'; connect-src 'self'; style-src 'unsafe-inline'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'",
      ...(secure ? { 'Strict-Transport-Security': 'max-age=31536000' } : {}), ...headers,
    });
    res.end(html ? body : JSON.stringify(body));
  }
  const originAllowed = req => {
    if (req.headers['sec-fetch-site'] === 'cross-site') return false;
    if (!req.headers.origin) return true;
    try {
      const origin = new URL(req.headers.origin);
      return origin.host === req.headers.host && origin.protocol === (secure ? 'https:' : 'http:');
    } catch { return false; }
  };
  return http.createServer(async (req, res) => {
    const pathname = (req.url || '/').split('?')[0];
    if (pathname === '/healthz' && req.method === 'GET') {
      try {
        const r = await fetch(`http://127.0.0.1:${backendPort}/api/health`, { signal: AbortSignal.timeout(10000) });
        const body = await r.json();
        return send(res, r.ok && body.ok ? 200 : 503, { ok: Boolean(r.ok && body.ok) });
      } catch { return send(res, 503, { ok: false }); }
    }
    if (pathname === '/robots.txt' && req.method === 'GET') {
      res.writeHead(200, { 'Content-Type': 'text/plain', 'Cache-Control': 'no-store' });
      return res.end('User-agent: *\nDisallow: /\n');
    }
    if (pathname === '/__cloud/login.js' && req.method === 'GET') {
      res.writeHead(200, { 'Content-Type': 'application/javascript; charset=utf-8', 'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff' });
      return res.end(loginScript);
    }
    if (!['GET', 'HEAD'].includes(req.method) && !originAllowed(req)) return send(res, 403, { detail: 'Nguồn truy cập không được phép.' });
    if (pathname === '/__cloud/login') {
      if (req.method === 'GET') return send(res, 200, loginPage(), true);
      if (req.method !== 'POST') return send(res, 405, { detail: 'Method not allowed' });
      if (!req.headers.origin) return send(res, 403, { detail: 'Thiếu nguồn truy cập.' });
      // A bounded global bucket avoids trusting spoofable forwarded IP headers.
      const bucket = failures.get('login');
      if (bucket && bucket.until > now() && bucket.count >= 10) return send(res, 429, loginPage('Thử sai quá nhiều lần. Hãy chờ 10 phút rồi thử lại.'), true, { 'Retry-After': '600' });
      if (!String(req.headers['content-type'] || '').startsWith('application/x-www-form-urlencoded')) return send(res, 415, { detail: 'Sai định dạng.' });
      let body = '', size = 0;
      try {
        for await (const chunk of req) {
          size += chunk.length;
          if (size > 4096) return send(res, 413, { detail: 'Yêu cầu quá lớn.' });
          body += chunk.toString();
        }
      } catch { return; }
      const supplied = new URLSearchParams(body).get('password') || '';
      if (!equal(supplied, password)) {
        const current = bucket && bucket.until > now() ? bucket : { count: 0, until: now() + 600000 };
        current.count++; failures.set('login', current);
        return send(res, 401, loginPage('Mật khẩu chưa đúng.'), true);
      }
      failures.clear();
      const payload = Buffer.from(JSON.stringify({ exp: now() + 28800000, nonce: randomBytes(16).toString('hex') })).toString('base64url');
      return send(res, 303, {}, false, { Location: '/', 'Set-Cookie': cookie(`${payload}.${sign(payload)}`, 28800) });
    }
    if (pathname === '/__cloud/logout' && req.method === 'POST') return send(res, 303, {}, false, { Location: '/__cloud/login', 'Set-Cookie': cookie('', 0) });
    if (!validSession(req)) {
      if (pathname.startsWith('/api/')) return send(res, 401, { code: 'auth_required', detail: 'Phiên đăng nhập đã hết. Tải lại trang để đăng nhập.' });
      return send(res, 303, {}, false, { Location: '/__cloud/login' });
    }
    // Retain the local backend's own mutation header guard. Validate the public
    // origin above, then translate it to the internal origin accepted by FastAPI.
    const headers = { ...req.headers, host: `127.0.0.1:${backendPort}` };
    delete headers.cookie; delete headers.authorization;
    delete headers['x-forwarded-host']; delete headers['x-forwarded-for']; delete headers['x-forwarded-proto'];
    if (headers.origin) headers.origin = `http://127.0.0.1:${backendPort}`;
    if (Number(req.headers['content-length'] || 0) > 100 * 1024 * 1024) return send(res, 413, { detail: 'Tổng tải lên tối đa 100 MB.' });
    const upstream = http.request({ hostname: '127.0.0.1', port: backendPort, path: req.url, method: req.method, headers, timeout: 150000 }, response => {
      res.writeHead(response.statusCode, { ...response.headers, 'Cache-Control': 'no-store', ...(secure ? { 'Strict-Transport-Security': 'max-age=31536000' } : {}) });
      response.pipe(res);
    });
    upstream.on('timeout', () => upstream.destroy());
    upstream.on('error', () => { if (!res.headersSent) send(res, 502, { detail: 'Bộ xử lý đang khởi động. Vui lòng thử lại.' }); else res.destroy(); });
    res.on('close', () => upstream.destroy());
    let bytes = 0;
    req.on('data', chunk => { bytes += chunk.length; if (bytes > 100 * 1024 * 1024) { upstream.destroy(); if (!res.headersSent) send(res, 413, { detail: 'Tổng tải lên tối đa 100 MB.' }); } });
    req.on('error', () => upstream.destroy());
    req.pipe(upstream);
  });
}
