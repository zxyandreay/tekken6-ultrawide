#!/usr/bin/env node

import net from 'node:net';
import process from 'node:process';

const EXPECTED_GAME_ID = 'ULUS10466';
const REQUIRED_PROTOCOL = 'debugger.ppsspp.org';
const DEFAULT_ENDPOINT = '192.168.0.101:39100';
const CONNECT_TIMEOUT_MS = 7000;
const EVENT_TIMEOUT_MS = 5000;

class DiagnosticError extends Error {
  constructor(layer, message, cause) {
    super(message, cause ? { cause } : undefined);
    this.name = 'DiagnosticError';
    this.layer = layer;
  }
}

function debuggerUrl(endpoint) {
  const raw = endpoint.trim();
  const withScheme = /^(?:ws|wss):\/\//i.test(raw) ? raw : `ws://${raw}`;
  const url = new URL(withScheme);

  if (url.protocol !== 'ws:' && url.protocol !== 'wss:') {
    throw new DiagnosticError('configuration', `Unsupported URL scheme: ${url.protocol}`);
  }

  const normalizedPath = url.pathname.replace(/\/+$/, '');
  if (!normalizedPath) url.pathname = '/debugger';
  else if (normalizedPath === '/debugger') url.pathname = '/debugger';
  else throw new DiagnosticError('configuration', `Expected endpoint path /debugger, got ${url.pathname}`);

  return url;
}

function describeError(error) {
  if (!error) return 'unknown error';
  const parts = [];
  for (const value of [error.code, error.message, error.cause?.code, error.cause?.message]) {
    if (value && !parts.includes(value)) parts.push(value);
  }
  return parts.join(': ') || String(error);
}

async function checkTcp(url) {
  const port = Number(url.port || (url.protocol === 'wss:' ? 443 : 80));

  await new Promise((resolve, reject) => {
    const socket = net.createConnection({ host: url.hostname, port });
    let settled = false;

    const finish = (error) => {
      if (settled) return;
      settled = true;
      socket.destroy();
      if (error) reject(error);
      else resolve();
    };

    socket.setTimeout(CONNECT_TIMEOUT_MS, () => {
      finish(new DiagnosticError(
        'TCP/network failure',
        `TCP connection timed out after ${CONNECT_TIMEOUT_MS} ms (${url.hostname}:${port})`,
      ));
    });
    socket.once('connect', () => finish());
    socket.once('error', error => {
      finish(new DiagnosticError(
        'TCP/network failure',
        `TCP connection failed (${url.hostname}:${port}): ${describeError(error)}`,
        error,
      ));
    });
  });
}

async function decodeMessageData(data) {
  if (typeof data === 'string') return data;
  if (data instanceof ArrayBuffer) return Buffer.from(data).toString('utf8');
  if (ArrayBuffer.isView(data)) {
    return Buffer.from(data.buffer, data.byteOffset, data.byteLength).toString('utf8');
  }
  if (data && typeof data.text === 'function') return data.text();
  return String(data);
}

class SmokeClient {
  constructor(url) {
    this.url = url;
    this.ws = null;
    this.nextTicket = 1;
    this.pending = new Map();
  }

  async connect() {
    if (typeof WebSocket === 'undefined') {
      throw new DiagnosticError('configuration', 'This smoke test requires Node.js with the global WebSocket API (Node 20+ recommended).');
    }

    await new Promise((resolve, reject) => {
      const ws = new WebSocket(this.url, REQUIRED_PROTOCOL);
      let opened = false;
      let lastError = null;
      let settled = false;

      const finish = (error) => {
        if (settled) return;
        settled = true;
        clearTimeout(timer);
        if (error) reject(error);
        else resolve();
      };

      const timer = setTimeout(() => {
        ws.close();
        finish(new DiagnosticError(
          'WebSocket HTTP upgrade failure',
          `WebSocket upgrade timed out after ${CONNECT_TIMEOUT_MS} ms (${this.url.href})`,
        ));
      }, CONNECT_TIMEOUT_MS);

      ws.addEventListener('open', () => {
        opened = true;
        if (ws.protocol !== REQUIRED_PROTOCOL) {
          ws.close(1002, 'Required subprotocol not selected');
          finish(new DiagnosticError(
            'subprotocol failure',
            `PPSSPP selected ${JSON.stringify(ws.protocol)} instead of ${JSON.stringify(REQUIRED_PROTOCOL)}`,
          ));
          return;
        }
        this.ws = ws;
        finish();
      }, { once: true });

      ws.addEventListener('error', event => {
        lastError = event.error || new Error(event.message || 'WebSocket error event');
        if (!opened) {
          finish(new DiagnosticError(
            'WebSocket HTTP upgrade failure',
            `WebSocket upgrade failed (${this.url.href}): ${describeError(lastError)}`,
            lastError,
          ));
        }
      });

      ws.addEventListener('close', event => {
        if (!opened) {
          const reason = event.reason || describeError(lastError);
          finish(new DiagnosticError(
            'WebSocket HTTP upgrade failure',
            `WebSocket closed before opening: code=${event.code}, reason=${reason}`,
            lastError,
          ));
        }
      });

      ws.addEventListener('message', event => void this.onMessage(event.data));
    });

    this.ws.addEventListener('close', event => {
      const reason = event.reason ? `: ${event.reason}` : '';
      for (const pending of this.pending.values()) {
        clearTimeout(pending.timer);
        pending.reject(new DiagnosticError(
          'WebSocket connected but PPSSPP event timeout',
          `Connection closed while waiting for ${pending.event} (code=${event.code}${reason})`,
        ));
      }
      this.pending.clear();
    }, { once: true });
  }

