import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import type { PersistedState, MemoryEvent, RevenueEvent } from './types.js';

export class Store {
  private readonly file: string;
  constructor(dir: string) { this.file = path.join(dir, 'state.json'); this.dir = dir; }
  private readonly dir: string;
  async init(): Promise<PersistedState> {
    await mkdir(this.dir, { recursive: true });
    try { return JSON.parse(await readFile(this.file, 'utf8')) as PersistedState; }
    catch {
      const now = Date.now();
      const state: PersistedState = { version: 1, createdAt: now, pressure: { cycleStartedAt: now, targetCents: 1, cycleRevenueCents: 0, pressure: 0, status: 'alive', deadline: now + 3600000 }, revenue: [], memory: [], working: { goal: 'Generate legitimate value and record verified revenue.', plan: [] } };
      await this.save(state); return state;
    }
  }
  async save(state: PersistedState) { await writeFile(this.file, JSON.stringify(state, null, 2)); }
  async addMemory(state: PersistedState, event: MemoryEvent) { state.memory.push(event); state.memory = state.memory.slice(-5000); await this.save(state); }
  async addRevenue(state: PersistedState, event: RevenueEvent) { state.revenue.push(event); await this.save(state); }
}
