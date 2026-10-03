import OpenAI from 'openai';
import crypto from 'node:crypto';
import type { AgentConfig, PersistedState, ToolContext } from './types.js';
import { tools } from './tools.js';
import { Store } from './store.js';
import { calculatePressure } from './pressure.js';

export class Agent {
  constructor(private readonly config: AgentConfig, private readonly store: Store, private state: PersistedState) {}
  getState() { return this.state; }
  async tick() {
    this.state.pressure = calculatePressure(Date.now(), this.state.pressure);
    await this.store.save(this.state);
    if (this.state.pressure.status === 'dead') return;
    const prompt = `You are TimePressure, an autonomous economic agent.\nGoal: ${this.state.working.goal}\nPressure: ${this.state.pressure.pressure.toFixed(1)}%\nCycle revenue: $${(this.state.pressure.cycleRevenueCents/100).toFixed(2)}\nTarget: $${(this.state.pressure.targetCents/100).toFixed(2)} before ${new Date(this.state.pressure.deadline).toISOString()}\nChoose one legitimate, legal, non-deceptive action that can create value. Never fabricate revenue. Never request or expose secrets. Available tools: ${tools.map(t=>t.name+': '+t.description).join('; ')}.`;
    if (!this.config.apiKey) { await this.store.addMemory(this.state, { id: crypto.randomUUID(), type: 'observation', text: 'Demo tick: no model API key configured.', timestamp: Date.now() }); return; }
    const client = new OpenAI({ apiKey: this.config.apiKey, baseURL: this.config.baseUrl });
    const response = await client.chat.completions.create({ model: this.config.model, messages: [{ role: 'system', content: 'You are a cautious autonomous agent. Output concise JSON with fields action, input, rationale.' }, { role: 'user', content: prompt }], temperature: 0.2 });
    const text = response.choices[0]?.message?.content ?? '{}';
    await this.store.addMemory(this.state, { id: crypto.randomUUID(), type: 'action', text, timestamp: Date.now(), metadata: { pressure: this.state.pressure.pressure } });
    try {
      const plan = JSON.parse(text) as { action?: string; input?: string; rationale?: string };
      if (plan.action) {
        const tool = tools.find(t => t.name === plan.action);
        if (tool) {
          const result = await tool.run(plan.input ?? '', { now: Date.now(), config: this.config } as ToolContext);
          await this.store.addMemory(this.state, { id: crypto.randomUUID(), type: 'observation', text: `${plan.action}: ${result.output}`, timestamp: Date.now() });
        }
      }
    } catch { /* model output is only a proposal */ }
  }
}