  async onMessage(data) {
    const raw = await decodeMessageData(data);
    let message;
    try {
      message = JSON.parse(raw);
    } catch {
      console.log(`[broadcast/non-JSON] ${raw}`);
      return;
    }

    if (message.ticket !== undefined && this.pending.has(message.ticket)) {
      const pending = this.pending.get(message.ticket);
      this.pending.delete(message.ticket);
      clearTimeout(pending.timer);
      if (message.event === 'error') {
        pending.reject(new DiagnosticError(
          'WebSocket connected but PPSSPP event error',
          `${pending.event} returned an error: ${message.message || JSON.stringify(message)}`,
        ));
      } else {
        pending.resolve(message);
      }
      return;
    }

    console.log(`[broadcast] ${JSON.stringify(message)}`);
  }

  request(event, params = {}) {
    const ticket = this.nextTicket++;
    const payload = { event, ...params, ticket };

    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        this.pending.delete(ticket);
        reject(new DiagnosticError(
          'WebSocket connected but PPSSPP event timeout',
          `${event} did not answer ticket ${ticket} within ${EVENT_TIMEOUT_MS} ms`,
        ));
      }, EVENT_TIMEOUT_MS);

      this.pending.set(ticket, { event, resolve, reject, timer });
      try {
        this.ws.send(JSON.stringify(payload));
      } catch (error) {
        clearTimeout(timer);
        this.pending.delete(ticket);
        reject(new DiagnosticError(
          'WebSocket connected but PPSSPP event error',
          `Could not send ${event}: ${describeError(error)}`,
          error,
        ));
      }
    });
  }

  async close() {
    if (!this.ws || this.ws.readyState === WebSocket.CLOSED) return;
    await new Promise(resolve => {
      const timer = setTimeout(resolve, 1000);
      this.ws.addEventListener('close', () => {
        clearTimeout(timer);
        resolve();
      }, { once: true });
      this.ws.close(1000, 'Smoke test complete');
    });
  }
}

function printResponse(label, response) {
  console.log(`\n${label}:`);
  console.log(JSON.stringify(response, null, 2));
}

async function main() {
  const endpoint = process.argv[2] || DEFAULT_ENDPOINT;
  const url = debuggerUrl(endpoint);
  const client = new SmokeClient(url);

  console.log(`Endpoint: ${url.href}`);
  console.log(`Required subprotocol: ${REQUIRED_PROTOCOL}`);

  try {
    console.log('\n[1/5] Checking TCP reachability...');
    await checkTcp(url);
    console.log('TCP connection: OK');

    console.log('[2/5] Performing WebSocket HTTP upgrade...');
    await client.connect();
    console.log(`WebSocket connection: OK (protocol=${client.ws.protocol})`);

    console.log('[3/5] Requesting PPSSPP version...');
    const version = await client.request('version', {
      name: 'tekken6-renderer-research',
      version: '1.0',
    });
    printResponse('version response', version);

    console.log('[4/5] Requesting game status...');
    const gameStatus = await client.request('game.status');
    printResponse('game.status response', gameStatus);

    if (!gameStatus.game) {
      throw new DiagnosticError('wrong game', 'PPSSPP is reachable, but no game is running.');
    }
    if (gameStatus.game.id !== EXPECTED_GAME_ID) {
      throw new DiagnosticError(
        'wrong game',
        `Expected ${EXPECTED_GAME_ID} (Tekken 6), got ${gameStatus.game.id || 'unknown ID'} (${gameStatus.game.title || 'unknown title'}).`,
      );
    }

    console.log('[5/5] Requesting CPU status...');
    const cpuStatus = await client.request('cpu.status');
    printResponse('cpu.status response', cpuStatus);

    console.log(`\nSUCCESS: connected to PPSSPP running ${gameStatus.game.title} (${gameStatus.game.id}); CPU status answered.`);
  } finally {
    await client.close();
  }
}

main().catch(error => {
  const layer = error.layer || 'unexpected failure';
  console.error(`\nFAILURE [${layer}]: ${error.message}`);
  process.exitCode = 1;
});
