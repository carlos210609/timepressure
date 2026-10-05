"""Browser-only temporary-email support for explicitly allowlisted test/integration domains.

This module intentionally does not call a temporary-mail API. It opens the provider's
normal web UI with Playwright, reads the generated address from the page, and fills the
target form only when the target domain is explicitly allowlisted.
"""
from __future__ import annotations

import re
import time
from urllib.parse import urlparse


EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
DEFAULT_PROVIDERS = (
    {"name": "temp-mail.io", "url": "https://temp-mail.io/en", "domain": "temp-mail.io"},
)


def is_target_domain_allowed(url, allowed_domains):
    parsed = urlparse(url)
    if parsed.scheme != "https":
        return False
    host = (parsed.hostname or "").lower().rstrip(".")
    domains = [d.lower().lstrip(".").rstrip(".") for d in allowed_domains]
    return bool(host and domains and any(host == d or host.endswith("." + d) for d in domains))


def _provider_allowed(url, config):
    return is_target_domain_allowed(url, getattr(config, "temp_email_provider_domains", []))


def _extract_email(page):
    # Prefer actual input values because page text can contain documentation/support emails.
    for selector in (
        'input[type="email"]',
        'input[readonly]',
        'input[aria-label*="mail" i]',
        'input[name*="mail" i]',
    ):
        locator = page.locator(selector)
        for i in range(min(locator.count(), 8)):
            try:
                value = (locator.nth(i).input_value(timeout=2000) or "").strip()
            except Exception:
                continue
            if EMAIL_RE.fullmatch(value):
                return value

    text = page.locator("body").inner_text(timeout=5000)
    candidates = EMAIL_RE.findall(text)
    for value in candidates:
        lowered = value.lower()
        if not lowered.startswith(("support@", "info@", "contact@", "hello@")):
            return value
    return candidates[0] if candidates else None


def _open_provider(browser, config):
    providers = getattr(config, "temp_email_providers", None) or DEFAULT_PROVIDERS
    for provider in providers:
        if not _provider_allowed(provider["url"], config):
            continue
        page = browser.context.new_page()
        try:
            page.goto(provider["url"], wait_until="domcontentloaded", timeout=30000)
            # The provider generates an address on page load. A short wait covers delayed UI hydration.
            deadline = time.time() + 8
            while time.time() < deadline:
                address = _extract_email(page)
                if address:
                    return page, provider, address
                page.wait_for_timeout(500)
        except Exception:
            page.close()
    raise RuntimeError("No configured temporary-email web provider produced an address.")


def prepare_temp_email_for_page(browser, config):
    if not getattr(config, "temp_email_enabled", False):
        raise PermissionError("Temporary email support is disabled.")
    target_url = browser.page.url
    if not is_target_domain_allowed(target_url, config.temp_email_target_domains):
        raise PermissionError(
            "Temporary email automation is allowed only on explicitly configured test domains."
        )

    provider_page, provider, address = _open_provider(browser, config)
    if not _provider_allowed(provider["url"], config):
        provider_page.close()
        raise PermissionError("Temporary-email provider is not allowlisted.")
    try:
        locator = browser.page.locator(
            'input[type="email"], input[name*="email" i], input[autocomplete="email"]'
        ).filter(visible=True).first
        if locator.count() == 0:
            raise ValueError("No visible email input was detected on the target page.")
        locator.fill(address, timeout=10000)
        return {
            "url": target_url,
            "email": address,
            "provider": provider["name"],
            "mode": "browser_ui",
            "message": "Temporary address generated through the provider web UI and filled on an explicitly allowlisted page.",
        }
    finally:
        provider_page.close()
