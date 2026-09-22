#!/usr/bin/env node

import crypto from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import process from 'node:process';
import { createInterface } from 'node:readline/promises';

const EXPECTED_GAME_ID = 'ULUS10466';
const REQUIRED_PROTOCOL = 'debugger.ppsspp.org';
const DEFAULT_MAX_HITS = 24;
const DEFAULT_TIMEOUT_MS = 6000;
const BREAKPOINT_HEALTH_MS = 1200;
const TARGET_AFTER_CANARY_MS = 1800;
const STACK_BYTES = 0x100;
const PACKET_BYTES = 0x40;
const DESCRIPTOR_TABLE = 0x08B9BB84;

const SITES = {
  // These exact call instructions are already proven to trap under PPSSPP
  // v1.20.4. Capturing here is explicitly pre-delay-slot/pre-wrapper.
  sharedA: { label: 'D56C', address: 0x0892D56C, callAddress: 0x0892D56C, expectedReturn: 0x0892D574 },
  sharedB: { label: 'D5B0', address: 0x0892D5B0, callAddress: 0x0892D5B0, expectedReturn: 0x0892D5B8 },
  // Visible HP reaches this owner before the shared packet builder. It is a
  // breakpoint-health canary only; its state is never used to classify a
  // downstream packet.
  canary: { label: 'gauge-canary', address: 0x08928FF4 },
  stockSubmit: { label: 'stock-submit', address: 0x08825EAC },
};

const STOCK_CHECKS = [
  [0x08945F10, 0x3C013FE3, '3D aspect #1 LUI'],
  [0x08945F14, 0x34218E39, '3D aspect #1 ORI'],
  [0x08946794, 0x3C013FE3, '3D aspect #2 LUI'],
  [0x08946798, 0x34218E39, '3D aspect #2 ORI'],
  [0x08946BC8, 0x3C013FE3, '3D aspect #3 LUI'],
  [0x08946BCC, 0x34218E39, '3D aspect #3 ORI'],
  [0x08947D90, 0x3C013FE3, '3D aspect #4 LUI'],
  [0x08947D94, 0x34218E39, '3D aspect #4 ORI'],
  [0x0892C1F0, 0x0E24A3FD, 'HP gauge JAL owner'],
  [0x0892C26C, 0x0A24A3FD, 'HP gauge tail-J owner'],
  [0x0892D56C, 0x0E2097AB, 'shared sprite call D56C'],
  [0x0892D5B0, 0x0E2097AB, 'shared sprite call D5B0'],
  [0x08825EAC, 0x0A2B6DAA, 'stock sprite submitter'],
];

const BREAKPOINT_SHAPE_CHECKS = [
  [0x0892D568, 0x46800820, 'D56C pre-call height conversion'],
  [0x0892D5AC, 0x46000000, 'D5B0 pre-call height doubling'],
];

const V120_RELEASE = {
  prxSha256: '311720e8aa115865343df4fcd13fa5e9f8f074ff1e05348ab165e9c6ef81ee75',
  // These are ELF program-header values from the release artifact.  PPSSPP's
  // hle.module.list `size` is the allocated module memory-block span, not
  // PT_LOAD p_memsz; PPSSPP v1.20.4 reports the 0xEB0 release as 0x0F00.
  elfLoadFileSize: 0x0EB0,
  elfLoadMemorySize: 0x0EB0,
  knownPpssppModuleSpan: 0x0F00,
  gaugeWrapperOffset: 0x07E4,
  downstreamWrapperOffset: 0x0850,
  downstreamSignatureOffset: 0x0850,
  downstreamSignatureSize: 0x00E4,
  downstreamSignatureSha256: 'd752ffb38520ab692c72267990f002254e63da2318ce15afe52422872e2ba910',
};

const V120_HOOKS = [
  { address: 0x0892C1F0, label: 'HP gauge JAL owner', opcode: 3, targetOffset: V120_RELEASE.gaugeWrapperOffset },
  { address: 0x0892C26C, label: 'HP gauge tail-J owner', opcode: 2, targetOffset: V120_RELEASE.gaugeWrapperOffset },
  { address: 0x0892D56C, label: 'shared sprite call D56C', opcode: 3, targetOffset: V120_RELEASE.downstreamWrapperOffset },
  { address: 0x0892D5B0, label: 'shared sprite call D5B0', opcode: 3, targetOffset: V120_RELEASE.downstreamWrapperOffset },
];

const V120_RUNTIME_PARAMETERS = [
  [0x08802300, 'horizontalScaleQ15', 'u32'],
  [0x08802304, 'horizontalScale', 'float'],
  [0x08802310, 'hpShift', 'float'],
  [0x08802314, 'hpScale', 'float'],
];

const SELECTED_REGISTERS = [
  'pc', 'ra', 'sp',
  'v0',
  'a0', 'a1', 'a2', 'a3',
  't0', 't1', 't2', 't3', 't4', 't5',
  's0', 's1', 's2', 's3', 's4', 's5', 's6', 's7',
  'f0', 'f12',
];

function hex(value, width = 8) {
  if (!Number.isInteger(value)) return null;
  return `0x${(value >>> 0).toString(16).padStart(width, '0').toUpperCase()}`;
}

