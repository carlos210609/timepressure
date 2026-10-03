import base64
import hashlib
import json
import os
import secrets
import time
import urllib.parse
import urllib.request
import uuid
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

AUTH = "https://auth.openai.com/api/accounts/authorize"
TOKEN = "https://auth.openai.com/api/accounts/oauth/token"
RESOURCE = "https://api.openai.com/v1"
SCOPES = "openid profile email offline_access resource.invoke chatgpt.tokens.use.direct"
ISSUER = "https://auth.openai.com"
JWKS = "https://auth.openai.com/.well-known/jwks.json"


class OAuth:
    def __init__(self, path=None):
        self.path = Path(path or os.path.expanduser("~/.config/timepressure/oauth.json"))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        d = self._load()
        self.host_id = d.get("ext_agent_host_id")
        if not self.host_id:
            self.host_id = "urn:uuid:" + str(uuid.uuid4())
            self._save({"ext_agent_host_id": self.host_id})

    def _load(self):
        try:
            return json.loads(self.path.read_text())
        except Exception:
            return {}

    def _save(self, d):
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(d, indent=2))
        os.replace(tmp, self.path)
        try:
            os.chmod(self.path, 0o600)
        except OSError:
            pass

    def _verify(self, id_token, client_id, nonce):
        try:
            import jwt
            key = jwt.PyJWKClient(JWKS).get_signing_key_from_jwt(id_token).key
            claims = jwt.decode(
                id_token,
                key,
                algorithms=["RS256"],
                issuer=ISSUER,
                audience=client_id,
                leeway=5,
                options={"require": ["sub", "exp", "iat"]},
            )
            if claims.get("nonce") != nonce:
                raise RuntimeError("OpenAI ID token nonce did not match.")
            return claims
        except ImportError as exc:
            raise RuntimeError(
                "OAuth requires PyJWT. The launcher should install it automatically."
            ) from exc
        except Exception as exc:
            raise RuntimeError(f"Invalid OpenAI ID token: {exc}") from exc

    def _refresh(self, d):
        if not d.get("refresh_token"):
            raise RuntimeError("No refresh token is available; sign in again.")
        body = urllib.parse.urlencode({
            "grant_type": "refresh_token",
            "client_id": d["client_id"],
            "refresh_token": d["refresh_token"],
            "resource": RESOURCE,
        }).encode()
        req = urllib.request.Request(
            TOKEN,
            body,
            {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            refreshed = json.loads(response.read())
        d.update(refreshed)
        d["saved_at"] = time.time()
        self._save(d)
        return d["access_token"]

    def access_token(self):
        d = self._load()
        if not d.get("access_token"):
            return None
        if time.time() >= d.get("saved_at", 0) + d.get("expires_in", 3600) - 120:
            return self._refresh(d)
        return d["access_token"]

    def login(self, agent_name="TimePressure"):
        d = self._load()
        client = d.get("client_id", "dynamic_agent_client")
        state = secrets.token_urlsafe(32)
        nonce = secrets.token_urlsafe(32)
        verifier = secrets.token_urlsafe(64)
        challenge = base64.urlsafe_b64encode(
            hashlib.sha256(verifier.encode()).digest()
        ).rstrip(b"=").decode()

        class Handler(BaseHTTPRequestHandler):
            result = None

            def do_GET(self):
                parsed = urllib.parse.urlparse(self.path)
                if parsed.path == "/auth/callback":
                    Handler.result = dict(urllib.parse.parse_qsl(parsed.query))
                    self.send_response(200)
                    self.send_header("Content-Type", "text/plain; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(b"TimePressure connected. You can close this window.")

            def log_message(self, *_args):
                pass

        try:
            server = HTTPServer(("127.0.0.1", 1455), Handler)
        except OSError:
            server = HTTPServer(("127.0.0.1", 0), Handler)

        redirect = f"http://127.0.0.1:{server.server_port}/auth/callback"
        query = {
            "client_id": client,
            "response_type": "code",
            "redirect_uri": redirect,
            "scope": SCOPES,
            "resource": RESOURCE,
            "state": state,
            "nonce": nonce,
            "code_challenge_method": "S256",
            "code_challenge": challenge,
            "ext_agent_host_id": self.host_id,
        }
        if client == "dynamic_agent_client":
            query["agent_name_hint"] = agent_name
        elif d.get("id_token"):
            query["id_token_hint"] = d["id_token"]
        if d.get("email") and client != "dynamic_agent_client":
            query["login_hint"] = d["email"]

        webbrowser.open(AUTH + "?" + urllib.parse.urlencode(query))
        deadline = time.time() + 600
        while Handler.result is None and time.time() < deadline:
            server.handle_request()
        server.server_close()

        result = Handler.result
        if not result or result.get("state") != state:
            raise RuntimeError("OAuth state validation failed.")
        if result.get("error"):
            raise RuntimeError(result.get("error_description", result["error"]))

        code = result.get("code")
        issued_client = result.get("client_id") or client
        if not code:
            raise RuntimeError("OAuth callback did not contain a code.")

        body = urllib.parse.urlencode({
            "grant_type": "authorization_code",
            "code": code,
            "client_id": issued_client,
            "code_verifier": verifier,
            "redirect_uri": redirect,
            "resource": RESOURCE,
        }).encode()
        req = urllib.request.Request(
            TOKEN,
            body,
            {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            token = json.loads(response.read())

        if not token.get("access_token") or not token.get("id_token"):
            raise RuntimeError("OpenAI OAuth token exchange did not return the required credentials.")

        scopes = token.get("scope", "").split()
        if "chatgpt.tokens.use.direct" not in scopes:
            raise RuntimeError("ChatGPT plan usage permission was not granted.")

        identity = self._verify(token["id_token"], issued_client, nonce)
        d.update({
            "client_id": issued_client,
            "access_token": token["access_token"],
            "refresh_token": token.get("refresh_token"),
            "id_token": token["id_token"],
            "token_type": token.get("token_type", "Bearer"),
            "expires_in": token.get("expires_in", 3600),
            "scope": token.get("scope", ""),
            "email": identity.get("email"),
            "subject": identity["sub"],
            "saved_at": time.time(),
            "ext_agent_host_id": self.host_id,
        })
        self._save(d)
        return d

    def connected(self):
        d = self._load()
        return bool(d.get("access_token"))
