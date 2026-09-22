#!/usr/bin/env node

import fs from 'node:fs/promises';
import path from 'node:path';
import process from 'node:process';
import { createInterface } from 'node:readline/promises';

const EXPECTED_GAME_ID = 'ULUS10466';
const DEFAULT_PHASE_SECONDS = 12;

const TARGETS = {
  slotBuilder: { label: 'slot_builder', address: 0x0892D9F8, limit: 4 },
  rectangleBuilder: { label: 'rectangle_builder', address: 0x08AB9380, limit: 4 },
  gaugeSubmit: { label: 'gauge_submit', address: 0x08928FF4, limit: 4 },
  gaugeRenderer: { label: 'gauge_renderer', address: 0x0892D3E0, limit: 4 },
  hpSpriteA: { label: 'hp_shared_sprite_a', address: 0x0892D56C, limit: 4 },
  hpSpriteB: { label: 'hp_shared_sprite_b', address: 0x0892D5B0, limit: 4 },
  stockSpriteSubmit: { label: 'stock_sprite_submit', address: 0x08825EAC, limit: 2 },
  timerRenderer: { label: 'timer_renderer', address: 0x0892D72C, limit: 4 },
  winnerConverter: { label: 'winner_glow_converter', address: 0x08AE94A4, limit: 4 },
  textScaleEarly: { label: 'text_scale_early', address: 0x08970A90, limit: 8 },
  textPackedLate: { label: 'text_packed_late', address: 0x08970B24, limit: 8 },
};

const PHASES = [
  {
    id: 'battle-baseline',
    seconds: 10,
    instructions: 'Enter Arcade/Ghost/Story fight. Keep both HP bars full, timer visible, and do not pause. Press Enter here when the active fight HUD is stable.',
    targets: ['slotBuilder', 'rectangleBuilder', 'gaugeSubmit', 'gaugeRenderer', 'hpSpriteA', 'hpSpriteB', 'stockSpriteSubmit', 'timerRenderer'],
  },
  {
    id: 'battle-partial-hp',
    seconds: 10,
    instructions: 'Damage BOTH fighters so both colored HP fills are visibly partial. Keep the round active and timer visible. Press Enter when ready.',
    targets: ['gaugeSubmit', 'gaugeRenderer', 'hpSpriteA', 'hpSpriteB', 'stockSpriteSubmit'],
  },
  {
    id: 'round-win',
    seconds: 14,
    instructions: 'Put the opponent at very low HP BEFORE pressing Enter. After capture starts, immediately land the finishing hit and stay through the winner orb/glow into the next-round HUD.',
    targets: ['slotBuilder', 'rectangleBuilder', 'winnerConverter', 'stockSpriteSubmit'],
  },
  {
    id: 'practice',
    seconds: 14,
    instructions: 'Enter Practice with the fight HUD and Practice stats visible. Press Enter, then perform a short combo so combo/hit/damage rows update during capture.',
    targets: ['rectangleBuilder', 'textScaleEarly', 'textPackedLate', 'stockSpriteSubmit'],
  },
  {
    id: 'gold-rush',
    seconds: 14,
    instructions: 'Enter Gold Rush with REWARD / ATTACK VARIATION visible. Press Enter and keep the battle active while those labels are on screen.',
    targets: ['rectangleBuilder', 'textScaleEarly', 'textPackedLate', 'stockSpriteSubmit'],
  },
  {
    id: 'pause-menu',
    seconds: 12,
    instructions: 'Start from an active fight. Press Enter, then open the pause menu and move the selection once or open one pause submenu before capture ends.',
    targets: ['slotBuilder', 'rectangleBuilder', 'stockSpriteSubmit', 'textScaleEarly', 'textPackedLate'],
  },
  {
    id: 'character-select',
    seconds: 12,
    instructions: 'Go to character select with the main selection UI visible. Press Enter, then move the cursor between characters at least once.',
    targets: ['slotBuilder', 'rectangleBuilder', 'stockSpriteSubmit', 'textScaleEarly', 'textPackedLate'],
  },
];