function floatEqual(a, b, epsilon = 0.01) {
  return Number.isFinite(a) && Math.abs(a - b) <= epsilon;
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function debuggerUrl(endpoint) {
  const raw = endpoint.trim();
  const withScheme = /^(?:ws|wss):\/\//i.test(raw) ? raw : `ws://${raw}`;
  const url = new URL(withScheme);
  if (!['ws:', 'wss:'].includes(url.protocol)) throw new Error(`Unsupported debugger URL scheme: ${url.protocol}`);

  const normalizedPath = url.pathname.replace(/\/+$/, '');
  if (!normalizedPath) url.pathname = '/debugger';
  else if (normalizedPath !== '/debugger') throw new Error(`Expected debugger path /debugger, got ${url.pathname}`);
  else url.pathname = '/debugger';
  return url;
}

async function decodeMessageData(data) {
  if (typeof data === 'string') return data;
  if (data instanceof ArrayBuffer) return Buffer.from(data).toString('utf8');
  if (ArrayBuffer.isView(data)) return Buffer.from(data.buffer, data.byteOffset, data.byteLength).toString('utf8');
  if (data && typeof data.text === 'function') return data.text();
  return String(data);
}

class PPSSPPDebugger {
  constructor(endpoint) {
    this.url = debuggerUrl(endpoint);
    this.ws = null;
    this.ticket = 1;
    this.pending = new Map();
    this.listeners = new Set();
  }

  async connect() {
    if (typeof WebSocket === 'undefined') throw new Error('Node.js with the global WebSocket API is required (Node 20+ recommended).');

    await new Promise((resolve, reject) => {
      const ws = new WebSocket(this.url, REQUIRED_PROTOCOL);
      let lastError = null;
      let settled = false;
      const finish = error => {
        if (settled) return;
        settled = true;
        clearTimeout(timer);
        if (error) reject(error);
        else resolve();
      };
      const timer = setTimeout(() => {
        ws.close();
        finish(new Error(`WebSocket connection timed out: ${this.url.href}`));
      }, 7000);

      ws.addEventListener('open', () => {
        if (ws.protocol !== REQUIRED_PROTOCOL) {
          ws.close(1002, 'Required subprotocol not selected');
          finish(new Error(`PPSSPP selected subprotocol ${JSON.stringify(ws.protocol)}, expected ${JSON.stringify(REQUIRED_PROTOCOL)}`));
          return;
        }
        this.ws = ws;
        finish();
      }, { once: true });
      ws.addEventListener('error', event => {
        const detail = event.error?.message || event.message || 'Node WebSocket API reported no network error detail';
        lastError = event.error || new Error(detail);
        finish(new Error(`WebSocket connection failed: ${detail}`));
      });
      ws.addEventListener('close', event => {
        if (!this.ws) finish(new Error(`WebSocket closed before opening (code=${event.code}, reason=${event.reason || lastError?.message || 'none'})`));
        for (const pending of this.pending.values()) {
          clearTimeout(pending.timer);
          pending.reject(new Error(`Debugger connection closed while waiting for ${pending.event}`));
        }
        this.pending.clear();
      });
      ws.addEventListener('message', event => void this.#onMessage(event.data));
    });
  }

  async #onMessage(data) {
    const raw = await decodeMessageData(data);
    let message;
    try {
      message = JSON.parse(raw);
    } catch {
      return;
    }

    if (message.ticket !== undefined && this.pending.has(message.ticket)) {
      const pending = this.pending.get(message.ticket);
      this.pending.delete(message.ticket);
      clearTimeout(pending.timer);
      if (message.event === 'error') pending.reject(new Error(message.message || `${pending.event} returned an error`));
      else pending.resolve(message);
      return;
    }

    for (const listener of this.listeners) {
      try { listener(message); } catch { /* isolate listener failures */ }
    }
  }

  request(event, params = {}, timeoutMs = 5000) {
    const ticket = this.ticket++;
    const payload = { event, ...params, ticket };
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        this.pending.delete(ticket);
        reject(new Error(`${event} timed out (ticket ${ticket})`));
      }, timeoutMs);
      this.pending.set(ticket, { event, resolve, reject, timer });
      this.ws.send(JSON.stringify(payload));
    });
  }

  send(event, params = {}) {
    this.ws.send(JSON.stringify({ event, ...params }));
  }

  onEvent(listener) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  async readBytes(address, size, replacements = true) {
    const response = await this.request('memory.read', { address: address >>> 0, size, replacements });
    return Buffer.from(response.base64, 'base64');
  }

  async readU32(address) {
    const bytes = await this.readBytes(address, 4, false);
    return bytes.readUInt32LE(0);
  }

  async close() {
    if (!this.ws || this.ws.readyState === WebSocket.CLOSED) return;
    await new Promise(resolve => {
      const timer = setTimeout(resolve, 1000);
      this.ws.addEventListener('close', () => {
        clearTimeout(timer);
        resolve();
      }, { once: true });
      this.ws.close(1000, 'HP downstream probe complete');
    });
  }
}

function flattenRegisters(response) {
  const registers = {};
  for (const category of response.categories || []) {
    const names = category.registerNames || [];
    const uints = category.uintValues || [];
    const floats = category.floatValues || [];
    for (let index = 0; index < names.length; index++) {
      registers[names[index]] = {
        uint: uints[index] === undefined ? null : (uints[index] >>> 0),
        float: floats[index] === undefined || floats[index] === null ? null : Number(floats[index]),
        category: category.name,
      };
    }
  }
  return registers;
}

function registerValue(registers, name) {
  return registers[name]?.uint ?? null;
}

function serializeRegister(register) {
  if (!register) return null;
  return {
    raw: hex(register.uint),
    uint: register.uint,
    int: Number.isInteger(register.uint) ? (register.uint | 0) : null,
    float: Number.isFinite(register.float) ? register.float : null,
    category: register.category,
  };
}

function serializeRegisters(registers) {
  return Object.fromEntries(SELECTED_REGISTERS.map(name => [name, serializeRegister(registers[name])]));
}

function looksLikeUserPointer(value, size = 1) {
  return Number.isInteger(value) && value >= 0x08000000 && value + size <= 0x0A000000;
}

async function safeReadBytes(client, address, size, replacements = true) {
  try {
    return await client.readBytes(address, size, replacements);
  } catch {
    return null;
  }
}

function decodeWords(buffer) {
  const words = [];
  for (let offset = 0; offset + 4 <= buffer.length; offset += 4) {
    const uint = buffer.readUInt32LE(offset);
    words.push({
      offset: hex(offset, 2),
      raw: hex(uint),
      uint,
      int: buffer.readInt32LE(offset),
      float: buffer.readFloatLE(offset),
    });
  }
  return words;
}

function descriptorSideId(pointer) {
  if (!Number.isInteger(pointer)) return null;
  const difference = pointer - DESCRIPTOR_TABLE;
  if (difference < 0 || difference % 0x10 !== 0) return null;
  const id = difference / 0x10;
  return id >= 0 && id <= 0x48 ? id : null;
}

function preDelayHeight(registers) {
  return {
    value: registers.f0?.float ?? null,
    source: 'f0 at the JAL instruction; the height conversion is complete and the delay-slot store has not executed',
  };
}

function decodePacket(buffer, registers, stage, site) {
  const readFloat = offset => buffer.length >= offset + 4 ? buffer.readFloatLE(offset) : null;
  const x = readFloat(0x00);
  const y = readFloat(0x04);
  const z = readFloat(0x08);
  const width = readFloat(0x18);
  const storedHeight = readFloat(0x1C);
  const orientation = readFloat(0x20);
  const preHeight = preDelayHeight(registers);
  const height = stage === 'callsite-pre-delay' ? preHeight.value : storedHeight;
  const resource = registerValue(registers, 'a1');
  const descriptor = registerValue(registers, 'a3');
  const sideId = descriptorSideId(descriptor);
  const xRegion = x < 240 ? 'left' : x > 240 ? 'right' : 'center';
  const orientationSign = orientation < 0 ? 'negative' : orientation > 0 ? 'positive' : 'zero';
  const hpOwnerLayerTuple = (
    (resource === 0x0E && sideId === 8 && floatEqual(orientation, -1)) ||
    (resource === 0x0D && sideId === 6 && floatEqual(orientation, -1)) ||
    (resource === 0x0E && sideId === 9 && floatEqual(orientation, 1)) ||
    (resource === 0x0D && sideId === 7 && floatEqual(orientation, 1))
  );
  const hpControlMatch = Boolean(
    floatEqual(y, 21) && floatEqual(z, 1000) &&
    hpOwnerLayerTuple && floatEqual(height, 32)
  );

  return {
    address: hex(registerValue(registers, 'a0')),
    bytesHex: buffer.toString('hex'),
    words: decodeWords(buffer),
    fields: {
      x, y, z, width, height,
      storedHeight,
      heightSource: stage === 'callsite-pre-delay' ? preHeight.source : 'packet+0x1C (delay slot executed)',
      orientation,
      resource,
      resourceHex: hex(resource),
      descriptor: hex(descriptor),
      sideId,
      xRegion,
      orientationSign,
      hpControlMatch,
    },
  };
}

