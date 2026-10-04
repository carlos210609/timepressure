import ipaddress
import socket
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from .browser import Browser


def _safe_path(raw):
    root = Path.cwd().resolve()
    resolved = Path(raw).expanduser().resolve()
    if root != resolved and root not in resolved.parents:
        raise ValueError("Path is outside the workspace.")
    if resolved.name == ".env" or ".env" in resolved.parts:
        raise ValueError("Access to .env is blocked.")
    return resolved


def _safe_command(command):
    blocked = [
        "rm -rf", "mkfs", "shutdown", "reboot", "poweroff",
        "curl | sh", "wget | sh", "sudo ", ">/", ">>",
    ]
    if any(x in command.lower() for x in blocked):
        raise ValueError("Command blocked by safety policy.")


def _assert_public_host(host):
    if not host:
        raise ValueError("URL must include a hostname.")
    try:
        addresses = {item[4][0] for item in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)}
    except socket.gaierror as exc:
        raise ValueError(f"Could not resolve host: {host}") from exc
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if not ip.is_global:
            raise ValueError(f"Network access to non-public address is blocked: {address}")


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _fetch_https(url, max_redirects=5):
    current = url
    opener = urllib.request.build_opener(_NoRedirect)
    for _ in range(max_redirects + 1):
        parsed = urllib.parse.urlparse(current)
        if parsed.scheme != "https":
            raise ValueError("Only HTTPS URLs are allowed.")
        _assert_public_host(parsed.hostname)
        request = urllib.request.Request(current, headers={"User-Agent": "TimePressure/0.4"})
        try:
            with opener.open(request, timeout=10) as response:
                return response.read(30000).decode(errors="replace")
        except urllib.error.HTTPError as exc:
            if exc.code not in {301, 302, 303, 307, 308}:
                raise
            location = exc.headers.get("Location")
            if not location:
                raise ValueError("Redirect response did not provide a location.")
            current = urllib.parse.urljoin(current, location)
    raise ValueError("Too many redirects.")


def run_tool(name, input_text, config, state=None, store=None):
    if name == "shell":
        if not config.shell_enabled:
            raise ValueError(
                "Shell tool is disabled. Set TIMEPRESSURE_SHELL_ENABLED=true only if you explicitly trust local command execution."
            )
        _safe_command(input_text)
        result = subprocess.run(
            ["bash", "-lc", input_text],
            capture_output=True,
            text=True,
            timeout=15,
        )
        return (result.stdout if result.returncode == 0 else result.stderr or result.stdout)[:20000]

    if name == "read_file":
        return _safe_path(input_text).read_text()[:30000]

    if name == "fetch_url":
        if not config.allow_network:
            return "Network disabled."
        return _fetch_https(input_text)

    if name.startswith("browser_"):
        if not config.browser_enabled:
            raise ValueError("Browser disabled.")
        if state is None or store is None:
            raise ValueError("Browser requires state.")
        browser = Browser(config, state, store)
        try:
            if name == "browser_open":
                return browser.open(input_text)
            if name == "browser_click":
                return browser.click(input_text)
            if name == "browser_fill":
                return browser.fill(*input_text.split("\n", 1))
        finally:
            browser.close()

    raise ValueError("Unknown tool.")


TOOLS = {
    "shell": "Run a restricted local command.",
    "read_file": "Read a workspace text file.",
    "fetch_url": "Fetch an HTTPS URL.",
    "browser_open": "Open an allowed HTTPS page in a real Chromium browser and inspect its text.",
    "browser_click": "Click a CSS selector on the current browser page.",
    "browser_fill": "Fill a form field as selector then newline then value. Never use for payments or purchases.",
}