const STOCK_CHECKS = [
  [0x08945F10, 0x3C013FE3, '3d aspect #1 lui'], [0x08945F14, 0x34218E39, '3d aspect #1 ori'],
  [0x08946794, 0x3C013FE3, '3d aspect #2 lui'], [0x08946798, 0x34218E39, '3d aspect #2 ori'],
  [0x08946BC8, 0x3C013FE3, '3d aspect #3 lui'], [0x08946BCC, 0x34218E39, '3d aspect #3 ori'],
  [0x08947D90, 0x3C013FE3, '3d aspect #4 lui'], [0x08947D94, 0x34218E39, '3d aspect #4 ori'],

  [0x0892D9F8, 0x27BDFFE0, 'slot builder entry'],
  [0x08AB9380, 0x27BDFFC0, 'rectangle builder entry'],
  [0x08928FF4, 0x3C0308BA, 'gauge submit entry'],
  [0x0892D3E0, 0x27BDFF80, 'gauge renderer entry'],
  [0x08825EAC, 0x0A2B6DAA, 'stock sprite submit entry'],
  [0x0892D72C, 0x27BDFFF0, 'timer renderer entry'],
  [0x08AE94A4, 0x27BDFFD0, 'winner glow converter entry'],
  [0x08970A90, 0x96CB02C8, 'text scale early instruction'],
  [0x08970B24, 0x8EC402C8, 'text packed late instruction'],

  [0x08929854, 0x0E24B67E, 'slot route jal 1'], [0x08929958, 0x0E24B67E, 'slot route jal 2'],
  [0x089299E8, 0x0E24B67E, 'slot route jal 3'], [0x08929DF0, 0x0E24B67E, 'slot route jal 4'],
  [0x08929F3C, 0x0E24B67E, 'slot route jal 5'], [0x0892A10C, 0x0E24B67E, 'slot route jal 6'],
  [0x0892A170, 0x0E24B67E, 'slot route jal 7'], [0x0892A1B4, 0x0E24B67E, 'slot route jal 8'],
  [0x0892A1F0, 0x0E24B67E, 'slot route jal 9'], [0x0892A268, 0x0E24B67E, 'slot route jal 10'],
  [0x08929228, 0x0A24B67E, 'slot route tail j 1'], [0x089292F4, 0x0A24B67E, 'slot route tail j 2'],
  [0x08929D4C, 0x0A24B67E, 'slot route tail j 3'],

  [0x08AB9798, 0x0E2AE4E0, 'rectangle builder call 1'], [0x08AB98AC, 0x0E2AE4E0, 'rectangle builder call 2'],
  [0x0892C1F0, 0x0E24A3FD, 'gauge jal'], [0x0892C26C, 0x0A24A3FD, 'gauge tail j'],
  [0x0892D56C, 0x0E2097AB, 'shared sprite call 1'], [0x0892D5B0, 0x0E2097AB, 'shared sprite call 2'],
  [0x08AC9C38, 0x0E2BA529, 'winner glow converter call'],
  [0x08929AF8, 0x0E24B5CB, 'timer digit call 1'], [0x08929B44, 0x0E24B5CB, 'timer digit call 2'],
];

const SNAPSHOT_SITES = [
  ...Object.values(TARGETS).map(t => [t.address, t.label]),
  [0x0892C124, 'CGaugeTcb_Draw'], [0x0892BDAC, 'CMainTcb_Draw'],
  [0x08AC9C38, 'winner_glow_callsite'], [0x08929AF8, 'timer_callsite_1'], [0x08929B44, 'timer_callsite_2'],
];

