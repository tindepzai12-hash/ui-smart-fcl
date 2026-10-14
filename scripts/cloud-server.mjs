import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { createGateway } from './cloud-gateway.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const port = Number(process.env.PORT || 10000);
const backendPort = Number(process.env.UI_SMART_BACKEND_PORT || 8767);
if (!Number.isInteger(port) || !Number.isInteger(backendPort) || port === backendPort) throw new Error('Invalid port configuration');
const server = createGateway({ password: process.env.UI_SMART_PASSWORD, secret: process.env.UI_SMART_SESSION_SECRET, backendPort, secure: process.env.UI_SMART_INSECURE_LOCAL !== '1' || Boolean(process.env.RENDER) });
const child = spawn(process.env.PYTHON_EXECUTABLE || 'python3', ['-u', path.join(root, 'run.py'), '--port', String(backendPort)], {
  cwd: root, stdio: ['ignore', 'inherit', 'inherit'], shell: false,
  env: { ...process.env, UI_SMART_CLOUD: '1', UI_SMART_DATA: process.env.UI_SMART_DATA || path.join(root, 'data'), PYTHONUNBUFFERED: '1', LD_LIBRARY_PATH: [path.join(root, 'tools/ocr/usr/lib/x86_64-linux-gnu'), process.env.LD_LIBRARY_PATH].filter(Boolean).join(':') },
});
let stopping = false;
function stop(code = 0) {
  if (stopping) return;
  stopping = true;
  server.close(); child.kill('SIGTERM');
  setTimeout(() => { child.kill('SIGKILL'); process.exit(code); }, 5000).unref();
  child.once('exit', () => process.exit(code));
}
child.on('error', () => { console.error('Document processor could not start. Check Python installation.'); stop(1); });
child.on('exit', code => { if (!stopping) { console.error('Document processor stopped:', code); server.close(); process.exit(code || 1); } });
server.on('error', error => { console.error('Web server failed:', error.code); stop(1); });
server.listen(port, '0.0.0.0', () => console.log(`U&I SMART Node gateway listening on port ${port}`));
process.on('SIGTERM', () => stop());
process.on('SIGINT', () => stop());
