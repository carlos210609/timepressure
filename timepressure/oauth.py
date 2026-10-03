import base64,hashlib,json,os,secrets,time,urllib.parse,urllib.request,webbrowser,uuid
from http.server import BaseHTTPRequestHandler,HTTPServer
from pathlib import Path

AUTH="https://auth.openai.com/api/accounts/authorize";TOKEN="https://auth.openai.com/api/accounts/oauth/token";RESOURCE="https://api.openai.com/v1"
SCOPES="openid profile email offline_access resource.invoke chatgpt.tokens.use.direct";ISSUER="https://auth.openai.com";JWKS="https://auth.openai.com/.well-known/jwks.json"

class OAuth:
    def __init__(self,path=None):
        self.path=Path(path or os.path.expanduser("~/.config/timepressure/oauth.json"));self.path.parent.mkdir(parents=True,exist_ok=True);d=self._load();self.host_id=d.get("ext_agent_host_id")
        if not self.host_id:self.host_id="urn:uuid:"+str(uuid.uuid4());self._save({"ext_agent_host_id":self.host_id})
    def _load(self):
        try:return json.loads(self.path.read_text())
        except Exception:return {}
    def _save(self,d):
        tmp=self.path.with_suffix(".tmp");tmp.write_text(json.dumps(d,indent=2));os.replace(tmp,self.path)
        try:os.chmod(self.path,0o600)
        except OSError:pass
    def _verify(self,id_token,client_id,nonce):
        try:
            import jwt
            key=jwt.PyJWKClient(JWKS).get_signing_key_from_jwt(id_token).key
            return jwt.decode(id_token,key,algorithms=["RS256"],issuer=ISSUER,audience=client_id,leeway=5,options={"require":["sub","exp","iat"]},verify_signature=True,verify_exp=True)
        except ImportError:raise RuntimeError("OAuth requires PyJWT. Install with: python3 -m pip install 'PyJWT[crypto]'")
        except Exception as e:raise RuntimeError(f"Invalid OpenAI ID token: {e}")
    def _refresh(self,d):
        body=urllib.parse.urlencode({"grant_type":"refresh_token","client_id":d["client_id"],"refresh_token":d["refresh_token"],"resource":RESOURCE}).encode();req=urllib.request.Request(TOKEN,body,{"Content-Type":"application/x-www-form-urlencoded","Accept":"application/json"})
        with urllib.request.urlopen(req,timeout=30) as r:n=json.loads(r.read())
        d.update(n);d["saved_at"]=time.time();self._save(d);return d["access_token"]
    def access_token(self):
        d=self._load()
        if not d.get("access_token"):return None
        if time.time()>=d.get("saved_at",0)+d.get("expires_in",3600)-120:return self._refresh(d)
        return d["access_token"]
    def login(self,agent_name="TimePressure"):
        d=self._load();client=d.get("client_id","dynamic_agent_client");state=secrets.token_urlsafe(32);nonce=secrets.token_urlsafe(32);verifier=secrets.token_urlsafe(64);challenge=base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
        class H(BaseHTTPRequestHandler):
            result=None
            def do_GET(self):
                if self.path.startswith("/auth/callback"):
                    H.result=dict(urllib.parse.parse_qsl(urllib.parse.urlparse(self.path).query));self.send_response(200);self.end_headers();self.wfile.write(b"TimePressure connected. Close this window.")
            def log_message(self,*a):pass
        try:s=HTTPServer(("127.0.0.1",1455),H)
        except OSError:s=HTTPServer(("127.0.0.1",0),H)
        redirect=f"http://127.0.0.1:{s.server_port}/auth/callback";q={"client_id":client,"response_type":"code","redirect_uri":redirect,"scope":SCOPES,"resource":RESOURCE,"state":state,"nonce":nonce,"code_challenge_method":"S256","code_challenge":challenge,"ext_agent_host_id":self.host_id}
        if client=="dynamic_agent_client":q["agent_name_hint"]=agent_name
        elif d.get("id_token"):q["id_token_hint"]=d["id_token"]
        if d.get("email") and client!="dynamic_agent_client":q["login_hint"]=d["email"]
        webbrowser.open(AUTH+"?"+urllib.parse.urlencode(q));deadline=time.time()+600
        while H.result is None and time.time()<deadline:s.handle_request()
        s.server_close();r=H.result
        if not r or r.get("state")!=state:raise RuntimeError("OAuth state validation failed.")
        if r.get("error"):raise RuntimeError(r.get("error_description",r["error"]))
        code=r.get("code");issued=r.get("client_id") or client
        if not code:raise RuntimeError("OAuth callback did not contain a code.")
        body=urllib.parse.urlencode({"grant_type":"authorization_code","code":code,"client_id":issued,"code_verifier":verifier,"redirect_uri":redirect,"resource":RESOURCE}).encode();req=urllib.request.Request(TOKEN,body,{"Content-Type":"application/x-www-form-urlencoded","Accept":"application/json"})
        with urllib.request.urlopen(req,timeout=30) as resp:t=json.loads(resp.read())
        if not t.get("access_token") or not t.get("id_token"):raise RuntimeError("OpenAI OAuth token exchange did not return the required credentials.")
        scopes=t.get("scope","").split()
        if "chatgpt.tokens.use.direct" not in scopes:raise RuntimeError("ChatGPT plan usage permission was not granted.")
        identity=self._verify(t["id_token"],issued,nonce)
        d.update({"client_id":issued,"access_token":t["access_token"],"refresh_token":t.get("refresh_token"),"id_token":t["id_token"],"token_type":t.get("token_type","Bearer"),"expires_in":t.get("expires_in",3600),"scope":t.get("scope",""),"email":identity.get("email"),"subject":identity["sub"],"saved_at":time.time(),"ext_agent_host_id":self.host_id});self._save(d);return d
    def connected(self):return bool(self._load().get("access_token"))