function hex(v, width = 8) {
  if (v === undefined || v === null || Number.isNaN(v)) return null;
  return `0x${Number(v >>> 0).toString(16).padStart(width, '0').toUpperCase()}`;
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

class PPSSPPDebugger {
  constructor(endpoint) {
    this.endpoint = endpoint;
    this.ws = null;
    this.ticket = 1;
    this.pending = new Map();
    this.listeners = new Set();
  }

  async connect() {
    if (typeof WebSocket === 'undefined') {
      throw new Error('This script requires a Node.js build with the global WebSocket API (Node 20+ recommended).');
    }
    const url = this.endpoint.startsWith('ws://') || this.endpoint.startsWith('wss://')
      ? `${this.endpoint.replace(/\/$/, '')}${this.endpoint.endsWith('/debugger') ? '' : '/debugger'}`
      : `ws://${this.endpoint.replace(/\/$/, '')}/debugger`;

    await new Promise((resolve, reject) => {
      const ws = new WebSocket(url, 'debugger.ppsspp.org');
      const timer = setTimeout(() => reject(new Error(`WebSocket connection timed out: ${url}`)), 7000);
      ws.addEventListener('open', () => {
        clearTimeout(timer);
        this.ws = ws;
        resolve();
      }, { once: true });
      ws.addEventListener('error', () => {
        clearTimeout(timer);
        reject(new Error(`WebSocket connection failed: ${url}`));
      }, { once: true });
      ws.addEventListener('message', e => this.#onMessage(e.data));
      ws.addEventListener('close', () => {
        for (const p of this.pending.values()) p.reject(new Error('Debugger connection closed'));
        this.pending.clear();
      });
    });
  }

  #onMessage(raw) {
    let msg;
    try {
      msg = JSON.parse(typeof raw === 'string' ? raw : String(raw));
    } catch {
      return;
    }

    if (msg.ticket !== undefined && this.pending.has(msg.ticket)) {
      const pending = this.pending.get(msg.ticket);
      this.pending.delete(msg.ticket);
      clearTimeout(pending.timer);
      if (msg.event === 'error') pending.reject(new Error(msg.message || 'PPSSPP debugger error'));
      else pending.resolve(msg);
      return;
    }

    for (const listener of this.listeners) {
      try { listener(msg); } catch { /* listener errors are isolated */ }
    }
  }

  onEvent(listener) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  request(event, params = {}, timeoutMs = 5000) {
    const ticket = this.ticket++;
    const payload = { event, ...params, ticket };
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        this.pending.delete(ticket);
        reject(new Error(`${event} timed out`));
      }, timeoutMs);
      this.pending.set(ticket, { resolve, reject, timer });
      this.ws.send(JSON.stringify(payload));
    });
  }

  send(event, params = {}) {
    this.ws.send(JSON.stringify({ event, ...params }));
  }

  async readU32(address) {
    // memory.read_u32 preserves PPSSPP JIT/replacement opcodes.  Stock code
    // verification needs the original guest instruction instead.
    const bytes = await this.readBytes(address, 4, false);
    return bytes.readUInt32LE(0);
  }

  async readBytes(address, size, replacements = true) {
    const r = await this.request('memory.read', { address, size, replacements });
    return Buffer.from(r.base64, 'base64');
  }

  close() {
    this.ws?.close();
  }
}

function flattenRegisters(response) {
  const byName = {};
  for (const category of response.categories || []) {
    const names = category.registerNames || [];
    const uints = category.uintValues || [];
    const floats = category.floatValues || [];
    for (let i = 0; i < names.length; i++) {
      byName[names[i]] = {
        uint: uints[i] === undefined ? null : (uints[i] >>> 0),
        float: floats[i] ?? null,
        category: category.name,
      };
    }
  }
  return byName;
}

function pickReg(regs, name) {
  return regs[name]?.uint ?? null;
}

function looksLikeUserPointer(v) {
  return Number.isInteger(v) && v >= 0x08000000 && v <= 0x09FFFFC0;
}

async function safeReadBytes(debuggerClient, address, size, replacements = true) {
  try {
    return (await debuggerClient.readBytes(address >>> 0, size, replacements)).toString('hex');
  } catch {
    return null;
  }
}