function jumpTarget(site, instruction) {
  return ((((site + 4) >>> 0) & 0xF0000000) | ((instruction & 0x03FFFFFF) << 2)) >>> 0;
}

async function readRuntimeParameters(client) {
  const result = {};
  for (const [address, name, type] of V120_RUNTIME_PARAMETERS) {
    const bytes = await client.readBytes(address, 4);
    result[name] = {
      address: hex(address),
      raw: hex(bytes.readUInt32LE(0)),
      value: type === 'float' ? bytes.readFloatLE(0) : bytes.readUInt32LE(0),
    };
  }
  const scale = result.horizontalScale.value;
  result.detectedAspect = Number.isFinite(scale) && scale !== 0 ? (16 / 9) / scale : null;
  return result;
}

async function verifyRuntime(client, mode) {
  const gameStatus = await client.request('game.status');
  if (!gameStatus.game) throw new Error('No game is running in PPSSPP. Start Tekken 6 first.');
  if (gameStatus.game.id !== EXPECTED_GAME_ID) {
    throw new Error(`Wrong game: expected ${EXPECTED_GAME_ID}, got ${gameStatus.game.id} (${gameStatus.game.title || 'unknown title'})`);
  }

  const moduleResponse = await client.request('hle.module.list');
  const modules = moduleResponse.modules || [];
  const pluginModules = modules.filter(module => /Tekken6Ultrawide/i.test(module.name || ''));
  const siteWords = [];

  if (mode === 'stock') {
    if (pluginModules.length) throw new Error(`STOCK validation failed: plugin module loaded (${pluginModules.map(module => module.name).join(', ')}).`);
    const mismatches = [];
    for (const [address, expected, label] of [...STOCK_CHECKS, ...BREAKPOINT_SHAPE_CHECKS]) {
      const actual = await client.readU32(address);
      siteWords.push({ address: hex(address), label, expected: hex(expected), actual: hex(actual) });
      if (actual !== (expected >>> 0)) mismatches.push({ address, expected, actual, label });
    }
    if (mismatches.length) {
      for (const mismatch of mismatches) {
        console.error(`  ${mismatch.label}: ${hex(mismatch.address)} expected ${hex(mismatch.expected)}, got ${hex(mismatch.actual)}`);
      }
      throw new Error('STOCK validation failed: code differs from the documented ULUS10466 stock image. Disable plugins/CWCheats and restart Tekken.');
    }
    return { gameStatus, modules, siteWords, mode, plugin: null, runtimeParameters: null };
  }

  if (pluginModules.length !== 1) {
    throw new Error(`V1.2.0 validation failed: expected exactly one Tekken6Ultrawide module, found ${pluginModules.length}.`);
  }
  const plugin = pluginModules[0];
  if (plugin.isActive === false) throw new Error('V1.2.0 validation failed: Tekken6Ultrawide module is not active.');
  const moduleSpan = plugin.size >>> 0;
  const minimumSignatureSpan = V120_RELEASE.downstreamSignatureOffset + V120_RELEASE.downstreamSignatureSize;
  if (moduleSpan < minimumSignatureSpan) {
    throw new Error(
      `V1.2.0 validation failed: PPSSPP module span ${hex(moduleSpan)} does not cover ` +
      `the release signature ending at module offset ${hex(minimumSignatureSpan)}.`,
    );
  }

  for (const [address, expected, label] of BREAKPOINT_SHAPE_CHECKS) {
    const actual = await client.readU32(address);
    siteWords.push({ address: hex(address), label, expected: hex(expected), actual: hex(actual) });
    if (actual !== (expected >>> 0)) {
      throw new Error(`V1.2.0 validation failed: ${label} at ${hex(address)} expected ${hex(expected)}, got ${hex(actual)}.`);
    }
  }

  const hookMismatches = [];
  for (const expectedHook of V120_HOOKS) {
    const actual = await client.readU32(expectedHook.address);
    const opcode = actual >>> 26;
    const target = jumpTarget(expectedHook.address, actual);
    const expectedTarget = ((plugin.address >>> 0) + expectedHook.targetOffset) >>> 0;
    siteWords.push({
      address: hex(expectedHook.address),
      label: expectedHook.label,
      actual: hex(actual),
      opcode,
      target: hex(target),
      expectedTarget: hex(expectedTarget),
    });
    if (opcode !== expectedHook.opcode || target !== expectedTarget) {
      hookMismatches.push({ ...expectedHook, actual, opcode, target, expectedTarget });
    }
  }
  if (hookMismatches.length) {
    for (const mismatch of hookMismatches) {
      console.error(`  ${mismatch.label}: word=${hex(mismatch.actual)} opcode=${mismatch.opcode} target=${hex(mismatch.target)} expected=${hex(mismatch.expectedTarget)}`);
    }
    throw new Error('V1.2.0 validation failed: live hook targets do not match the released v1.2.0 wrapper offsets.');
  }

  const signatureAddress = ((plugin.address >>> 0) + V120_RELEASE.downstreamSignatureOffset) >>> 0;
  const signatureBytes = await client.readBytes(signatureAddress, V120_RELEASE.downstreamSignatureSize, false);
  const signatureHash = crypto.createHash('sha256').update(signatureBytes).digest('hex');
  if (signatureHash !== V120_RELEASE.downstreamSignatureSha256) {
    throw new Error(`V1.2.0 validation failed: downstream wrapper signature ${signatureHash} does not match released v1.2.0.`);
  }

  const runtimeParameters = await readRuntimeParameters(client);
  return {
    gameStatus,
    modules,
    siteWords,
    mode,
    plugin,
    runtimeParameters,
    releaseSignature: {
      releasePrxSha256: V120_RELEASE.prxSha256,
      releaseElfLoadFileSize: V120_RELEASE.elfLoadFileSize,
      releaseElfLoadMemorySize: V120_RELEASE.elfLoadMemorySize,
      ppssppReportedModuleSpan: moduleSpan,
      knownPpssppModuleSpan: V120_RELEASE.knownPpssppModuleSpan,
      downstreamAddress: hex(signatureAddress),
      downstreamSize: V120_RELEASE.downstreamSignatureSize,
      downstreamSha256: signatureHash,
    },
  };
}

