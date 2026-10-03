import process from 'node:process';
import type { AgentConfig } from './types.js';
import { loadLitecoinConfig } from './litecoin.js';

const num = (key: string, fallback: number) => {
  const v = Number(process.env[key]);
  return Number.isFinite(v) ? v : fallback;
};

export function loadConfig(): AgentConfig {
  return {
    targetCents: num('TIMEPRESSURE_TARGET_CENTS', 1),
    cycleMs: num('TIMEPRESSURE_CYCLE_MS', 60 * 60 * 1000),
    tickMs: num('TIMEPRESSURE_TICK_MS', 10_000),
    dataDir: process.env.TIMEPRESSURE_DATA_DIR ?? '.data',
    model: process.env.TIMEPRESSURE_MODEL ?? 'gpt-5.6',
    apiKey: process.env.OPENAI_API_KEY,
    baseUrl: process.env.OPENAI_BASE_URL ?? 'https://api.openai.com/v1',
    allowNetwork: process.env.TIMEPRESSURE_ALLOW_NETWORK !== 'false',
    litecoin: loadLitecoinConfig(),
  };
}
