import json
import socket
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from .pressure import calculate_pressure
from .traffic import traffic_snapshot


INDEX = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>TimePressure Control</title>
<style>
:root{--bg:#090b10;--panel:#10131a;--panel2:#151923;--line:#252b36;--text:#f4f7fb;--muted:#8993a3;--good:#50d890;--warn:#f2c14e;--bad:#ff6577;--accent:#7aa7ff}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 80% -10%,#1a2740 0,#090b10 42%);color:var(--text);font:14px Inter,ui-sans-serif,system-ui,-apple-system,sans-serif}
.layout{display:grid;grid-template-columns:230px 1fr;min-height:100vh}.side{border-right:1px solid var(--line);padding:24px 18px;background:rgba(8,10,14,.88);position:sticky;top:0;height:100vh}.brand{font-size:18px;font-weight:800;letter-spacing:-.04em;margin-bottom:34px}.brand span{color:var(--accent)}.nav{display:grid;gap:8px}.nav div{padding:11px 12px;border-radius:9px;color:var(--muted)}.nav .active{background:#171c26;color:#fff}.side small{position:absolute;bottom:22px;color:#667080;line-height:1.5}
main{padding:28px;max-width:1500px;width:100%;margin:auto}.top{display:flex;justify-content:space-between;align-items:center;margin-bottom:24px}.eyebrow{color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.14em}.title{font-size:28px;font-weight:800;letter-spacing:-.05em;margin-top:5px}.live{display:flex;align-items:center;gap:8px;color:var(--muted)}.dot{width:8px;height:8px;border-radius:50%;background:var(--good);box-shadow:0 0 14px var(--good)}
.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}.card{background:linear-gradient(145deg,rgba(22,26,35,.95),rgba(13,16,22,.95));border:1px solid var(--line);border-radius:14px;padding:18px;box-shadow:0 12px 35px rgba(0,0,0,.16)}.label{font-size:12px;color:var(--muted);margin-bottom:10px}.value{font-size:27px;font-weight:800;letter-spacing:-.04em}.sub{font-size:12px;color:var(--muted);margin-top:7px}
.progress{height:7px;background:#242a34;border-radius:20px;overflow:hidden;margin-top:15px}.bar{height:100%;background:var(--accent);width:0;transition:width .4s}.section{margin-top:18px;display:grid;grid-template-columns:1.25fr .75fr;gap:14px}.section2{margin-top:14px;display:grid;grid-template-columns:1fr 1fr;gap:14px}.head{display:flex;justify-content:space-between;align-items:center;margin-bottom:14px}.head h2{font-size:15px;margin:0}.badge{font-size:11px;border:1px solid var(--line);border-radius:999px;padding:4px 8px;color:var(--muted)}
pre{white-space:pre-wrap;word-break:break-word;margin:0;color:#d7dce5;font:12px/1.55 ui-monospace,SFMono-Regular,Menlo,monospace;max-height:330px;overflow:auto}.list{display:grid;gap:9px;max-height:330px;overflow:auto}.item{border:1px solid var(--line);background:#0d1016;border-radius:9px;padding:10px}.item b{font-size:12px}.item small{display:block;color:var(--muted);margin-top:4px}.empty{color:var(--muted);padding:25px;text-align:center}.browser{background:#07090d;border:1px solid var(--line);border-radius:10px;overflow:hidden}.browserbar{padding:8px 10px;background:#11151d;color:#8791a0;font:11px monospace;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.browserbody{padding:15px;max-height:270px;overflow:auto}.pill{display:inline-block;padding:4px 8px;border-radius:6px;background:#18202c;color:#aebbd0;font-size:11px}.green{color:var(--good)}.yellow{color:var(--warn)}.red{color:var(--bad)}
@media(max-width:1000px){.layout{grid-template-columns:1fr}.side{display:none}.grid{grid-template-columns:repeat(2,1fr)}.section,.section2{grid-template-columns:1fr}main{padding:18px}}
@media(max-width:560px){.grid{grid-template-columns:1fr}.title{font-size:23px}}
</style>
</head>
<body>
<div class="layout">
<aside class="side"><div class="brand">Time<span>Pressure</span></div><div class="nav"><div class="active">Overview</div><div>Agent activity</div><div>Revenue</div><div>Browser</div><div>Tasks</div></div><small>Autonomous economic runtime<br>Local control plane</small></aside>
<main>
<div class="top"><div><div class="eyebrow">Control plane</div><div class="title">Agent overview</div></div><div class="live"><span class="dot"></span><span id="live">Connecting…</span></div></div>
<div class="grid">
<div class="card"><div class="label">Cycle revenue</div><div class="value" id="revenue">$0.00</div><div class="sub" id="target">target $0.10</div><div class="progress"><div class="bar" id="bar"></div></div></div>
<div class="card"><div class="label">Pressure</div><div class="value" id="pressure">0%</div><div class="sub" id="status">alive</div></div>
<div class="card"><div class="label">Time remaining</div><div class="value" id="left">—</div><div class="sub" id="deadline">—</div></div>
<div class="card"><div class="label">Traffic</div><div class="value" id="traffic">—</div><div class="sub" id="trafficTarget">No campaign</div></div>
<div class="card"><div class="label">ChatGPT</div><div class="value" id="chatgpt">—</div><div class="sub" id="model">—</div></div>
</div>
<div class="section">
<div class="card"><div class="head"><h2>Current AI decision</h2><span class="badge">last thought</span></div><pre id="thought">Waiting for agent activity…</pre></div>
<div class="card"><div class="head"><h2>Working plan</h2><span class="badge" id="taskcount">0 tasks</span></div><div class="list" id="plan"><div class="empty">No active plan.</div></div></div>
</div>
<div class="section2">
<div class="card"><div class="head"><h2>Browser activity</h2><span class="badge">latest</span></div><div id="browser" class="browser"><div class="browserbar">No browser activity yet</div><div class="browserbody empty">The agent has not opened a page.</div></div></div>
<div class="card"><div class="head"><h2>Revenue ledger</h2><span class="badge" id="revcount">0 events</span></div><div class="list" id="ledger"><div class="empty">No verified revenue recorded.</div></div></div>
</div>
<div class="section2">
<div class="card"><div class="head"><h2>Recent agent events</h2><span class="badge">audit stream</span></div><div class="list" id="events"><div class="empty">Waiting…</div></div></div>
<div class="card"><div class="head"><h2>Runtime</h2><span class="badge">safe mode</span></div><pre id="runtime">Loading…</pre></div>
</div>
</main></div>
<script>
const $=id=>document.getElementById(id);
const esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
function money(c){return '$'+(Number(c||0)/100).toFixed(2)}
function statusClass(s){return s==='dead'?'red':(s==='critical'?'red':(s==='warning'?'yellow':'green'))}
function render(d){
 $('live').textContent='Live · '+new Date().toLocaleTimeString();
 $('revenue').textContent=money(d.cycleRevenueCents);
 $('target').textContent='target '+money(d.targetCents);
 $('bar').style.width=Math.min(100,(d.cycleRevenueCents/Math.max(1,d.targetCents))*100)+'%';
 $('pressure').textContent=(d.pressure||0).toFixed(1)+'%';
 $('status').innerHTML='<span class="'+statusClass(d.status)+'">'+esc(d.status)+'</span>';
 const left=Math.max(0,d.secondsLeft||0); $('left').textContent=left>3600?Math.floor(left/3600)+'h '+Math.floor((left%3600)/60)+'m':Math.floor(left/60)+'m '+left%60+'s';
 $('deadline').textContent=d.deadline||'—'; $('chatgpt').innerHTML=d.chatgpt?'<span class="green">Connected</span>':'<span class="red">Disconnected</span>'; $('model').textContent=d.model||'—';
 const tr=d.traffic||{}; $('traffic').textContent=tr.active?(tr.verified_visits||0)+' / '+(tr.target_visits||0):'—'; $('trafficTarget').textContent=tr.active?((tr.progress||0).toFixed(1)+'% · '+esc(tr.status)): 'No campaign';
 $('thought').textContent=d.lastThought||'Waiting for agent activity…';
 const plan=d.plan||[]; $('taskcount').textContent=plan.length+' tasks'; $('plan').innerHTML=plan.length?plan.map((x,i)=>'<div class="item"><b>#'+(i+1)+'</b><small>'+esc(x)+'</small></div>').join(''):'<div class="empty">No active plan.</div>';
 const b=(d.browserHistory||[]).slice(-1)[0]; $('browser').innerHTML=b?'<div class="browserbar">'+esc(b.url)+'</div><div class="browserbody"><span class="pill">'+esc(b.action)+'</span><h3>'+esc(b.title||'Untitled')+'</h3><small>'+new Date(b.timestamp*1000).toLocaleString()+'</small></div>':'<div class="browserbar">No browser activity yet</div><div class="browserbody empty">The agent has not opened a page.</div>';
 const rev=(d.revenue||[]).slice().reverse(); $('revcount').textContent=rev.length+' events'; $('ledger').innerHTML=rev.length?rev.slice(0,8).map(x=>'<div class="item"><b>'+money(x.cents)+'</b><small>'+esc(x.source)+' · '+new Date(x.timestamp*1000).toLocaleString()+'</small></div>').join(''):'<div class="empty">No verified revenue recorded.</div>';
 const ev=(d.memory||[]).slice().reverse(); $('events').innerHTML=ev.length?ev.slice(0,12).map(x=>'<div class="item"><b>'+esc(x.type)+'</b><small>'+esc(x.text)+'</small></div>').join(''):'<div class="empty">Waiting…</div>';
 $('runtime').textContent=JSON.stringify({version:d.version,model:d.model,browserEnabled:d.browserEnabled,browserHeadless:d.browserHeadless,networkEnabled:d.networkEnabled},null,2);
}
async function poll(){try{const r=await fetch('/api/state',{cache:'no-store'});if(!r.ok)throw Error();render(await r.json())}catch(e){$('live').textContent='Offline';}}
poll();setInterval(poll,1500);
</script>
</body></html>"""


def _local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return "127.0.0.1"


def dashboard_payload(state, config):
    state.pressure = calculate_pressure(time.time(), state.pressure)
    return {
        "version": state.version,
        "status": state.pressure.status,
        "pressure": state.pressure.pressure,
        "cycleRevenueCents": state.pressure.cycle_revenue_cents,
        "targetCents": state.pressure.target_cents,
        "secondsLeft": max(0, int(state.pressure.deadline - time.time())),
        "deadline": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(state.pressure.deadline)),
        "chatgpt": False,
        "model": config.model,
        "plan": state.working_plan,
        "lastThought": state.last_thought,
        "revenue": [vars(x) for x in state.revenue[-100:]],
        "memory": [vars(x) for x in state.memory[-100:]],
        "browserHistory": [vars(x) for x in state.browser_history[-100:]],
        "browserEnabled": config.browser_enabled,
        "browserHeadless": config.browser_headless,
        "networkEnabled": config.allow_network,
        "traffic": traffic_snapshot(state),
    }


def serve(config, store, state, host=None, port=8787):
    from .oauth import OAuth
    oauth = OAuth()

    class Handler(BaseHTTPRequestHandler):
        def _send(self, code, content_type, body):
            raw = body.encode() if isinstance(body, str) else body
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self):
            path = urlparse(self.path).path
            if path == "/":
                self._send(200, "text/html; charset=utf-8", INDEX)
                return
            if path == "/api/state":
                payload = dashboard_payload(state, config)
                payload["chatgpt"] = oauth.connected()
                self._send(200, "application/json; charset=utf-8", json.dumps(payload, ensure_ascii=False))
                return
            self._send(404, "text/plain; charset=utf-8", "Not found")

        def log_message(self, *_args):
            pass

    bind_host = host or _local_ip()
    server = ThreadingHTTPServer((bind_host, port), Handler)
    print(f"TimePressure Control: http://{_local_ip()}:{port}")
    print(f"Local: http://127.0.0.1:{port}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