function rounded(value, places = 4) {
  if (!Number.isFinite(value)) return null;
  const factor = 10 ** places;
  return Math.round(value * factor) / factor;
}

function numberText(value) {
  return Number.isFinite(value) ? value.toFixed(3) : 'null';
}

function packetSignature(pathLabel, packet) {
  const fields = packet.fields;
  return JSON.stringify([
    pathLabel,
    fields.resource,
    fields.sideId,
    rounded(fields.x),
    rounded(fields.y),
    rounded(fields.z),
    rounded(fields.width),
    rounded(fields.height),
    rounded(fields.orientation),
  ]);
}

function packetIdentitySignature(pathLabel, packet) {
  const fields = packet.fields;
  return JSON.stringify([
    pathLabel,
    fields.resource,
    fields.sideId,
    rounded(fields.y),
    rounded(fields.z),
    rounded(fields.height),
    rounded(fields.orientation),
  ]);
}

function compactPacketFields(fields) {
  return {
    x: fields.x,
    y: fields.y,
    z: fields.z,
    width: fields.width,
    height: fields.height,
    orientation: fields.orientation,
    resource: fields.resource,
    resourceHex: fields.resourceHex,
    descriptor: fields.descriptor,
    sideId: fields.sideId,
    xRegion: fields.xRegion,
    orientationSign: fields.orientationSign,
    hpControlMatch: fields.hpControlMatch,
  };
}

class ProbeRunner {
  constructor(client, output) {
    this.client = client;
    this.output = output;
    this.wrapperSite = output.mode === 'v120' ? {
      label: 'v120-downstream-wrapper',
      address: ((output.metadata.plugin.address >>> 0) + V120_RELEASE.downstreamWrapperOffset) >>> 0,
    } : null;
    this.gaugeWrapperSite = output.mode === 'v120' ? {
      label: 'v120-gauge-wrapper',
      address: ((output.metadata.plugin.address >>> 0) + V120_RELEASE.gaugeWrapperOffset) >>> 0,
    } : null;
    // Stock traps at the original JAL instructions.  In v1.2.0 those
    // instructions are runtime-patched, and PPSSPP may keep executing their
    // already-compiled JIT blocks without delivering an execution-breakpoint
    // event at the patched callsite.  The verified wrapper entry is the exact
    // equivalent downstream boundary after the JAL delay slot; RA recovers
    // which of the two callsites dispatched the packet.
    this.targetBreakpointSites = this.wrapperSite ? [this.wrapperSite] : [SITES.sharedA, SITES.sharedB];
    this.capture = null;
    this.captureBusy = false;
    this.pendingPair = null;
    this.pendingGaugeInput = null;
    this.pendingGaugeTransform = null;
    this.ownedBreakpoints = new Set();
    this.nextSampleId = 1;
    this.unsubscribe = client.onEvent(message => void this.#onEvent(message));
  }

  async #onEvent(message) {
    if (!this.capture || this.captureBusy || message.event !== 'cpu.stepping') return;
    const candidates = [
      message.hit?.breakpoint?.start,
      message.hit?.address,
      message.relatedAddress,
      message.pc,
    ].filter(Number.isInteger).map(address => address >>> 0);

    const targetSite = this.targetBreakpointSites.find(site => candidates.includes(site.address));
    const atGaugeWrapper = this.gaugeWrapperSite && candidates.includes(this.gaugeWrapperSite.address);
    const atCanary = candidates.includes(SITES.canary.address);
    const atSubmit = candidates.includes(SITES.stockSubmit.address);
    if (!targetSite && !atGaugeWrapper && !atCanary && !atSubmit) return;

    this.captureBusy = true;
    try {
      if (atGaugeWrapper) await this.#handleGaugeInput(message);
      else if (atCanary) await this.#handleCanary(message);
      else if (targetSite) await this.#handleCallsite(message, targetSite);
      else await this.#handleSubmit(message);
    } catch (error) {
      this.output.errors.push({ at: new Date().toISOString(), message: error.message });
      console.error(`  Capture error: ${error.message}`);
      this.capture.failure ||= `capture error: ${error.message}`;
      await this.#finish('capture error');
    } finally {
      try { this.client.send('cpu.resume'); } catch { /* connection may be closing */ }
      this.captureBusy = false;
    }
  }

  async #handleCanary(stepMessage) {
    const regsResponse = await this.client.request('cpu.getAllRegs');
    const registers = flattenRegisters(regsResponse);
    if (!this.capture.canary) {
      this.capture.canary = {
        stoppedPc: hex(registerValue(registers, 'pc') ?? stepMessage.pc),
        a0: hex(registerValue(registers, 'a0')),
        a1: hex(registerValue(registers, 'a1')),
        f12: serializeRegister(registers.f12),
        ticks: stepMessage.ticks ?? null,
      };
      this.output.healthCheck = this.capture.canary;
      console.log(`  CANARY PASS 0x08928FF4 executed (a1=${this.capture.canary.a1}, f12=${registers.f12?.float ?? 'null'})`);

      // Re-add the active downstream target breakpoint(s) while the CPU is
      // stopped. PPSSPP performs the mutation on the CPU thread, which gives
      // the JIT a synchronized refresh point.
      const synchronizedSites = [...this.targetBreakpointSites];
      if (this.gaugeWrapperSite) synchronizedSites.push(this.gaugeWrapperSite);
      for (const site of synchronizedSites) {
        await this.client.request('cpu.breakpoint.add', { address: site.address, enabled: true, log: false });
        this.ownedBreakpoints.add(site.address);
      }
    }

    if (this.pendingGaugeInput) {
      const outputResource = registerValue(registers, 'a1');
      const input = this.pendingGaugeInput;
      const inputWidth = input.f12?.float;
      const outputWidth = registers.f12?.float;
      const transform = {
        id: `G${String(this.capture.gaugeTransforms.length + 1).padStart(2, '0')}`,
        input,
        output: {
          pc: hex(registerValue(registers, 'pc') ?? stepMessage.pc),
          resource: outputResource,
          resourceHex: hex(outputResource),
          f12: serializeRegister(registers.f12),
          ticks: stepMessage.ticks ?? null,
        },
        resourceMatches: outputResource === input.resource,
        widthRatio: Number.isFinite(inputWidth) && inputWidth !== 0 && Number.isFinite(outputWidth)
          ? outputWidth / inputWidth
          : null,
      };
      this.capture.gaugeTransforms.push(transform);
      this.output.gaugeTransforms.push(transform);
      this.pendingGaugeTransform = transform.resourceMatches ? transform : null;
      this.pendingGaugeInput = null;
      console.log(
        `  GAUGE ${transform.id} res=${transform.output.resourceHex} ` +
        `W ${numberText(inputWidth)} -> ${numberText(outputWidth)} ` +
        `ratio=${Number.isFinite(transform.widthRatio) ? transform.widthRatio.toFixed(9) : 'null'}` +
        `${transform.resourceMatches ? '' : ' [RESOURCE-MISMATCH]'}`,
      );
    }