async function verifyStockRuntime(client) {
  const gameStatus = await client.request('game.status');
  if (!gameStatus.game) throw new Error('No game is running in PPSSPP. Start Tekken 6 first.');
  if (gameStatus.game.id !== EXPECTED_GAME_ID) {
    throw new Error(`Wrong game: expected ${EXPECTED_GAME_ID}, got ${gameStatus.game.id} (${gameStatus.game.title || 'unknown title'})`);
  }

  const modules = await client.request('hle.module.list').catch(() => ({ modules: [] }));
  const suspiciousModules = (modules.modules || []).filter(m => /Tekken6Ultrawide/i.test(m.name || ''));

  const mismatches = [];
  const stockWords = [];
  for (const [address, expected, label] of STOCK_CHECKS) {
    const actual = await client.readU32(address);
    stockWords.push({ address: hex(address), label, expected: hex(expected), actual: hex(actual) });
    if (actual !== (expected >>> 0)) mismatches.push({ address, expected, actual, label });
  }

  if (suspiciousModules.length || mismatches.length) {
    console.error('\nSTOCK RUNTIME VERIFICATION FAILED.');
    if (suspiciousModules.length) {
      console.error('Loaded plugin-like module(s):', suspiciousModules.map(m => m.name).join(', '));
    }
    for (const m of mismatches) {
      console.error(`  ${m.label}: ${hex(m.address)} expected ${hex(m.expected)}, got ${hex(m.actual)}`);
    }
    throw new Error('Disable the ultrawide plugin / HUD patch, restart Tekken 6, and rerun the census.');
  }

  return { gameStatus, modules: modules.modules || [], stockWords };
}

async function snapshotKnownSites(client) {
  const result = [];
  for (const [address, label] of SNAPSHOT_SITES) {
    const word = await client.readU32(address).catch(() => null);
    result.push({ address: hex(address), label, word: word === null ? null : hex(word) });
  }
  return result;
}

class CensusRunner {
  constructor(client, output) {
    this.client = client;
    this.output = output;
    this.phase = null;
    this.captureBusy = false;
    this.ownedBreakpoints = new Set();
    this.unsubscribe = client.onEvent(msg => this.#onEvent(msg));
  }

  async #onEvent(msg) {
    if (!this.phase || this.captureBusy) return;
    if (msg.event !== 'cpu.stepping') return;

    // PPSSPP v1.20.4 can omit the stop reason and structured hit details, but
    // reports the stopped PC. Only accept an address armed by this phase.
    const candidateAddresses = [
      msg.hit?.breakpoint?.start,
      msg.hit?.address,
      msg.relatedAddress,
      msg.pc,
    ].filter(Number.isInteger).map(address => address >>> 0);
    const target = this.phase.targets.find(t => candidateAddresses.includes(t.address));
    if (!target) return;
    const bpAddress = target.address;

    this.captureBusy = true;
    try {
      const phase = this.phase;
      await this.#captureHit(msg, target, phase);
    } catch (err) {
      console.error(`Capture error at ${target.label}: ${err.message}`);
    } finally {
      try { this.client.send('cpu.resume'); } catch { /* connection may be closing */ }
      this.captureBusy = false;
    }
  }

  async #captureHit(stepMsg, target, phase) {
    const count = phase.counts.get(target.address) || 0;
    if (count >= target.limit) {
      await this.#removeBreakpoint(target.address);
      return;
    }

    const regsResponse = await this.client.request('cpu.getAllRegs');
    const regs = flattenRegisters(regsResponse);
    const pc = pickReg(regs, 'pc') ?? (stepMsg.pc >>> 0);
    const ra = pickReg(regs, 'ra');
    const sp = pickReg(regs, 'sp');
    const f12 = regs.f12 || null;

    const stackHex = sp && looksLikeUserPointer(sp)
      ? await safeReadBytes(this.client, sp, 0x80)
      : null;
    const pcBytes = pc >= 0x10
      ? await safeReadBytes(this.client, pc - 0x10, 0x40, false)
      : null;
    const raBytes = ra && ra >= 0x10
      ? await safeReadBytes(this.client, ra - 0x10, 0x30, false)
      : null;

