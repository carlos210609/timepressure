import OpenAI from 'openai';
import crypto from 'node:crypto';
import type { AgentConfig, PersistedState, ToolContext } from './types.js';
import { tools } from './tools.js';
import { Store } from './store.js';
import { calculatePressure } from './pressure.js';
import { getAccessToken } from './auth.js';

export class Agent {
  constructor(private readonly config: AgentConfig, private readonly store: Store, private state: PersistedState) {}
  getState(){ return this.state; }

  async tick(){
    this.state.pressure=calculatePressure(Date.now(),this.state.pressure);
    await this.store.save(this.state);
    if(this.state.pressure.status==='dead') return;

    const prompt=`You are TimePressure, an autonomous economic agent.
Goal: ${this.state.working.goal}
Pressure: ${this.state.pressure.pressure.toFixed(1)}%
Cycle revenue: $${(this.state.pressure.cycleRevenueCents/100).toFixed(2)}
Target: $${(this.state.pressure.targetCents/100).toFixed(2)} before ${new Date(this.state.pressure.deadline).toISOString()}.
Choose one legitimate, legal, non-deceptive action that can create value.
Never fabricate revenue, make purchases, gamble, evade controls, or expose secrets.
Available local tools: ${tools.map(t=>t.name+': '+t.description).join('; ')}.
Return JSON with action, input and rationale.`;

    const token=await getAccessToken();
    const credential=token??this.config.apiKey;
    if(!credential){
      await this.store.addMemory(this.state,{id:crypto.randomUUID(),type:'observation',text:'No AI credential configured. Run "timepressure login" or configure OPENAI_API_KEY.',timestamp:Date.now()});
      return;
    }

    const client=new OpenAI({apiKey:credential,baseURL:this.config.baseUrl});
    const response=await client.responses.create({
      model:this.config.model,
      instructions:'You are a cautious autonomous agent. Return concise JSON only.',
      input:[{role:'user',content:[{type:'input_text',text:prompt}]}],
      store:false,
      stream:true
    });

    let text='';
    for await(const event of response){
      if(event.type==='response.output_text.delta') text+=event.delta;
    }

    await this.store.addMemory(this.state,{id:crypto.randomUUID(),type:'action',text,timestamp:Date.now(),metadata:{pressure:this.state.pressure.pressure}});
    try{
      const plan=JSON.parse(text) as {action?:string;input?:string};
      if(plan.action){
        const tool=tools.find(t=>t.name===plan.action);
        if(tool){
          const result=await tool.run(plan.input??'',{now:Date.now(),config:this.config} as ToolContext);
          await this.store.addMemory(this.state,{id:crypto.randomUUID(),type:'observation',text:`${plan.action}: ${result.output}`,timestamp:Date.now()});
        }
      }
    }catch{
      await this.store.addMemory(this.state,{id:crypto.randomUUID(),type:'error',text:'Model returned invalid action JSON.',timestamp:Date.now()});
    }
  }
}
