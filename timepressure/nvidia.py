from __future__ import annotations
import json, os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
ENDPOINT="https://integrate.api.nvidia.com/v1/chat/completions"
MODEL="meta/llama-3.1-8b-instruct"

def suggest(context):
    key=os.getenv("NVIDIA_API_KEY")
    if not key: return None
    payload={"model":os.getenv("NVIDIA_MODEL",MODEL),"temperature":0.2,"max_tokens":300,"messages":[{"role":"system","content":"Suggest one legitimate website traffic-growth action. Never suggest fake traffic, spam, fake accounts, click manipulation, or policy evasion."},{"role":"user","content":json.dumps(context,ensure_ascii=False)}]}
    req=Request(ENDPOINT,data=json.dumps(payload).encode(),headers={"Authorization":"Bearer "+key,"Content-Type":"application/json","Accept":"application/json"},method="POST")
    try:
        with urlopen(req,timeout=20) as response: data=json.loads(response.read().decode())
        return data["choices"][0]["message"]["content"].strip()
    except (HTTPError,URLError,TimeoutError,KeyError,IndexError,json.JSONDecodeError): return None