    const pointerRegs = ['a0', 'a1', 'a2', 'a3', 't0', 't1', 't2', 't3', 's0', 's1', 's2', 's3'];
    const seen = new Set();
    const pointerSnapshots = [];
    for (const regName of pointerRegs) {
      const value = pickReg(regs, regName);
      if (!looksLikeUserPointer(value) || seen.has(value)) continue;
      seen.add(value);
      const bytes = await safeReadBytes(this.client, value, 0x40);
      if (bytes !== null) {
        pointerSnapshots.push({ register: regName, address: hex(value), bytesHex: bytes });
      }
      if (pointerSnapshots.length >= 6) break;
    }

    const backtrace = await this.client.request('hle.backtrace').catch(err => ({ error: err.message }));
    const cpuStatus = await this.client.request('cpu.status').catch(() => null);

    const nextCount = count + 1;
    phase.counts.set(target.address, nextCount);

    const summary = {
      phase: phase.id,
      target: target.label,
      targetAddress: hex(target.address),
      hitNumber: nextCount,
      breakpointSequence: stepMsg.sequence ?? null,
      pc: hex(pc),
      ra: hex(ra),
      sp: hex(sp),
      a0: hex(pickReg(regs, 'a0')),
      a1: hex(pickReg(regs, 'a1')),
      a2: hex(pickReg(regs, 'a2')),
      a3: hex(pickReg(regs, 'a3')),
      t0: hex(pickReg(regs, 't0')),
      t1: hex(pickReg(regs, 't1')),
      t2: hex(pickReg(regs, 't2')),
      t3: hex(pickReg(regs, 't3')),
      f12,
      ticks: stepMsg.ticks ?? cpuStatus?.ticks ?? null,
      emulatedUs: cpuStatus?.us ?? null,
      registers: regsResponse.categories || [],
      backtrace,
      stackHex,
      pcWindowHex: pcBytes,
      raWindowHex: raBytes,
      pointerSnapshots,
    };

    this.output.hits.push(summary);
    console.log(`  HIT ${target.label.padEnd(22)} #${nextCount} pc=${hex(pc)} ra=${hex(ra)} a0=${hex(pickReg(regs, 'a0'))} a1=${hex(pickReg(regs, 'a1'))} f12=${f12?.float ?? '-'}`);

    if (nextCount >= target.limit) {
      await this.#removeBreakpoint(target.address);
    }
  }

  async #addBreakpoint(address) {
    await this.client.request('cpu.breakpoint.add', { address, enabled: true, log: false });
    this.ownedBreakpoints.add(address);
  }

  async #removeBreakpoint(address) {
    if (!this.ownedBreakpoints.has(address)) return;
    try {
      await this.client.request('cpu.breakpoint.remove', { address });
    } catch {
      // It may already have been removed during phase cleanup.
    }
    this.ownedBreakpoints.delete(address);
  }

  async runPhase(phaseDef) {
    const targets = phaseDef.targets.map(key => ({ ...TARGETS[key] }));
    this.phase = {
      id: phaseDef.id,
      targets,
      counts: new Map(),
    };

    const existing = await this.client.request('cpu.breakpoint.list');
    const existingAddresses = new Set((existing.breakpoints || []).map(b => b.address >>> 0));
    const overlap = targets.filter(t => existingAddresses.has(t.address));
    if (overlap.length) {
      throw new Error(`Existing breakpoint(s) overlap this phase: ${overlap.map(t => `${t.label}@${hex(t.address)}`).join(', ')}. Remove them in PPSSPP and retry.`);
    }

    for (const target of targets) await this.#addBreakpoint(target.address);

    console.log(`\nCAPTURING ${phaseDef.id} for ${phaseDef.seconds ?? DEFAULT_PHASE_SECONDS}s...`);
    console.log('Use the phone now. The game may briefly pause on sampled renderer hits; the probe resumes it automatically.');
    await sleep((phaseDef.seconds ?? DEFAULT_PHASE_SECONDS) * 1000);

    this.phase = null;
    while (this.captureBusy) await sleep(20);
    for (const address of [...this.ownedBreakpoints]) await this.#removeBreakpoint(address);

    const counts = targets.map(t => ({ label: t.label, address: hex(t.address), hits: this.output.hits.filter(h => h.phase === phaseDef.id && h.target === t.label).length }));
    this.output.phases.push({ id: phaseDef.id, counts });

    console.log(`Finished ${phaseDef.id}:`);
    for (const c of counts) console.log(`  ${c.label.padEnd(22)} ${c.hits} hit(s)`);
  }

  async cleanup() {
    this.phase = null;
    while (this.captureBusy) await sleep(20);
    for (const address of [...this.ownedBreakpoints]) await this.#removeBreakpoint(address);
    this.unsubscribe?.();
  }
}

