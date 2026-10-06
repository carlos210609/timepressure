from __future__ import annotations
import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from spark_bot.agent import SparkBot

ROOT=Path(__file__).resolve().parent.parent
BOT=SparkBot()

class Handler(SimpleHTTPRequestHandler):
    def translate_path(self,path):
        if path.startswith("/web/"):
            return str(ROOT/path.lstrip("/"))
        return str(ROOT/"web"/"index.html")
    def do_GET(self):
        path=urlparse(self.path).path
        if path=="/api/status": return self.send_json(BOT.status())
        if path=="/api/policy": return self.send_json(BOT.policies())
        if path=="/api/skills": return self.send_json({"count":len(BOT.capabilities()),"skills":BOT.capabilities()})
        return super().do_GET()
    def do_POST(self):
        if self.path!="/api/think": return self.send_error(404)
        try:
            n=int(self.headers.get("Content-Length","0"))
            data=json.loads(self.rfile.read(n) or b"{}")
            return self.send_json(BOT.think(str(data.get("objective",""))))
        except Exception as exc:
            return self.send_json({"status":"error","error":str(exc)},500)
    def send_json(self,data,status=200):
        raw=json.dumps(data,ensure_ascii=False).encode()
        self.send_response(status); self.send_header("Content-Type","application/json; charset=utf-8")
        self.send_header("Content-Length",str(len(raw))); self.end_headers(); self.wfile.write(raw)

def serve(host="127.0.0.1",port=8787):
    print(f"Spark Bot web: http://{host}:{port}")
    ThreadingHTTPServer((host,port),Handler).serve_forever()

if __name__=="__main__": serve()
