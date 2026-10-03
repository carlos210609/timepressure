import subprocess, urllib.parse, urllib.request
from pathlib import Path
from .browser import Browser

def _safe_path(raw):
    root=Path.cwd().resolve(); resolved=Path(raw).expanduser().resolve()
    if root!=resolved and root not in resolved.parents: raise ValueError("Path is outside the workspace.")
    if resolved.name==".env" or ".env" in resolved.parts: raise ValueError("Access to .env is blocked.")
    return resolved

def _safe_command(command):
    blocked=["rm -rf","mkfs","shutdown","reboot","poweroff","curl | sh","wget | sh"]
    if any(x in command.lower() for x in blocked): raise ValueError("Command blocked by safety policy.")

def run_tool(name,input_text,config,state=None,store=None):
    if name=="shell":
        _safe_command(input_text); r=subprocess.run(["bash","-lc",input_text],capture_output=True,text=True,timeout=15)
        return (r.stdout if r.returncode==0 else r.stderr or r.stdout)[:20000]
    if name=="read_file": return _safe_path(input_text).read_text()[:30000]
    if name=="fetch_url":
        if not config.allow_network:return "Network disabled."
        u=urllib.parse.urlparse(input_text)
        if u.scheme!="https":raise ValueError("Only HTTPS URLs are allowed.")
        with urllib.request.urlopen(input_text,timeout=10) as r:return r.read(30000).decode(errors="replace")
    if name.startswith("browser_"):
        if not config.browser_enabled:raise ValueError("Browser disabled.")
        if state is None or store is None:raise ValueError("Browser requires state.")
        b=Browser(config,state,store)
        try:
            if name=="browser_open":return b.open(input_text)
            if name=="browser_click":return b.click(input_text)
            if name=="browser_fill":return b.fill(*input_text.split("\n",1))
        finally:b.close()
    raise ValueError("Unknown tool.")

TOOLS={
 "shell":"Run a restricted local command.",
 "read_file":"Read a workspace text file.",
 "fetch_url":"Fetch an HTTPS URL.",
 "browser_open":"Open an allowed HTTPS page in a real Chromium browser and inspect its text.",
 "browser_click":"Click a CSS selector on the current browser page.",
 "browser_fill":"Fill a form field as selector then newline then value. Never use for payments or purchases.",
}