async function main() {
  const endpoint = process.argv[2];
  if (!endpoint || endpoint.startsWith('--')) {
    console.error('Usage: node tools/research/probes/ppsspp_stock_renderer_census.mjs <PHONE_IP:PORT>');
    console.error('Example: node tools/research/probes/ppsspp_stock_renderer_census.mjs 192.168.0.101:43091');
    process.exit(2);
  }

  const rl = createInterface({ input: process.stdin, output: process.stdout });
  const client = new PPSSPPDebugger(endpoint);
  const output = {
    format: 'tekken6-stock-renderer-census-v1',
    createdAt: new Date().toISOString(),
    endpoint,
    metadata: {},
    phases: [],
    hits: [],
  };
  let runner;

  try {
    console.log('Connecting to PPSSPP remote debugger...');
    await client.connect();

    const version = await client.request('version', { name: 'tekken6-stock-renderer-census', version: '1.0' });
    console.log(`Connected: ${version.name} ${version.version}`);

    console.log('Verifying Tekken 6 USA and stock/no-plugin code...');
    const verification = await verifyStockRuntime(client);
    console.log(`Game: ${verification.gameStatus.game.title} (${verification.gameStatus.game.id})`);
    console.log('Stock runtime verification: PASS');

    output.metadata.version = version;
    output.metadata.game = verification.gameStatus.game;
    output.metadata.modules = verification.modules;
    output.metadata.stockWords = verification.stockWords;
    output.metadata.siteWords = await snapshotKnownSites(client);

    console.log('\nThis probe does NOT write Tekken memory. It uses debugger execution breakpoints plus read-only register/memory snapshots.');
    console.log('For the clean control, keep Tekken6Ultrawide.prx disabled and keep aspect/HUD CWCheats disabled for the whole run.');

    runner = new CensusRunner(client, output);

    for (const phase of PHASES) {
      console.log(`\n=== ${phase.id.toUpperCase()} ===`);
      console.log(phase.instructions);
      const answer = await rl.question('Press Enter when ready, or type s then Enter to skip this phase: ');
      if (answer.trim().toLowerCase() === 's') {
        console.log(`Skipped ${phase.id}.`);
        output.phases.push({ id: phase.id, skipped: true, counts: [] });
        continue;
      }
      await runner.runPhase(phase);
    }

    const outDir = path.join(process.cwd(), 'research', 'captures');
    await fs.mkdir(outDir, { recursive: true });
    const stamp = new Date().toISOString().replace(/[:.]/g, '-');
    const outPath = path.join(outDir, `stock-renderer-census-${stamp}.json`);
    await fs.writeFile(outPath, `${JSON.stringify(output, null, 2)}\n`, 'utf8');

    console.log(`\nCapture complete: ${outPath}`);
    console.log(`Total sampled renderer hits: ${output.hits.length}`);
    console.log('Send me this JSON file unchanged. It contains the stock renderer/register/stack/pointer snapshots needed for comparison with v1.2.0.');
  } finally {
    try { await runner?.cleanup(); } catch { /* best effort */ }
    client.close();
    rl.close();
  }
}

main().catch(err => {
  console.error(`\nERROR: ${err.message}`);
  process.exitCode = 1;
});
