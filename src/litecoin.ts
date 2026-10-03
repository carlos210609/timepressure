export interface LitecoinWalletConfig{rpcUrl:string;rpcUser?:string;rpcPassword?:string;payoutAddress?:string;minPayoutLtc:number;autoPayout:boolean}
export class LitecoinRpc{
 constructor(private readonly config:LitecoinWalletConfig){}
 private async call<T>(method:string,params:unknown[]=[]):Promise<T>{
  const headers:Record<string,string>={'content-type':'application/json'};
  if(this.config.rpcUser||this.config.rpcPassword) headers.authorization=`Basic ${Buffer.from(`${this.config.rpcUser??''}:${this.config.rpcPassword??''}`).toString('base64')}`;
  const res=await fetch(this.config.rpcUrl,{method:'POST',headers,body:JSON.stringify({jsonrpc:'1.0',id:'timepressure',method,params})});
  if(!res.ok) throw new Error(`Litecoin RPC HTTP ${res.status}`);
  const body=await res.json() as {result:T;error:{code:number;message:string}|null};
  if(body.error) throw new Error(`Litecoin RPC ${body.error.code}: ${body.error.message}`);
  return body.result;
 }
 async getBalance(){return this.call<number>('getbalance')}
 async getNewAddress(label='timepressure'){return this.call<string>('getnewaddress',[label])}
 async sendToAddress(address:string,amountLtc:number,comment='TimePressure payout'){return this.call<string>('sendtoaddress',[address,amountLtc,comment])}
}
export function loadLitecoinConfig(env:NodeJS.ProcessEnv=process.env):LitecoinWalletConfig{return{rpcUrl:env.LTC_RPC_URL??'http://127.0.0.1:9332/',rpcUser:env.LTC_RPC_USER,rpcPassword:env.LTC_RPC_PASSWORD,payoutAddress:env.LTC_PAYOUT_ADDRESS,minPayoutLtc:Number(env.LTC_MIN_PAYOUT??'0.001'),autoPayout:env.LTC_AUTO_PAYOUT==='true',usdRate:Number.isFinite(Number(env.LTC_USD_RATE))&&Number(env.LTC_USD_RATE)>0?Number(env.LTC_USD_RATE):undefined}}
