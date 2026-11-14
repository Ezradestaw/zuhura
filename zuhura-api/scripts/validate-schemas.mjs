import { spawnSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const apiRoot = resolve(here, '..');
const venvPython = resolve(apiRoot, '../.venv/bin/python');
const python = existsSync(venvPython) ? venvPython : 'python3';
const script = resolve(here, 'validate_schemas.py');

const result = spawnSync(python, [script], { stdio: 'inherit', cwd: apiRoot });
if (result.error) {
  console.error(result.error.message);
  process.exit(1);
}
process.exit(result.status ?? 1);
