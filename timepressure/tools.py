import subprocess
import urllib.error
import urllib.parse
import urllib.request

from .audit import AuditLog
from .browser import Browser
from .security import assert_agent_action, assert_https_public_url, assert_path_safe, assert_public_host
from .temp_email import prepare_temp_email_for_page


def _safe_path(raw):
    return assert_path_safe(raw)


def _safe_command(command):
    blocked = [
        "rm -rf", "mkfs", "shutdown", "reboot", "poweroff",
        "curl | sh", "wget | sh", "sudo ", ">/", ">>",
    ]
    if any(x in command.lower() for x in blocked):
        raise ValueError("Command blocked by safety policy.")


def _assert_public_host(host):
    assert_public_host(host, 443)


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _fetch_https(url, max_redirects=5):
    current = url
    opener = urllib.request.build_opener(_NoRedirect)
    for _ in range(max_redirects + 1):
        assert_https_public_url(current)
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
    assert_agent_action(name, input_text, config)
    audit = AuditLog(config.data_dir)
    audit.append("tool_attempt", tool=name)

    if name == "shell":
        _safe_command(input_text)
        result = subprocess.run(
            ["bash", "-lc", input_text],
            capture_output=True,
            text=True,
            timeout=15,
        )
        output = (result.stdout if result.returncode == 0 else result.stderr or result.stdout)[:20000]
        audit.append("tool_success", tool=name, returncode=result.returncode)
        return output

    if name == "read_file":
        output = _safe_path(input_text).read_text()[:30000]
        audit.append("tool_success", tool=name)
        return output

    if name == "fetch_url":
        output = _fetch_https(input_text)
        audit.append("tool_success", tool=name, url=input_text)
        return output

    if name.startswith("browser_"):
        if state is None or store is None:
            raise ValueError("Browser requires state.")
        browser = Browser(config, state, store)
        try:
            if name == "browser_open":
                result = browser.open(input_text)
            elif name == "browser_click":
                result = browser.click(input_text)
            elif name == "browser_fill":
                result = browser.fill(*input_text.split("\n", 1))
            elif name == "browser_use_temp_email":
                result = prepare_temp_email_for_page(browser, config)
            else:
                raise ValueError("Unknown browser tool.")
            audit.append("tool_success", tool=name)
            return result
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
    "browser_use_temp_email": "On an explicitly allowlisted test domain, open the configured temporary-email provider in the browser, obtain its displayed address, and fill a detected email field. Does not bypass CAPTCHA or verification.",
}
