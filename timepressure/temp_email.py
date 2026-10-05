"""Controlled temporary-email support for explicit test/integration domains.

The runtime deliberately requires an operator-configured target-domain allowlist.
It is not a general account-creation or verification-bypass system.
"""
from __future__ import annotations

import json
import secrets
import time
import urllib.error
import urllib.request

from .security import assert_https_public_url


class MailTm:
    """Minimal Mail.tm REST client using only the public documented API."""

    def __init__(self, api_url="https://api.mail.tm", timeout=15):
        self.api_url = api_url.rstrip("/")
        self.timeout = timeout
        parsed = assert_https_public_url(self.api_url + "/domains")
        if (parsed.hostname or "").lower() != "api.mail.tm":
            raise ValueError("Only api.mail.tm is supported by the built-in provider.")

    def _request(self, path, method="GET", payload=None, token=None):
        url = self.api_url + path
        assert_https_public_url(url)
        headers = {"User-Agent": "TimePressure/0.6", "Accept": "application/json"}
        if payload is not None:
            headers["Content-Type"] = "application/json"
        if token:
            headers["Authorization"] = "Bearer " + token
        data = json.dumps(payload).encode() if payload is not None else None
        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            raw = response.read(100000)
            return json.loads(raw.decode("utf-8"))

    def create(self):
        domains = self._request("/domains").get("hydra:member", [])
        active = [x["domain"] for x in domains if x.get("isActive") and x.get("domain")]
        if not active:
            raise RuntimeError("Mail.tm returned no active domains.")
        domain = active[0]
        local = "tp" + secrets.token_hex(7)
        password = secrets.token_urlsafe(18)
        address = f"{local}@{domain}"
        self._request("/accounts", method="POST", payload={
            "address": address,
            "password": password,
        })
        auth = self._request("/token", method="POST", payload={
            "address": address,
            "password": password,
        })
        return {
            "address": address,
            "accountId": auth.get("id"),
            "token": auth.get("token"),
            "createdAt": time.time(),
        }

    def messages(self, token):
        if not token:
            raise ValueError("Mailbox token is required.")
        return self._request("/messages", token=token).get("hydra:member", [])

    def latest_message(self, token):
        messages = self.messages(token)
        return messages[0] if messages else None

    def read_message(self, token, message_id):
        if not message_id:
            raise ValueError("message_id is required.")
        return self._request(f"/messages/{message_id}", token=token)


def is_target_domain_allowed(url, allowed_domains):
    from urllib.parse import urlparse
    host = (urlparse(url).hostname or "").lower().rstrip(".")
    domains = [d.lower().lstrip(".").rstrip(".") for d in allowed_domains]
    return bool(host and domains and any(host == d or host.endswith("." + d) for d in domains))


def generate_temp_mailbox(config):
    if not getattr(config, "temp_email_enabled", False):
        raise PermissionError("Temporary email support is disabled.")
    return MailTm(config.temp_email_api_url).create()


def prepare_temp_email_for_page(browser, config):
    """Create a mailbox and fill the first visible email input on an allowlisted page."""
    if not getattr(config, "temp_email_enabled", False):
        raise PermissionError("Temporary email support is disabled.")
    if not is_target_domain_allowed(browser.page.url, config.temp_email_target_domains):
        raise PermissionError(
            "Temporary email automation is allowed only on explicitly configured test domains."
        )
    mailbox = generate_temp_mailbox(config)
    locator = browser.page.locator(
        'input[type="email"], input[name*="email" i], input[autocomplete="email"]'
    ).filter(visible=True).first
    if locator.count() == 0:
        raise ValueError("No visible email input was detected on the page.")
    locator.fill(mailbox["address"], timeout=10000)
    return {
        "url": browser.page.url,
        "email": mailbox["address"],
        "provider": "mail.tm",
        "accountId": mailbox.get("accountId"),
        "message": "Temporary address created and filled on an explicitly allowlisted page.",
    }
