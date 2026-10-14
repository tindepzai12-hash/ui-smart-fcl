import { test } from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import { createGateway } from '../scripts/cloud-gateway.mjs';

test('cloud auth protects files and APIs, validates origin, expires sessions and redacts health', async t => {
  let now = Date.now();
  const upstream = http.createServer((req, res) => {
    res.setHeader('content-type', 'application/json');
    res.end(JSON.stringify(req.url === '/api/health' ? { ok: true, private: 'must not leak' } : { host: req.headers.host, origin: req.headers.origin, guard: req.headers['x-ui-smart'], cookie: req.headers.cookie }));
  });
  await new Promise(r => upstream.listen(0, '127.0.0.1', r));
  const backendPort = upstream.address().port;
  const gateway = createGateway({ password: 'test-password-123456', secret: 's'.repeat(64), backendPort, secure: false, now: () => now });
  await new Promise(r => gateway.listen(0, '127.0.0.1', r));
  t.after(() => { gateway.closeAllConnections(); gateway.close(); upstream.closeAllConnections(); upstream.close(); });
  const url = `http://127.0.0.1:${gateway.address().port}`;
  const request = (p, options = {}) => fetch(url + p, { redirect: 'manual', ...options });
  assert.deepEqual(await (await request('/healthz')).json(), { ok: true });
  for (const p of ['/', '/assets/app.js', '/data/private.sqlite', '/docs']) assert.equal((await request(p)).status, 303);
  assert.equal((await request('/api/cases')).status, 401);
  const login = (password, origin = url) => request('/__cloud/login', { method: 'POST', headers: { Origin: origin, 'Content-Type': 'application/x-www-form-urlencoded' }, body: new URLSearchParams({ password }) });
  assert.equal((await login('test-password-123456', 'https://evil.example')).status, 403);
  assert.equal((await login('wrong')).status, 401);
  const signed = await login('test-password-123456');
  assert.equal(signed.status, 303);
  const rawCookie = signed.headers.get('set-cookie');
  assert.match(rawCookie, /HttpOnly; SameSite=Strict/);
  const cookie = rawCookie.split(';')[0];
  const headers = { Cookie: cookie, Origin: url, 'X-UI-Smart': 'local' };
  const result = await request('/api/cases', { method: 'POST', headers });
  assert.equal(result.status, 200);
  const proxied = await result.json();
  assert.equal(proxied.host, `127.0.0.1:${backendPort}`);
  assert.equal(proxied.origin, `http://127.0.0.1:${backendPort}`);
  assert.equal(proxied.guard, 'local');
  assert.equal(proxied.cookie, undefined);
  assert.equal((await request('/api/cases', { method: 'POST', headers: { ...headers, Origin: 'https://evil.example' } })).status, 403);
  assert.equal((await request('/api/cases', { headers: { Cookie: cookie + 'tampered' } })).status, 401);
  assert.match((await request('/__cloud/logout', { method: 'POST', headers })).headers.get('set-cookie'), /Max-Age=0/);
  now += 8 * 60 * 60 * 1000 + 1;
  assert.equal((await request('/api/cases', { headers })).status, 401);
});

test('weak configuration fails closed and login brute force is bounded', async t => {
  assert.throws(() => createGateway({ password: '', secret: '', backendPort: 1 }), /strong/);
  const gateway = createGateway({ password: 'test-password-123456', secret: 's'.repeat(64), backendPort: 1, secure: false });
  await new Promise(r => gateway.listen(0, '127.0.0.1', r));
  t.after(() => { gateway.closeAllConnections(); gateway.close(); });
  const url = `http://127.0.0.1:${gateway.address().port}`;
  for (let i = 0; i < 11; i++) {
    const r = await fetch(url + '/__cloud/login', { method: 'POST', headers: { Origin: url, 'Content-Type': 'application/x-www-form-urlencoded' }, body: 'password=wrong' });
    assert.equal(r.status, i < 10 ? 401 : 429);
  }
  assert.equal((await fetch(url + '/healthz')).status, 503);
});
