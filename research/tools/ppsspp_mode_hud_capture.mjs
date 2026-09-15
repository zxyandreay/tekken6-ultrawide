#!/usr/bin/env node
/**
 * Capture stable Practice and Gold Rush HUD frames for ultrawide research.
 *
 * Read-only: no breakpoints and no game-memory writes.
 * Phases:
 *   practice-idle  - infinity timer/status visible, no active combo
 *   practice-hit   - Practice hit/damage/combo readout populated and stable
 *   goldrush       - active Gold Rush fight with right-side HUD visible
 */

import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { createInterface } from 'node:readline/promises';
import { stdin as input, stdout as output } from 'node:process';
import { fileURLToPath } from 'node:url';

const EXPECTED_GAME = 'ULUS10466';
const PHASES = [
  {
    id: 'practice-idle',
    title: 'PRACTICE - IDLE',
    lines: [
      'Enter Practice with the full fight HUD visible.',
      'Keep the infinity-time indicator visible and do not pause.',
      'Do not perform an attack immediately before capture.',
    ],
  },
  {
    id: 'practice-hit',
    title: 'PRACTICE - HIT / COMBO READOUT',
    lines: [
      'Remain in Practice and perform a short combo or hit sequence.',
      'Wait until the HITS / DAMAGE / combo values are visible and stable.',
      'Do not pause or open Practice settings.',
    ],
  },
  {
    id: 'goldrush',
    title: 'GOLD RUSH',
    lines: [
      'Enter an active Gold Rush fight with the full HUD visible.',
      'Make sure the right-side Gold Rush score/gold HUD is visible.',
      'Avoid K.O./result overlays, pause menus, and loading transitions.',
    ],
  },
];
const FRAMES_PER_PHASE = 2;

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, '..', '..');
const rootDir = path.join(repoRoot, '.local-research', 'mode-hud');
const analyzer = path.join(__dirname, 'ppdmp_mode_hud_analysis.py');

function normalizeEndpoint(raw) {
  let value = String(raw || '').trim();
  if (!value) throw new Error('Debugger endpoint missing. Pass <host:port>.');
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
    const r = spawnSync(exe, [...prefix, '--version'], { encoding: 'utf8' });
    if (r.status === 0) return { exe, prefix };
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
      for (const p of this.pending.values()) p.reject(new Error('WebSocket closed'));
      this.pending.clear();
    });
  }

  onMessage(event) {
    let msg;
    try { msg = JSON.parse(String(event.data)); } catch { return; }
    if (msg.ticket != null && this.pending.has(msg.ticket)) {
      const p = this.pending.get(msg.ticket);
      this.pending.delete(msg.ticket);
      clearTimeout(p.timer);
      if (msg.event === 'error') p.reject(new Error(msg.message || 'PPSSPP debugger error'));
      else p.resolve(msg);
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

async function captureOne(dbg, filename) {
  const msg = await dbg.request('gpu.record.dump', {}, 30000);
  saveFrameDump(msg.uri, filename);
}

async function main() {
  const endpointArg = process.argv[2] || process.env.PPSSPP_DEBUGGER;
  if (!endpointArg) {
    console.log('Usage: node research/tools/ppsspp_mode_hud_capture.mjs <host:port>');
    process.exit(2);
  }

  fs.rmSync(rootDir, { recursive: true, force: true });
  fs.mkdirSync(rootDir, { recursive: true });

  const dbg = new PPSSPPDebugger(normalizeEndpoint(endpointArg));
  const rl = createInterface({ input, output });
  try {
    console.log('Connecting to PPSSPP remote debugger...');
    await dbg.connect();
    const status = await dbg.request('game.status', {});
    if (status.game?.id !== EXPECTED_GAME) {
      throw new Error(`Expected ${EXPECTED_GAME}, got ${status.game?.id ?? 'no running game'}`);
    }
    console.log(`Connected: ${status.game.title || EXPECTED_GAME} (${status.game.id})`);
    console.log('Read-only capture: no breakpoints and no game-memory writes.');

    for (const phase of PHASES) {
      console.log('');
      console.log(phase.title);
      for (const line of phase.lines) console.log(line);
      await rl.question('Press Enter when this HUD state is stable... ');
      for (let i = 1; i <= FRAMES_PER_PHASE; ++i) {
        const file = path.join(rootDir, `${phase.id}-${i}.ppdmp`);
        process.stdout.write(`Capturing ${phase.id} frame ${i}/${FRAMES_PER_PHASE}... `);
        await captureOne(dbg, file);
        console.log('done');
      }
    }

    const python = findPython();
    console.log('');
    console.log('Analyzing stable mode-specific HUD draws...');
    const result = spawnSync(
      python.exe,
      [...python.prefix, analyzer, rootDir],
      { cwd: repoRoot, encoding: 'utf8' },
    );
    if (result.stdout) process.stdout.write(result.stdout);
    if (result.status !== 0) {
      throw new Error(`mode-HUD analyzer failed:\n${result.stderr || result.stdout}`);
    }
    console.log(`Report: ${path.relative(repoRoot, path.join(rootDir, 'analysis.json'))}`);
  } finally {
    rl.close();
    dbg.close();
  }
}

main().catch(err => {
  console.error(`Error: ${err.message}`);
  process.exitCode = 1;
});