    // Stock only uses this as a one-shot breakpoint-health canary.  In v1.2.0
    // it remains armed to pair every gauge-wrapper input with its renderer
    // entry output during the same execution.
    if (!this.gaugeWrapperSite) await this.#removeBreakpoint(SITES.canary.address);
  }

  async #handleGaugeInput(stepMessage) {
    const regsResponse = await this.client.request('cpu.getAllRegs');
    const registers = flattenRegisters(regsResponse);
    const resource = registerValue(registers, 'a1');
    this.pendingGaugeInput = {
      pc: hex(registerValue(registers, 'pc') ?? stepMessage.pc),
      ra: hex(registerValue(registers, 'ra')),
      sp: hex(registerValue(registers, 'sp')),
      resource,
      resourceHex: hex(resource),
      f12: serializeRegister(registers.f12),
      a0: hex(registerValue(registers, 'a0')),
      a1: hex(resource),
      a2: hex(registerValue(registers, 'a2')),
      a3: hex(registerValue(registers, 'a3')),
      t1: hex(registerValue(registers, 't1')),
      s0: hex(registerValue(registers, 's0')),
      ticks: stepMessage.ticks ?? null,
    };
  }

  async #handleCallsite(stepMessage, breakpointSite) {
    const regsResponse = await this.client.request('cpu.getAllRegs');
    const registers = flattenRegisters(regsResponse);
    const ra = registerValue(registers, 'ra');
    const callsite = this.wrapperSite
      ? [SITES.sharedA, SITES.sharedB].find(site => site.expectedReturn === ra)
      : breakpointSite;
    if (!callsite) {
      throw new Error(`V1.2.0 wrapper entry has an unexpected RA ${hex(ra)}; cannot assign D56C/D5B0 safely.`);
    }
    if (this.pendingPair) throw new Error(`Reached ${callsite.label} while waiting for the preceding submit pair.`);

    const packetAddress = registerValue(registers, 'a0');
    if (!looksLikeUserPointer(packetAddress, PACKET_BYTES)) {
      throw new Error(`${callsite.label} a0 is not a readable packet pointer: ${hex(packetAddress)}`);
    }

    const packetBytes = await this.client.readBytes(packetAddress, PACKET_BYTES);
    const entryStage = this.wrapperSite ? 'downstream-wrapper-entry-post-delay' : 'callsite-pre-delay';
    const packet = decodePacket(packetBytes, registers, entryStage, breakpointSite);
    const key = packetSignature(callsite.label, packet);
    const identityKey = packetIdentitySignature(callsite.label, packet);
    let identity = this.capture.identities.get(identityKey);
    if (!identity) {
      identity = {
        id: `I${String(this.capture.identities.size + 1).padStart(2, '0')}`,
        key: identityKey,
        path: callsite.label,
        count: 0,
        clusterIds: [],
        invariantFields: {
          resource: packet.fields.resource,
          resourceHex: packet.fields.resourceHex,
          descriptor: packet.fields.descriptor,
          sideId: packet.fields.sideId,
          y: packet.fields.y,
          z: packet.fields.z,
          height: packet.fields.height,
          orientation: packet.fields.orientation,
          xRegion: packet.fields.xRegion,
          orientationSign: packet.fields.orientationSign,
          hpControlMatch: packet.fields.hpControlMatch,
        },
      };
      this.capture.identities.set(identityKey, identity);
    }
    identity.count++;
    let cluster = this.capture.clusters.get(key);
    const isNew = !cluster;
    if (!cluster) {
      cluster = {
        id: `C${String(this.capture.clusters.size + 1).padStart(2, '0')}`,
        identityId: identity.id,
        key,
        path: callsite.label,
        count: 0,
        firstRawHit: this.capture.rawHits.length + 1,
        pre: compactPacketFields(packet.fields),
        post: null,
        delta: null,
        sampleId: null,
      };
      this.capture.clusters.set(key, cluster);
      identity.clusterIds.push(cluster.id);
    }
    cluster.count++;

    const fields = packet.fields;
    const matchedGaugeTransform = fields.hpControlMatch &&
      this.pendingGaugeTransform?.output.resource === fields.resource
      ? this.pendingGaugeTransform
      : null;
    const rawHit = {
      index: this.capture.rawHits.length + 1,
      identityId: identity.id,
      clusterId: cluster.id,
      path: callsite.label,
      packetAddress: hex(packetAddress),
      fields: compactPacketFields(packet.fields),
      registers: serializeRegisters(registers),
      ticks: stepMessage.ticks ?? null,
      breakpointSequence: stepMessage.sequence ?? null,
      gaugeTransformId: null,
    };
    if (matchedGaugeTransform) {
      rawHit.gaugeTransformId = matchedGaugeTransform.id;
      cluster.gaugeTransformIds ||= [];
      if (!cluster.gaugeTransformIds.includes(matchedGaugeTransform.id)) {
        cluster.gaugeTransformIds.push(matchedGaugeTransform.id);
      }
      this.pendingGaugeTransform = null;
    }
    this.capture.rawHits.push(rawHit);
    this.output.rawHits.push(rawHit);

    console.log(
      `  RAW #${String(rawHit.index).padStart(2)} ${identity.id}/${cluster.id}${isNew ? ' NEW' : '    '} ${callsite.label} ` +
      `res=${fields.resourceHex} sid=${fields.sideId ?? '-'} ` +
      `X=${numberText(fields.x)} Y=${numberText(fields.y)} Z=${numberText(fields.z)} ` +
      `W=${numberText(fields.width)} H=${numberText(fields.height)} O=${numberText(fields.orientation)}` +
      `${fields.hpControlMatch ? ' [HP-CONTROL]' : ''}`,
    );

    if (!isNew) {
      if (this.capture.rawHits.length >= this.capture.maxHits) await this.#finish('raw hit limit reached');
      return;
    }

    const snapshot = await this.#buildSnapshot(stepMessage, regsResponse, registers, packetBytes, entryStage, breakpointSite);
    const sample = {
      id: this.nextSampleId++,
      clusterId: cluster.id,
      runtimeMode: this.output.mode,
      sceneLabel: this.output.sceneLabel,
      measurementStage: `${entryStage} -> stock-submit-entry-post-delay`,
      path: callsite.label,
      breakpointAddress: hex(breakpointSite.address),
      callsiteAddress: hex(callsite.callAddress),
      expectedSubmitReturn: hex(callsite.expectedReturn),
      delaySlot: {
        address: hex(callsite.callAddress + 4),
        effect: 'swc1 f0,0x2C(sp); packet+0x1C height becomes valid before wrapper/stock-submit entry',
        callsiteStage: this.wrapperSite ? 'executed before wrapper entry' : 'not executed',
        submitStage: 'executed',
      },
      callsite: snapshot,
      submit: null,
      pairingMismatches: [],
      upstreamGaugeTransform: matchedGaugeTransform,
    };
    cluster.sampleId = sample.id;

    const stopAfterPair = this.capture.rawHits.length >= this.capture.maxHits;
    if (stopAfterPair) {
      for (const site of this.targetBreakpointSites) await this.#removeBreakpoint(site.address);
    }
    await this.#addBreakpoint(SITES.stockSubmit.address);
    this.pendingPair = { sample, cluster, packetAddress, callsite, stopAfterPair };
  }

  async #handleSubmit(stepMessage) {
    if (!this.pendingPair) {
      await this.#removeBreakpoint(SITES.stockSubmit.address);
      return;
    }

    const regsResponse = await this.client.request('cpu.getAllRegs');
    const registers = flattenRegisters(regsResponse);
    const packetAddress = registerValue(registers, 'a0');
    const ra = registerValue(registers, 'ra');
    const pending = this.pendingPair;

    if (packetAddress !== pending.packetAddress || ra !== pending.callsite.expectedReturn) {
      pending.sample.pairingMismatches.push({ packetAddress: hex(packetAddress), ra: hex(ra) });
      if (pending.sample.pairingMismatches.length >= 8) {
        throw new Error(`Could not pair ${pending.callsite.label} packet ${hex(pending.packetAddress)} with stock-submit.`);
      }
      return;
    }

    const packetBytes = await this.client.readBytes(packetAddress, PACKET_BYTES);
    pending.sample.submit = await this.#buildSnapshot(stepMessage, regsResponse, registers, packetBytes, 'submit-post-delay', SITES.stockSubmit);
    await this.#removeBreakpoint(SITES.stockSubmit.address);
    this.pendingPair = null;
    this.output.samples.push(pending.sample);

    const before = pending.sample.callsite.packet.fields;
    const after = pending.sample.submit.packet.fields;
    pending.cluster.post = compactPacketFields(after);
    pending.cluster.delta = {
      x: after.x - before.x,
      width: after.width - before.width,
      orientation: after.orientation - before.orientation,
    };
    console.log(
      `       ${pending.cluster.id} POST X=${numberText(after.x)} W=${numberText(after.width)} ` +
      `O=${numberText(after.orientation)} H=${numberText(after.height)}`,
    );

    if (pending.stopAfterPair) await this.#finish('raw hit limit reached');
  }

  async #buildSnapshot(stepMessage, regsResponse, registers, packetBytes, stage, site) {
    const pc = registerValue(registers, 'pc') ?? stepMessage.pc;
    const sp = registerValue(registers, 'sp');
    const ra = registerValue(registers, 'ra');
    const stackBytes = looksLikeUserPointer(sp, STACK_BYTES) ? await safeReadBytes(this.client, sp, STACK_BYTES) : null;
    const pcBytes = Number.isInteger(pc) && pc >= 0x10 ? await safeReadBytes(this.client, pc - 0x10, 0x40, false) : null;
    const raBytes = Number.isInteger(ra) && ra >= 0x10 ? await safeReadBytes(this.client, ra - 0x10, 0x30, false) : null;
    const backtrace = await this.client.request('hle.backtrace').catch(error => ({ error: error.message }));
    const cpuStatus = await this.client.request('cpu.status').catch(() => null);

    return {
      stage,
      site: site.label,
      siteAddress: hex(site.address),
      stoppedPc: hex(pc),
      registers: serializeRegisters(registers),
      fpu: {
        f0: serializeRegister(registers.f0),
        f12: serializeRegister(registers.f12),
      },
      stack: stackBytes ? {
        address: hex(sp),
        size: stackBytes.length,
        bytesHex: stackBytes.toString('hex'),
        words: decodeWords(stackBytes),
      } : null,
      packet: decodePacket(packetBytes, registers, stage, site),
      backtrace,
      pcWindowHex: pcBytes?.toString('hex') ?? null,
      raWindowHex: raBytes?.toString('hex') ?? null,
      ticks: stepMessage.ticks ?? cpuStatus?.ticks ?? null,
      emulatedUs: cpuStatus?.us ?? null,
      rawRegisterCategories: regsResponse.categories || [],
    };
  }

  async #addBreakpoint(address) {
    if (this.ownedBreakpoints.has(address)) return;
    await this.client.request('cpu.breakpoint.add', { address, enabled: true, log: false });
    this.ownedBreakpoints.add(address);
  }

  async #removeBreakpoint(address) {
    if (!this.ownedBreakpoints.has(address)) return;
    try { await this.client.request('cpu.breakpoint.remove', { address }); } catch { /* best effort */ }
    this.ownedBreakpoints.delete(address);
  }

  async #finish(reason) {
    if (!this.capture || this.capture.finished) return;
    this.capture.finished = true;
    this.capture.finishReason = reason;
    const captureAddresses = [...this.targetBreakpointSites.map(site => site.address), SITES.canary.address];
    if (this.gaugeWrapperSite) captureAddresses.push(this.gaugeWrapperSite.address);
    for (const address of captureAddresses) {
      await this.#removeBreakpoint(address);
    }
    if (!this.pendingPair) await this.#removeBreakpoint(SITES.stockSubmit.address);
    this.capture.resolveCompletion(reason);
  }

  async #pauseForAtomicArm() {
    const stopped = new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        unsubscribe();
        reject(new Error('PPSSPP did not enter debugger stepping state before breakpoint installation.'));
      }, 2500);
      const unsubscribe = this.client.onEvent(message => {
        if (message.event !== 'cpu.stepping') return;
        clearTimeout(timer);
        unsubscribe();
        resolve();
      });
    });
    this.client.send('cpu.stepping');
    await stopped;
  }

  async runDiscovery({ maxHits, timeoutMs }) {
    const existing = await this.client.request('cpu.breakpoint.list');
    const existingAddresses = new Set((existing.breakpoints || []).map(breakpoint => breakpoint.address >>> 0));
    const probeAddresses = [...this.targetBreakpointSites.map(site => site.address), SITES.canary.address, SITES.stockSubmit.address];
    if (this.gaugeWrapperSite) probeAddresses.push(this.gaugeWrapperSite.address);
    const overlaps = probeAddresses.filter(address => existingAddresses.has(address));
    if (overlaps.length) throw new Error(`Remove existing PPSSPP breakpoints at ${overlaps.map(hex).join(', ')} before running this probe.`);

    let resolveCompletion;
    const completion = new Promise(resolve => { resolveCompletion = resolve; });
    this.capture = {
      startedAt: new Date().toISOString(),
      maxHits,
      rawHits: [],
      identities: new Map(),
      clusters: new Map(),
      canary: null,
      gaugeTransforms: [],
      failure: null,
      finished: false,
      finishReason: null,
      resolveCompletion,
    };

    console.log('\nFreezing the CPU briefly so all breakpoints are armed atomically...');
    await this.#pauseForAtomicArm();
    for (const site of this.targetBreakpointSites) await this.#addBreakpoint(site.address);
    if (this.gaugeWrapperSite) await this.#addBreakpoint(this.gaugeWrapperSite.address);
    await this.#addBreakpoint(SITES.canary.address);
    console.log(`CAPTURING the first ${maxHits} raw shared-call hits (no HUD-family filter)...`);
    this.client.send('cpu.resume');

    const healthTimer = setTimeout(() => {
      if (!this.capture || this.capture.canary || this.capture.rawHits.length) return;
      this.capture.failure = 'No gauge canary or shared-call breakpoint fired. The game may be paused/not in an active fight, or PPSSPP execution breakpoints are unhealthy.';
      void this.#finish('breakpoint health timeout');
    }, BREAKPOINT_HEALTH_MS);
    const targetTimer = setTimeout(() => {
      if (!this.capture || this.capture.rawHits.length || !this.capture.canary) return;
      this.capture.failure = this.wrapperSite
        ? 'The upstream HP canary fired but the verified v1.2.0 downstream wrapper entry did not. This is a target-breakpoint/JIT failure, not evidence about HUD routing.'
        : 'The upstream HP canary fired but D56C/D5B0 did not. This is a target-breakpoint/JIT failure, not evidence about HUD routing.';
      void this.#finish('target breakpoint timeout');
    }, TARGET_AFTER_CANARY_MS);
    const overallTimer = setTimeout(() => {
      if (!this.capture || this.capture.finished) return;
      const hasHpControl = [...this.capture.clusters.values()].some(cluster => cluster.pre.hpControlMatch);
      if (!this.capture.rawHits.length || !hasHpControl) {
        this.capture.failure ||= `Capture timed out after ${timeoutMs} ms before a proven HP control packet was observed.`;
      }
      void this.#finish(hasHpControl ? 'timebox elapsed after valid HUD burst' : 'overall timeout');
    }, timeoutMs);

    await completion;
    clearTimeout(healthTimer);
    clearTimeout(targetTimer);
    clearTimeout(overallTimer);
    while (this.captureBusy) await sleep(20);
    for (const address of [...this.ownedBreakpoints]) await this.#removeBreakpoint(address);
    this.pendingPair = null;
    this.pendingGaugeInput = null;
    this.pendingGaugeTransform = null;

    const capture = this.capture;
    capture.endedAt = new Date().toISOString();
    const identities = [...capture.identities.values()];
    const clusters = [...capture.clusters.values()];
    const hpControls = clusters.filter(cluster => cluster.pre.hpControlMatch);
    const matchedGaugeTransforms = capture.gaugeTransforms.filter(transform => transform.resourceMatches);
    const attachedGaugeTransformIds = new Set(
      capture.rawHits.map(hit => hit.gaugeTransformId).filter(Boolean),
    );
    const valid = !capture.failure && capture.rawHits.length > 0 && hpControls.length > 0;
    this.output.capture = {
      startedAt: capture.startedAt,
      endedAt: capture.endedAt,
      finishReason: capture.finishReason,
      failure: capture.failure,
      valid,
      rawHitCount: capture.rawHits.length,
      identityCount: identities.length,
      clusterCount: clusters.length,
      hpControlClusterCount: hpControls.length,
      gaugeTransformCount: capture.gaugeTransforms.length,
      matchedGaugeTransformCount: matchedGaugeTransforms.length,
      attachedGaugeTransformCount: attachedGaugeTransformIds.size,
      gaugeTraceComplete: !this.gaugeWrapperSite || attachedGaugeTransformIds.size > 0,
    };
    this.output.identities = identities;
    this.output.clusters = clusters;

    console.log('\nSTRUCTURAL IDENTITY SUMMARY (X and width excluded so animated HP values stay together):');
    for (const identity of identities) {
      const fields = identity.invariantFields;
      console.log(
        `  ${identity.id} count=${String(identity.count).padStart(2)} ${identity.path} ` +
        `res=${fields.resourceHex} sid=${fields.sideId ?? '-'} x-region=${fields.xRegion} ` +
        `Y=${numberText(fields.y)} Z=${numberText(fields.z)} H=${numberText(fields.height)} ` +
        `O=${numberText(fields.orientation)} clusters=${identity.clusterIds.join(',')}` +
        `${fields.hpControlMatch ? ' [HP-CONTROL]' : ''}`,
      );
    }

    console.log('\nRAW VALUE CLUSTERS (descriptive IDs only; no side-strip/rank labels are assigned):');
    for (const cluster of clusters) {
      const fields = cluster.pre;
      console.log(
        `  ${cluster.identityId}/${cluster.id} count=${String(cluster.count).padStart(2)} ${cluster.path} ` +
        `res=${fields.resourceHex} sid=${fields.sideId ?? '-'} x-region=${fields.xRegion} ` +
        `X=${numberText(fields.x)} Y=${numberText(fields.y)} Z=${numberText(fields.z)} ` +
        `W=${numberText(fields.width)} H=${numberText(fields.height)} O=${numberText(fields.orientation)}` +
        `${fields.hpControlMatch ? ' [HP-CONTROL]' : ''}`,
      );
    }

    if (this.gaugeWrapperSite) {
      const expectedScale = this.output.metadata.runtimeParameters?.hpScale?.value;
      const ratios = matchedGaugeTransforms.map(transform => transform.widthRatio).filter(Number.isFinite);
      const maximumScaleError = ratios.length && Number.isFinite(expectedScale)
        ? Math.max(...ratios.map(ratio => Math.abs(ratio - expectedScale)))
        : null;
      console.log(
        `\nGAUGE TRANSFORM PAIRS: ${matchedGaugeTransforms.length} matched input/output pair(s); ` +
        `${attachedGaugeTransformIds.size} attached to downstream HP hit(s); ` +
        `max |ratio-hp_scale|=${Number.isFinite(maximumScaleError) ? maximumScaleError.toExponential(3) : 'null'}.`,
      );
      if (!attachedGaugeTransformIds.size) {
        console.log('GAUGE TRACE INCOMPLETE: downstream packets are valid, but no same-execution gauge input/output pair was trapped.');
      }
    }

    if (!valid) {
      const reason = capture.failure || 'No proven HP control packet was observed, so this run cannot validate target-breakpoint health.';
      console.log(`\nCAPTURE INVALID: ${reason}`);
    } else {
      console.log(`\nCAPTURE VALID: ${capture.rawHits.length} raw hits, ${identities.length} structural identities, ${clusters.length} raw value clusters, ${hpControls.length} proven HP control cluster(s).`);
    }
    this.capture = null;
    return valid;
  }

  async cleanup() {
    while (this.captureBusy) await sleep(20);
    for (const address of [...this.ownedBreakpoints]) await this.#removeBreakpoint(address);
    this.pendingPair = null;
    this.capture = null;
    this.unsubscribe?.();
  }
}

