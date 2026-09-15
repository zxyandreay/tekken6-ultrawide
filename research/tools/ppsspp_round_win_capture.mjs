#!/usr/bin/env node
/**
 * Tekken 6 ULUS10466 - neutral round-win frame capture.
 *
 * Captures three phases for one controlled winner:
 *   - 2 pre-KO frames
 *   - 18 immediate win/burst frames
 *   - 3 stable next-round frames
 *
 * No breakpoints are installed and no game memory is written.
 */

import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { createInterface } from 'node:readline/promises';
import { stdin as input, stdout as output } from 'node:process';
import { fileURLToPath } from 'node:url';

const EXPECTED_GAME = 'ULUS10466';
const PRE_COUNT = 2;
const BURST_COUNT = 18;
const NEXT_COUNT = 3;

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, '..', '..');
const rootDir = path.join(repoRoot, '.local-research', 'round-win');
const analyzer = path.join(__dirname, 'ppdmp_round_win_analysis.py');

function normalizeEndpoint(raw) {
  let value = String(raw || '').trim();
  if (!value) throw new Error('Debugger endpoint missing. Pass <host:port> or set PPSSPP_DEBUGGER.');
  if (!/^wss?:\/\//i.test(value)) value = `ws://${value}`;
  const url = new URL(value);
  if (!url.pathname || url.pathname === '/') url.pathname = '/debugger';
  return url.toString();
}

function findPython() {
  const candidates = process.platform === 'win32'
    ? [['py', ['-3']], ['python', []], ['python3', []]]
    : [['python3', []], ['python', []]];
  for (const [exe, prefix] of candidates) {
    const result = spawnSync(exe, [...prefix, '--version'], { encoding: 'utf8' });
    if (result.status === 0) return { exe, prefix };
  }
  throw new Error('Python 3 was not found in PATH.');
}

class PPSSPPDebugger {
  constructor(endpoint) {
    this.endpoint = endpoint;
    this.ws = null;
    this.ticket = 1;
    this.pending = new Map();
  }

  async connect() {
    this.ws = new WebSocket(this.endpoint, 'debugger.ppsspp.org');
    await new Promise((resolve, reject) => {
      const timer = setTimeout(() => reject(new Error('WebSocket connection timed out')), 10000);
      this.ws.addEventListener('open', () => { clearTimeout(timer); resolve(); }, { once: true });
      this.ws.addEventListener('error', () => { clearTimeout(timer); reject(new Error('WebSocket connection failed')); }, { once: true });
    });
    this.ws.addEventListener('message', event => this.onMessage(event));
    this.ws.addEventListener('close', () => {
      for (const pending of this.pending.values()) pending.reject(new Error('WebSocket closed'));
      this.pending.clear();
    });
  }

  onMessage(event) {
    let message;
    try { message = JSON.parse(String(event.data)); } catch { return; }
    if (message.ticket != null && this.pending.has(message.ticket)) {
      const pending = this.pending.get(message.ticket);
      this.pending.delete(message.ticket);
      clearTimeout(pending.timer);
      if (message.event === 'error') pending.reject(new Error(message.message || 'PPSSPP debugger error'));
      else pending.resolve(message);
    }
  }

  request(event, params = {}, timeoutMs = 30000) {
    const ticket = this.ticket++;
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        this.pending.delete(ticket);
        reject(new Error(`${event} timed out`));
      }, timeoutMs);
      this.pending.set(ticket, { resolve, reject, timer });
      this.ws.send(JSON.stringify({ event, ticket, ...params }));
    });
  }

  close() {
    try { this.ws?.close(); } catch {}
  }
}

function saveFrameDump(uri, filename) {
  const marker = 'base64,';
  const at = String(uri || '').indexOf(marker);
  if (at < 0) throw new Error('gpu.record.dump returned an unexpected URI');
  fs.writeFileSync(filename, Buffer.from(uri.slice(at + marker.length), 'base64'));
}

