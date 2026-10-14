import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const steps = [
  ['node_modules/typescript/bin/tsc', ['--noEmit']],
  ['node_modules/vite/bin/vite.js', ['build']],
];
if (steps.some(([script]) => !fs.existsSync(path.join(root, script)))) {
  console.error('Thiếu thư viện build. Chạy npm ci trong thư mục ui-smart rồi thử lại.');
  process.exit(1);
}
// Direct Node invocation also handles Windows workspace paths containing &.
for (const [script, args] of steps) {
  const result = spawnSync(process.execPath, [path.join(root, script), ...args], {
    cwd: root, stdio: 'inherit', shell: false,
  });
  if (result.error) console.error(result.error.message);
  if (result.status !== 0) process.exit(result.status ?? 1);
}
