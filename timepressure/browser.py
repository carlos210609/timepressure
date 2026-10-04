import time
import uuid
from pathlib import Path
from urllib.parse import urlparse

from .models import BrowserEvent


class Browser:
    def __init__(self, config, state, store):
        self.config = config
        self.state = state
        self.store = store
        self.page = None
        self.context = None
        self._pw = None
        try:
            from playwright.sync_api import sync_playwright
            self._pw = sync_playwright().start()
            profile = Path(config.data_dir).resolve() / "browser-profile"
            profile.mkdir(parents=True, exist_ok=True)
            try:
                profile.chmod(0o700)
            except OSError:
                pass
            self.context = self._pw.chromium.launch_persistent_context(
                str(profile),
                headless=config.browser_headless,
            )
            self.context.route("**/*", self._guard_request)
            self.page = self.context.pages[0] if self.context.pages else self.context.new_page()
        except ImportError as exc:
            raise RuntimeError(
                "Browser support needs Playwright. Install with: "
                "python3 -m pip install playwright && python3 -m playwright install chromium"
            ) from exc
        except Exception:
            self.close()
            raise

    def _allowed_host(self, host):
        host = (host or "").lower().rstrip(".")
        allowed = [d.lstrip(".").lower().rstrip(".") for d in self.config.browser_allowed_domains]
        return bool(host and allowed and any(host == d or host.endswith("." + d) for d in allowed))

    def _check(self, url):
        parsed = urlparse(url)
        if parsed.scheme != "https":
            raise ValueError("Browser only permits HTTPS URLs.")
        if not self._allowed_host(parsed.hostname):
            raise ValueError(f"Domain not allowed: {(parsed.hostname or '').lower()}")

    def _guard_request(self, route):
        url = route.request.url
        try:
            self._check(url)
        except ValueError:
            route.abort()
            return
        route.continue_()

    def _snapshot(self, limit=30000):
        self._check(self.page.url)
        return {
            "url": self.page.url,
            "title": self.page.title(),
            "text": self.page.locator("body").inner_text(timeout=5000)[:limit],
        }

    def open(self, url):
        self._check(url)
        self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
        result = self._snapshot()
        self.state.browser_history.append(
            BrowserEvent(
                str(uuid.uuid4()),
                "open",
                result["url"],
                result["title"],
                time.time(),
            )
        )
        self.state.browser_history = self.state.browser_history[-200:]
        self.store.save(self.state)
        return result

    def click(self, selector):
        self._snapshot(1000)
        self.page.locator(selector).first.click(timeout=10000)
        return self._snapshot()

    def fill(self, selector, text):
        self._snapshot(1000)
        self.page.locator(selector).first.fill(text, timeout=10000)
        return self._snapshot(10000)

    def close(self):
        try:
            if self.context:
                self.context.close()
        finally:
            self.context = None
            if self._pw:
                self._pw.stop()
                self._pw = None