function parseArguments(argv) {
  const args = [...argv];
  if (args.includes('--help') || args.includes('-h')) return { help: true };
  let mode = null;
  let sceneLabel = 'active-battle-hud';
  let maxHits = DEFAULT_MAX_HITS;

  const takeOption = name => {
    const index = args.indexOf(name);
    if (index === -1) return null;
    const value = args[index + 1];
    args.splice(index, 2);
    return value;
  };
  mode = takeOption('--mode');
  sceneLabel = takeOption('--label') ?? sceneLabel;
  const maxHitsText = takeOption('--max-hits');
  if (maxHitsText !== null) maxHits = Number.parseInt(maxHitsText, 10);

  const endpoint = args.shift();
  if (!mode && ['stock', 'v120'].includes(args[0])) mode = args.shift();
  if (
    !endpoint || !['stock', 'v120'].includes(mode) || args.length ||
    !Number.isInteger(maxHits) || maxHits < 8 || maxHits > 64 ||
    !/^[a-z0-9][a-z0-9._-]{0,63}$/i.test(sceneLabel)
  ) {
    throw new Error('Invalid arguments. Run with --help for usage.');
  }
  return { help: false, endpoint, mode, sceneLabel, maxHits };
}

function printUsage() {
  console.log('Usage:');
  console.log('  node tools/research/probes/ppsspp_hp_downstream_ab_probe.mjs <PHONE_IP:PORT> --mode <stock|v120> [--label NAME] [--max-hits 8..64]');
  console.log('');
  console.log('This v2 probe performs one short discovery capture per process. It captures raw D56C/D5B0 traffic without assigning HUD-family labels.');
}

