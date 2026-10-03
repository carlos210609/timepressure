import subprocess
import urllib.parse
import urllib.request
from pathlib import Path

def _safe_path(raw):
    root = Path.cwd().resolve()
    resolved = Path(raw).expanduser().resolve()
    if root != resolved and root not in resolved.parents:
        raise ValueError("Path is outside the workspace.")
    if resolved.name == ".env" or ".env" in resolved.parts:
        raise ValueError("Access to .env is blocked.")
    return resolved

def _safe_command(command):
    blocked = ["rm -rf", "mkfs", "shutdown", "reboot", "poweroff", "curl | sh", "wget | sh"]
    low = command.lower()
    if any(item in low for item in blocked):
        raise ValueError("Command blocked by safety policy.")

def run_tool(name, input_text, config):
    if name == "shell":
        _safe_command(input_text)
        result = subprocess.run(["bash", "-lc", input_text], capture_output=True, text=True, timeout=15)
        return (result.stdout if result.returncode == 0 else result.stderr or result.stdout)[:20000]
    if name == "read_file":
        return _safe_path(input_text).read_text()[:30000]
    if name == "fetch_url":
        if not config.allow_network:
            return "Network disabled."
        url = urllib.parse.urlparse(input_text)
        if url.scheme not in ("http", "https"):
            raise ValueError("Only HTTP(S) URLs are allowed.")
        with urllib.request.urlopen(input_text, timeout=10) as response:
            return response.read(30000).decode(errors="replace")
    raise ValueError("Unknown tool.")

TOOLS = {
    "shell": "Run a safe local command.",
    "read_file": "Read a relative text file.",
    "fetch_url": "Fetch a public HTTP(S) URL when network is enabled.",
}
