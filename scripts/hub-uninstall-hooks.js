#!/usr/bin/env node
const { spawnSync } = require('node:child_process');
const { existsSync } = require('node:fs');
const path = require('node:path');

function runPwsh(script, args = []) {
  const exe = 'pwsh';
  const res = spawnSync(exe, ['-File', script, ...args], { stdio: 'inherit', cwd: process.cwd() });
  if (res.status !== 0) {
    process.exit(res.status ?? 1);
  }
}

try {
  const repoRoot = process.cwd();
  if (!existsSync(path.join(repoRoot, '.git'))) {
    process.exit(0);
  }
  const packageRoot = path.resolve(__dirname, '..');
  const script = path.join(packageRoot, 'precommit', 'utils', 'uninstall.ps1');
  const hooksTarget = path.join(repoRoot, '.git', 'hooks');
  const backupDir = path.join(repoRoot, '.git', 'hooks.backup.hub');

  runPwsh(script, [
    '-HooksTarget', hooksTarget,
    '-BackupDir', backupDir,
    '-Restore'
  ]);
} catch (e) {
  console.error('[hub] uninstall failed:', e?.message || e);
  process.exit(1);
}