async function main() {
  const options = parseArguments(process.argv.slice(2));
  if (options.help) {
    printUsage();
    return;
  }
  const { endpoint, mode, sceneLabel, maxHits } = options;
  const client = new PPSSPPDebugger(endpoint);
  const rl = createInterface({ input: process.stdin, output: process.stdout });
  const output = {
    format: 'tekken6-hp-downstream-discovery-v2',
    createdAt: new Date().toISOString(),
    endpoint,
    mode,
    sceneLabel,
    runtimeGeneration: mode === 'stock' ? 'stock' : 'released-v1.2.0',
    measurementStage: mode === 'stock'
      ? 'callsite-pre-delay paired with stock-submit-entry-post-delay'
      : 'verified-downstream-wrapper-entry-post-delay paired with stock-submit-entry-post-delay',
    readOnlyGuestMemory: true,
    metadata: {},
    healthCheck: null,
    capture: null,
    rawHits: [],
    gaugeTransforms: [],
    identities: [],
    clusters: [],
    samples: [],
    errors: [],
  };
  let runner;

  try {
    console.log(`Connecting to ${client.url.href}...`);
    await client.connect();
    const version = await client.request('version', { name: 'tekken6-hp-downstream-discovery', version: '2.0' });
    console.log(`Connected: ${version.name} ${version.version} (subprotocol ${REQUIRED_PROTOCOL})`);

    console.log(`Verifying ${mode === 'stock' ? 'stock/no-plugin' : 'released v1.2.0'} runtime...`);
    const verification = await verifyRuntime(client, mode);
    output.metadata.version = version;
    output.metadata.game = verification.gameStatus.game;
    output.metadata.modules = verification.modules;
    output.metadata.siteWords = verification.siteWords;
    output.metadata.plugin = verification.plugin;
    output.metadata.releaseSignature = verification.releaseSignature ?? null;
    output.metadata.runtimeParameters = verification.runtimeParameters;
    console.log(`Game: ${verification.gameStatus.game.title} (${verification.gameStatus.game.id})`);
    console.log(`Runtime validation: ${mode === 'stock' ? 'STOCK' : 'V1.2.0'} PASS`);
    if (verification.releaseSignature) {
      console.log(
        `Module layout: PPSSPP span=${hex(verification.releaseSignature.ppssppReportedModuleSpan)}; ` +
        `release PT_LOAD p_filesz/p_memsz=${hex(verification.releaseSignature.releaseElfLoadFileSize)}/` +
        `${hex(verification.releaseSignature.releaseElfLoadMemorySize)}`,
      );
    }
    if (verification.runtimeParameters) {
      const params = verification.runtimeParameters;
      console.log(
        `Runtime aspect parameters: s=${params.horizontalScale.value.toFixed(9)} ` +
        `aspect=${params.detectedAspect.toFixed(9)} hp_shift=${params.hpShift.value.toFixed(9)} hp_scale=${params.hpScale.value.toFixed(9)}`,
      );
    }

    console.log('\nREAD-ONLY DISCOVERY PROBE: no PSP/game memory is written.');
    console.log('Use an active, unpaused fight. Exact HP percentages do not matter.');
    console.log('After Enter, the probe freezes the CPU immediately, arms all breakpoints together, then captures the first raw packet burst.');
    runner = new ProbeRunner(client, output);
    await rl.question(`Press Enter when scene "${sceneLabel}" is visible: `);
    await runner.runDiscovery({ maxHits, timeoutMs: DEFAULT_TIMEOUT_MS });

    const outputDirectory = path.join(process.cwd(), 'research', 'captures');
    await fs.mkdir(outputDirectory, { recursive: true });
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const outputPath = path.join(outputDirectory, `hp-downstream-discovery-${mode}-${sceneLabel}-${timestamp}.json`);
    await fs.writeFile(outputPath, `${JSON.stringify(output, null, 2)}\n`, 'utf8');

    console.log(`\nCapture saved: ${outputPath}`);
    console.log(`Raw hits: ${output.rawHits.length}; identities: ${output.identities.length}; clusters: ${output.clusters.length}; paired unique samples: ${output.samples.length}`);
    console.log('Paste the complete terminal output first. Keep the JSON unchanged for the later stock/v1.2.0 comparison.');
  } finally {
    try { await runner?.cleanup(); } catch { /* best effort */ }
    await client.close();
    rl.close();
  }
}

main().catch(error => {
  console.error(`\nERROR: ${error.message}`);
  process.exitCode = 1;
});
