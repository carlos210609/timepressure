import { createHash, randomBytes, randomUUID } from 'node:crypto';
import { chmod, mkdir, readFile, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { createRemoteJWKSet, jwtVerify } from 'jose';

const exec=promisify(execFile);
const AUTH='https://auth.openai.com';
const RESOURCE='https://api.openai.com/v1';
const CALLBACK_PATH='/auth/callback';
const SCOPES='openid profile email offline_access resource.invoke chatgpt.tokens.use.direct';

interface Credential{
 email?:string; issuer:string; subject:string; client_id:string; ext_agent_host_id:string;
 id_token:string; access_token:string; refresh_token:string; token_type:string;
 expires_in:number; expires_at:number; scopes:string[];
}
interface Stored{host_id:string; credential?:Credential}

function filePath(){return path.join(os.homedir(),'.config','timepressure','credentials.json')}
async function save(data:Stored){
 const file=filePath(); await mkdir(path.dirname(file),{recursive:true});
 const tmp=file+'.tmp'; await writeFile(tmp,JSON.stringify(data,null,2),{mode:0o600}); await chmod(tmp,0o600); await writeFile(file,await readFile(tmp),{mode:0o600});
}
async function load():Promise<Stored>{
 try{return JSON.parse(await readFile(filePath(),'utf8')) as Stored}catch{
  const data={host_id:'urn:uuid:'+randomUUID()}; await save(data); return data;
 }
}
function b64url(b:Buffer){return b.toString('base64url')}
function openBrowser(url:string){
 const p=process.platform==='win32'?['cmd','/c','start','',url]:process.platform==='darwin'?['open',url]:['xdg-open',url];
 return exec(p[0],p.slice(1)).catch(()=>{console.log('Open this URL in your browser:\n'+url)})
}
async function exchange(params:URLSearchParams){
 const res=await fetch(AUTH+'/api/accounts/oauth/token',{method:'POST',headers:{'content-type':'application/x-www-form-urlencoded'},body:params});
 if(!res.ok) throw new Error('OAuth token exchange failed: '+await res.text());
 return await res.json() as {access_token:string;refresh_token:string;id_token:string;token_type:string;expires_in:number;scope?:string};
}
async function verify(idToken:string,clientId:string,nonce:string){
 const jwks=createRemoteJWKSet(new URL(AUTH+'/.well-known/jwks.json'));
 return jwtVerify(idToken,jwks,{issuer:AUTH,audience:clientId,nonce});
}
export async function login(){
 const stored=await load();
 const server=(await import('node:http')).createServer();
 await new Promise<void>((resolve,reject)=>server.listen(0,'127.0.0.1',()=>resolve()));
 const address=server.address(); if(!address||typeof address==='string') throw new Error('Could not allocate OAuth callback port.');
 const redirect=`http://127.0.0.1:${address.port}${CALLBACK_PATH}`;
 const state=b64url(randomBytes(32)),nonce=b64url(randomBytes(32)),verifier=b64url(randomBytes(48));
 const challenge=b64url(createHash('sha256').update(verifier).digest());
 const url=new URL(AUTH+'/api/accounts/authorize');
 url.searchParams.set('client_id','dynamic_agent_client');
 url.searchParams.set('agent_name_hint','TimePressure');
 url.searchParams.set('ext_agent_host_id',stored.host_id);
 url.searchParams.set('response_type','code'); url.searchParams.set('redirect_uri',redirect);
 url.searchParams.set('scope',SCOPES); url.searchParams.set('resource',RESOURCE);
 url.searchParams.set('state',state); url.searchParams.set('nonce',nonce);
 url.searchParams.set('code_challenge_method','S256'); url.searchParams.set('code_challenge',challenge);
 console.log('Opening Sign in with ChatGPT...');
 await openBrowser(url.toString());
 const result=await new Promise<{code:string;clientId:string;scope?:string}>((resolve,reject)=>{
  const timer=setTimeout(()=>{server.close();reject(new Error('OAuth login timed out after 5 minutes.'))},300000);
  server.on('request',async(req,res)=>{
   try{
    const u=new URL(req.url??'/',redirect); if(u.pathname!==CALLBACK_PATH){res.statusCode=404;res.end();return}
    if(u.searchParams.get('state')!==state){res.statusCode=400;res.end('Invalid state.');throw new Error('Invalid OAuth state.')}
    const err=u.searchParams.get('error'); if(err){res.statusCode=400;res.end('Authorization failed.');throw new Error('OAuth error: '+err)}
    const code=u.searchParams.get('code'),clientId=u.searchParams.get('client_id');
    if(!code||!clientId) throw new Error('OAuth callback did not include code/client_id.');
    clearTimeout(timer);res.end('TimePressure connected. You can close this tab.');server.close();resolve({code,clientId,scope:u.searchParams.get('scope')??undefined});
   }catch(e){clearTimeout(timer);server.close();reject(e)}
  })
 });
 const token=await exchange(new URLSearchParams({grant_type:'authorization_code',client_id:result.clientId,code:result.code,code_verifier:verifier,redirect_uri:redirect,resource:RESOURCE}));
 const verified=await verify(token.id_token,result.clientId,nonce);
 const scopes=(token.scope??result.scope??'').split(/\s+/).filter(Boolean);
 if(!scopes.includes('chatgpt.tokens.use.direct')) throw new Error('ChatGPT plan usage permission was not granted.');
 const c:Credential={email:typeof verified.payload.email==='string'?verified.payload.email:undefined,issuer:String(verified.payload.iss),subject:String(verified.payload.sub),client_id:result.clientId,ext_agent_host_id:stored.host_id,id_token:token.id_token,access_token:token.access_token,refresh_token:token.refresh_token,token_type:token.token_type,expires_in:token.expires_in,expires_at:Date.now()+token.expires_in*1000,scopes};
 await save({host_id:stored.host_id,credential:c}); console.log('Connected'+(c.email?' as '+c.email:'')+'.');
}
export async function getAccessToken(){
 const s=await load(); if(!s.credential) return undefined;
 if(Date.now()<s.credential.expires_at-60000)return s.credential.access_token;
 const c=s.credential;
 const token=await exchange(new URLSearchParams({grant_type:'refresh_token',client_id:c.client_id,refresh_token:c.refresh_token,resource:RESOURCE}));
 const updated={...c,access_token:token.access_token,refresh_token:token.refresh_token??c.refresh_token,id_token:token.id_token??c.id_token,token_type:token.token_type??c.token_type,expires_in:token.expires_in,expires_at:Date.now()+token.expires_in*1000,scopes:(token.scope??c.scopes.join(' ')).split(/\s+/).filter(Boolean)};
 await save({host_id:s.host_id,credential:updated}); return updated.access_token;
}
export async function status(){
 const s=await load(); if(!s.credential){console.log(JSON.stringify({connected:false},null,2));return}
 console.log(JSON.stringify({connected:true,email:s.credential.email??null,clientId:s.credential.client_id,expiresAt:new Date(s.credential.expires_at).toISOString(),scopes:s.credential.scopes},null,2));
}
export async function logout(){
 const s=await load(); await save({host_id:s.host_id}); console.log('Local ChatGPT credentials removed.');
}
