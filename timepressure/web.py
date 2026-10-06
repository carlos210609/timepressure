"""Local dashboard for the website-traffic-only TimePressure."""
from __future__ import annotations

import json
import socket
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from .agent import Agent
from .chat_controls import parse_pressure_command, pressure_status
from .pressure import calculate_pressure
from .social import social_snapshot
from .traffic import traffic_snapshot, start_campaign
from .traffic_engine import snapshot as traffic_engine_snapshot
from .store import Store


INDEX = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>TimePressure · Traffic Engine</title>
<style>
:root{--bg:#080a0d;--panel:#101318;--line:#252a31;--text:#f4f6f8;--muted:#89919c;--accent:#8ab4ff;--good:#57d99a;--warn:#f3c95b;--bad:#ff6879}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:14px Inter,ui-sans-serif,system-ui,sans-serif}
main{max-width:1280px;margin:auto;padding:28px}.top{display:flex;justify-content:space-between;align-items:end;margin-bottom:22px}.eyebrow{color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.16em}.title{font-size:30px;font-weight:800;letter-spacing:-.05em;margin-top:5px}.live{color:var(--muted)}.dot{display:inline-block;width:7px;height:7px;border-radius:50%;background:var(--good);margin-right:7px}
.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:17px}.label{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.08em}.value{font-size:27px;font-weight:800;margin-top:8px;letter-spacing:-.04em}.sub{font-size:12px;color:var(--muted);margin-top:6px}.section{display:grid;grid-template-columns:1.35fr .65fr;gap:12px;margin-top:12px}.section2{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:12px}.head{display:flex;justify-content:space-between;align-items:center;margin-bottom:13px}.head h2{font-size:15px;margin:0}.badge{border:1px solid var(--line);border-radius:999px;padding:4px 8px;color:var(--muted);font-size:11px}.bar{height:8px;background:#242a30;border-radius:20px;overflow:hidden;margin-top:14px}.bar i{display:block;height:100%;width:0;background:var(--accent);transition:width .35s}.target{word-break:break-all;font-family:ui-monospace,monospace;font-size:12px}.list{max-height:280px;overflow:auto}.item{padding:10px 0;border-bottom:1px solid var(--line)}.item:last-child{border:0}.item b{display:block}.item small{color:var(--muted);line-height:1.45}pre{white-space:pre-wrap;word-break:break-word;max-height:300px;overflow:auto;color:#d9dee7;font:12px/1.55 ui-monospace,monospace;margin:0}
input,button{font:inherit}input{background:#0b0e12;border:1px solid var(--line);color:var(--text);border-radius:9px;padding:10px}button{border:1px solid var(--line);background:#171c23;color:var(--text);border-radius:9px;padding:9px 12px;cursor:pointer}.pressure{display:flex;gap:8px;align-items:center}.pressure input[type=range]{flex:1;padding:0}.chat{height:210px;overflow:auto}.chatform{display:flex;gap:8px;margin-top:9px}.chatform input{flex:1}
@media(max-width:850px){main{padding:16px}.grid{grid-template-columns:1fr 1fr}.section,.section2{grid-template-columns:1fr}.top{align-items:start;gap:10px;flex-direction:column}}
</style>
</head>
<body>
<main>
<div class="top"><div><div class="eyebrow">Autonomous website growth</div><div class="title">TimePressure</div></div><div class="live"><span class="dot"></span><span id="status">loading</span></div></div>
<div class="grid">
<div class="card"><div class="label">Verified traffic</div><div class="value" id="visits">0</div><div class="sub" id="visitTarget">target —</div><div class="bar"><i id="bar"></i></div></div>
<div class="card"><div class="label">Pressure</div><div class="value" id="pressure">0%</div><div class="sub" id="pressureMode">NORMAL</div></div>
<div class="card"><div class="label">Time remaining</div><div class="value" id="left">—</div><div class="sub" id="deadline">—</div></div>
<div class="card"><div class="label">AI</div><div class="value" id="ai">—</div><div class="sub" id="model">—</div></div>
</div>

<div class="card" style="margin-top:12px"><div class="head"><h2>Website target</h2><span class="badge">traffic-only</span></div><div class="target" id="targetUrl">Not configured</div><div style="display:flex;gap:8px;margin-top:12px"><input id="targetInput" placeholder="https://seusite.com" style="flex:1"><input id="targetVisits" type="number" min="1" value="100" style="width:110px"><button id="startTraffic">Start campaign</button></div><div class="sub">The engine does not manufacture visits. Only externally verified traffic counts.</div><div class="sub" id="trafficFeedback"></div></div>

<div class="section">
<div class="card"><div class="head"><h2>Growth plan</h2><span class="badge">AI-directed</span></div><div id="plan" class="list"></div></div>
<div class="card"><div class="head"><h2>Pressure control</h2><span class="badge" id="pressureLabel">NORMAL</span></div><div class="pressure"><input id="slider" type="range" min="0" max="100" value="25"><b id="sliderValue">25%</b></div><div class="sub">LOW 0% · NORMAL 25% · HIGH 75% · EXTREME 100%</div><button id="apply" style="margin-top:10px">Apply</button><div class="sub" id="feedback"></div></div>
</div>

<div class="section2">
<div class="card"><div class="head"><h2>Distribution</h2><span class="badge">authorized accounts</span></div><div id="social" class="list"></div></div>
<div class="card"><div class="head"><h2>AI decision</h2><span class="badge">focused</span></div><pre id="decision">Waiting…</pre></div>
</div>

<div class="section2">
<div class="card"><div class="head"><h2>Activity</h2><span class="badge">latest</span></div><div id="events" class="list"></div></div>
<div class="card"><div class="head"><h2>Operator chat</h2><span class="badge">NVIDIA</span></div><div id="chat" class="chat"></div><form id="chatForm" class="chatform"><input id="chatInput" placeholder="Ex.: qual é o próximo passo?"><button>Enviar</button></form></div>
</div>
</main>
<script>
const $=id=>document.getElementById(id);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function mode(v){return v>=90?'EXTREME':v>=63?'HIGH':v<=20?'LOW':'NORMAL'}
function render(d){
 $('status').textContent=d.status;
 $('visits').textContent=(d.traffic?.verified_visits??0).toLocaleString();
 $('visitTarget').textContent='target '+(d.traffic?.target_visits??0).toLocaleString()+' verified visits';
 const pct=d.traffic?.progress??0;$('bar').style.width=pct+'%';
 $('pressure').textContent=(d.pressure??0).toFixed(1)+'%';$('pressureMode').textContent=mode(d.pressure??0);
 $('pressureLabel').textContent=mode(Number($('slider').value));
 $('left').textContent=Math.max(0,d.secondsLeft??0)+'s';$('deadline').textContent=d.deadline||'—';
 $('ai').textContent=d.nvidia?'Connected':'Missing key';$('model').textContent=d.model||'NVIDIA';
 $('targetUrl').textContent=d.traffic?.target_url||d.targetUrl||'Not configured';
 $('plan').innerHTML=(d.plan||[]).map(x=>'<div class="item"><b>'+esc(x)+'</b></div>').join('')||'<div class="sub">Waiting for the first AI cycle.</div>';
 const s=d.social?.totals||{};$('social').innerHTML='<div class="item"><b>'+s.connected+' connected account(s)</b><small>'+s.published+' published · '+s.clicks+' clicks · '+s.visits+' verified visits</small></div>';
 $('decision').textContent=JSON.stringify(d.decision||{},null,2);
 $('events').innerHTML=(d.memory||[]).slice().reverse().slice(0,12).map(x=>'<div class="item"><b>'+esc(x.type)+'</b><small>'+esc(x.text)+'</small></div>').join('')||'<div class="sub">No activity yet.</div>';
}
async function refresh(){try{const r=await fetch('/api/state',{cache:'no-store'});const d=await r.json();render(d)}catch(e){$('status').textContent='offline'}}
refresh();setInterval(refresh,3000);
$('startTraffic').onclick=async()=>{const url=$('targetInput').value.trim();const target=Number($('targetVisits').value||100);if(!url)return $('trafficFeedback').textContent='Enter an HTTPS website.';const r=await fetch('/api/traffic',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url,target})});const d=await r.json();$('trafficFeedback').textContent=r.ok?'Campaign started.':(d.error||'Failed');refresh()};
const slider=$('slider');slider.oninput=()=>{$('sliderValue').textContent=slider.value+'%';$('pressureLabel').textContent=mode(Number(slider.value))};
$('apply').onclick=async()=>{const r=await fetch('/api/pressure',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({intensity:Number(slider.value)})});const d=await r.json();$('feedback').textContent=r.ok?'Applied: '+d.multiplier.toFixed(2)+'× multiplier':(d.error||'Failed')};
$('chatForm').onsubmit=async e=>{e.preventDefault();const input=$('chatInput'),m=input.value.trim();if(!m)return;input.value='';$('chat').innerHTML+='<div class="item"><b>Você</b><small>'+esc(m)+'</small></div>';const r=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:m})});const d=await r.json();$('chat').innerHTML+='<div class="item"><b>TimePressure</b><small>'+esc(d.reply||d.error)+'</small></div>'};
</script>
</body></html>"""


def dashboard_payload(state, config):
    now = time.time()
    state.pressure = calculate_pressure(now, state.pressure, config.pressure_multiplier)
    return {
        "version": state.version,
        "status": state.pressure.status,
        "pressure": state.pressure.pressure,
        "secondsLeft": max(0, int(state.pressure.deadline - now)),
        "deadline": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(state.pressure.deadline)),
        "nvidia": bool(config.nvidia_api_key),
        "model": config.nvidia_model,
        "pressureMultiplier": config.pressure_multiplier,
        "targetUrl": state.target_url or config.target_url,
        "plan": state.working_plan,
        "lastThought": state.last_thought,
        "decision": state.decision,
        "traffic": traffic_snapshot(state),
        "trafficEngine": traffic_engine_snapshot(state, config),
        "social": social_snapshot(state),
        "memory": [vars(x) for x in state.memory[-100:]],
        "browserHistory": [vars(x) for x in state.browser_history[-50:]],
        "networkEnabled": config.allow_network,
        "browserEnabled": config.browser_enabled,
        "mode": "website-traffic-only",
    }


def _local_ip():
    try:
        s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);s.connect(("8.8.8.8",80));ip=s.getsockname()[0];s.close();return ip
    except Exception:
        return "127.0.0.1"


def serve(config, store, state, host=None, port=8787):
    class Handler(BaseHTTPRequestHandler):
        def _send(self, code, content_type, body):
            raw = body.encode() if isinstance(body,str) else body
            self.send_response(code)
            self.send_header("Content-Type",content_type)
            self.send_header("Cache-Control","no-store")
            self.send_header("Content-Length",str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self):
            path=urlparse(self.path).path
            if path=="/":
                self._send(200,"text/html; charset=utf-8",INDEX);return
            if path=="/api/state":
                self._send(200,"application/json; charset=utf-8",json.dumps(dashboard_payload(state,config),ensure_ascii=False));return
            self._send(404,"text/plain; charset=utf-8","Not found")

        def do_POST(self):
            path=urlparse(self.path).path
            length=int(self.headers.get("Content-Length","0"))
            if length>20000:
                self._send(413,"application/json; charset=utf-8",json.dumps({"error":"Request too large"}));return
            try:
                body=json.loads(self.rfile.read(length) or b"{}")
                if path=="/api/pressure":
                    intensity=float(body.get("intensity"))
                    if not 0<=intensity<=100: raise ValueError("Intensity must be between 0 and 100.")
                    config.pressure_multiplier=1.0+(intensity/100.0)*2.0
                    self._send(200,"application/json; charset=utf-8",json.dumps({"ok":True,"intensity":intensity,"multiplier":config.pressure_multiplier}));return
                if path=="/api/chat":
                    message=str(body.get("message","")).strip()
                    if not message or len(message)>4000: raise ValueError("Message must contain 1-4000 characters.")
                    command=parse_pressure_command(message,config.pressure_multiplier)
                    if command is not None:
                        config.pressure_multiplier=command
                        self._send(200,"application/json; charset=utf-8",json.dumps({"reply":pressure_status(command)},ensure_ascii=False));return
                    prompt=(
                        "You are TimePressure operator support. The product is website-traffic-only. "
                        "Explain state and legitimate growth actions. Never recommend fake traffic, click fraud, spam, "
                        "CAPTCHA bypass, rate-limit evasion, account abuse or financial activity. Current state:\n"+
                        json.dumps(dashboard_payload(state,config),ensure_ascii=False)+"\nUser:\n"+message
                    )
                    reply=Agent(config,store,state)._ask_model(prompt)
                    self._send(200,"application/json; charset=utf-8",json.dumps({"reply":reply},ensure_ascii=False));return
                if path=="/api/traffic":
                    target=str(body.get("url","")).strip()
                    visits=int(body.get("target",100))
                    campaign=str(body.get("campaign","timepressure-growth")).strip()
                    start_campaign(state,target,visits,campaign);state.target_url=target;store.save(state)
                    self._send(200,"application/json; charset=utf-8",json.dumps(traffic_snapshot(state),ensure_ascii=False));return
                self._send(404,"text/plain; charset=utf-8","Not found")
            except Exception as exc:
                self._send(400,"application/json; charset=utf-8",json.dumps({"error":str(exc)},ensure_ascii=False))

        def log_message(self,*_args): pass

    bind_host=host or _local_ip()
    server=ThreadingHTTPServer((bind_host,port),Handler)
    print(f"TimePressure dashboard: http://{bind_host}:{port}")
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()
