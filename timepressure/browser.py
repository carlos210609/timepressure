import time, uuid
from urllib.parse import urlparse
from .models import Config, BrowserEvent

class Browser:
    def __init__(self, config, state, store):
        self.config,self.state,self.store=config,state,store
        self.page=None
        try:
            from playwright.sync_api import sync_playwright
            self._pw=sync_playwright().start()
            self.browser=self._pw.chromium.launch(headless=config.browser_headless)
            self.page=self.browser.new_page()
        except ImportError:
            raise RuntimeError("Browser support needs Playwright. Install with: pip install playwright && playwright install chromium")

    def _check(self,url):
        parsed=urlparse(url)
        if parsed.scheme!="https": raise ValueError("Browser only permits HTTPS URLs.")
        host=(parsed.hostname or "").lower()
        if not self.config.browser_allowed_domains: raise ValueError("Set TIMEPRESSURE_BROWSER_ALLOWED_DOMAINS before browser automation.")
        if not any(host==d or host.endswith("."+d) for d in self.config.browser_allowed_domains):
            raise ValueError(f"Domain not allowed: {host}")

    def open(self,url):
        self._check(url)
        self.page.goto(url,wait_until="domcontentloaded",timeout=30000)
        title=self.page.title()
        self.state.browser_history.append(BrowserEvent(str(uuid.uuid4()),"open",url,title,time.time()))
        self.state.browser_history=self.state.browser_history[-200:]
        self.store.save(self.state)
        return {"url":self.page.url,"title":title,"text":self.page.locator("body").inner_text(timeout=5000)[:30000]}

    def click(self,selector):
        self.page.locator(selector).first.click(timeout=10000)
        return {"url":self.page.url,"title":self.page.title(),"text":self.page.locator("body").inner_text(timeout=5000)[:30000]}

    def fill(self,selector,text):
        self.page.locator(selector).first.fill(text,timeout=10000)
        return {"url":self.page.url,"title":self.page.title(),"text":self.page.locator("body").inner_text(timeout=5000)[:10000]}

    def close(self):
        if self.page:self.browser.close(); self._pw.stop()