async function captureOne(debuggerClient, filename) {
  const message = await debuggerClient.request('gpu.record.dump', {}, 30000);
  saveFrameDump(message.uri, filename);
}

async function captureSeries(debuggerClient, dir, prefix, count) {
  for (let i = 1; i <= count; ++i) {
    const file = path.join(dir, `${prefix}-${String(i).padStart(2, '0')}.ppdmp`);
    process.stdout.write(`\r${prefix} capture ${i}/${count}`);
    await captureOne(debuggerClient, file);
  }
  process.stdout.write('\n');
}

function usage() {
  console.log('Usage: node research/tools/ppsspp_round_win_capture.mjs <host:port> <p1|p2>');
}

async function main() {
  const endpointArg = process.argv[2] || process.env.PPSSPP_DEBUGGER;
  const side = String(process.argv[3] || '').toLowerCase();
  if (!endpointArg || !['p1', 'p2'].includes(side)) {
    usage();
    process.exit(2);
  }

  const dir = path.join(rootDir, side);
  fs.rmSync(dir, { recursive: true, force: true });
  fs.mkdirSync(dir, { recursive: true });

  const debuggerClient = new PPSSPPDebugger(normalizeEndpoint(endpointArg));
  const rl = createInterface({ input, output });
  try {
    console.log('Connecting to PPSSPP remote debugger...');
    await debuggerClient.connect();
    const version = await debuggerClient.request('version', {});
    const status = await debuggerClient.request('game.status', {});
    if (status.game?.id !== EXPECTED_GAME) {
      throw new Error(`Expected ${EXPECTED_GAME}, got ${status.game?.id ?? 'no running game'}`);
    }

    console.log(`Connected: ${status.game.title || EXPECTED_GAME} (${status.game.id})`);
    console.log(`PPSSPP debugger version: ${version.version || 'unknown'}`);
    console.log(`Controlled winner: ${side.toUpperCase()}`);
    console.log('Read-only capture: no breakpoints and no game-memory writes.');
    console.log('');

    console.log('PHASE 1 - pre-KO baseline');
    console.log(`Set up a clean 0-0 round where ${side.toUpperCase()} will win.`);
    console.log('Put the losing player at very low HP, but do not finish the round yet.');
    await rl.question('Press Enter to capture the stable pre-KO HUD... ');
    await captureSeries(debuggerClient, dir, 'pre', PRE_COUNT);

    console.log('');
    console.log('PHASE 2 - immediate round-win sequence');
    console.log(`After pressing Enter, immediately make ${side.toUpperCase()} win the round.`);
    console.log('Once the finishing hit lands, do not pause, skip, or load a state while the burst captures run.');
    await rl.question('Press Enter when ready to deliver the finishing hit... ');
    await captureSeries(debuggerClient, dir, 'burst', BURST_COUNT);

    console.log('');
    console.log('PHASE 3 - next-round stable HUD');
    console.log('Wait until the next round starts and both round-marker areas are stable and visible.');
    console.log('Do not load a save state between the win and this capture.');
    await rl.question('Press Enter once the next-round HUD is stable... ');
    await captureSeries(debuggerClient, dir, 'next', NEXT_COUNT);

    const python = findPython();
    console.log('');
    console.log('Analyzing top-HUD THROUGH draws...');
    const result = spawnSync(
      python.exe,
      [...python.prefix, analyzer, dir, '--side', side],
      { cwd: repoRoot, encoding: 'utf8' },
    );
    if (result.stdout) process.stdout.write(result.stdout);
    if (result.status !== 0) {
      throw new Error(`round-win analyzer failed:\n${result.stderr || result.stdout}`);
    }

    console.log('');
    console.log('Round-win capture complete.');
    console.log(`Report: ${path.relative(repoRoot, path.join(dir, 'analysis.json'))}`);
  } finally {
    rl.close();
    debuggerClient.close();
  }
}

main().catch(error => {
  console.error(`Error: ${error.message}`);
  process.exitCode = 1;
});
