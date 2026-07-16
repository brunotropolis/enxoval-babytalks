"""
Workflow `ENXOVAL | Read Leads` — lê planilha e retorna JSON separado por região.
Endpoint: GET /webhook/enxoval-leads-<secret>
"""
import os, json, urllib.request, urllib.error

N8N_BASE = "https://n8n-n8n.xktssy.easypanel.host"
def envload(k):
    with open("D:/CLAUDE/.env.meta", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if line.startswith(k+"="):
                return line.strip().split("=", 1)[1].strip('"')

N8N_KEY = envload("N8N_API_KEY")
SECRET = envload("ENXOVAL_READ_SECRET")
SHEETS_CRED_ID = "8fMI5lX6WRmrn4Cy"
SHEET_ID = "1AKpEaKba0dHtgJkzK-820NDv8FF2hurYPfaSbqmXk7g"
WORKFLOW_NAME = "ENXOVAL | Read Leads"
WEBHOOK_PATH = f"enxoval-leads-{SECRET}"

def api(method, path, body=None):
    url = f"{N8N_BASE}/api/v1{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "X-N8N-API-KEY": N8N_KEY, "Content-Type": "application/json", "Accept": "application/json"
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, {"error": e.read().decode()}

def node(name, ntype, params, position, extra=None):
    n = {"id": name.replace(" ","_").lower(), "name": name, "type": ntype,
         "typeVersion": 1, "position": position, "parameters": params}
    if extra: n.update(extra)
    return n

nodes = [
    node("WEBHOOK", "n8n-nodes-base.webhook", {
        "httpMethod": "GET",
        "path": WEBHOOK_PATH,
        "responseMode": "lastNode",
        "options": {
            "responseHeaders": {"entries":[
                {"name":"Access-Control-Allow-Origin","value":"*"},
                {"name":"Content-Type","value":"application/json"},
                {"name":"Cache-Control","value":"no-cache"}
            ]}
        }
    }, [240, 300], extra={"typeVersion": 1.1, "webhookId": WEBHOOK_PATH}),

    node("READ SHEETS", "n8n-nodes-base.googleSheets", {
        "operation": "read",
        "documentId": {"__rl": True, "value": SHEET_ID, "mode": "id"},
        "sheetName": {"__rl": True, "value": "gid=0", "mode": "list", "cachedResultName": "Página1"},
        "options": {}
    }, [460, 300], extra={
        "typeVersion": 4.5,
        "alwaysOutputData": True,
        "credentials": {"googleSheetsOAuth2Api": {"id": SHEETS_CRED_ID, "name": "Google Sheets Bruno"}}
    }),

    node("SEPARAR", "n8n-nodes-base.code", {
        "language": "javaScript",
        "jsCode": """
const rows = $input.all().map(i => i.json);
const curitiba = [];
const outros = [];
for (const r of rows) {
  // pular linhas vazias
  if (!r.telefone && !r.nome) continue;
  const item = {
    criado_em: r.criado_em || '',
    nome: r.nome || '',
    telefone: r.telefone || '',
    ddd: r.ddd || '',
    trimestre: r.trimestre || '',
    origem: r.origem || ''
  };
  if (String(r.ddd) === '41' || String(r.regiao).toLowerCase() === 'curitiba') curitiba.push(item);
  else outros.push(item);
}
// ordenar mais recentes primeiro
const sortByDate = (a,b) => (b.criado_em||'').localeCompare(a.criado_em||'');
curitiba.sort(sortByDate);
outros.sort(sortByDate);
return [{ json: {
  curitiba, outros,
  total: curitiba.length + outros.length,
  total_curitiba: curitiba.length,
  total_outros: outros.length,
  atualizado_em: new Date().toISOString()
}}];
"""
    }, [680, 300], extra={"typeVersion": 2}),
]

connections = {
    "WEBHOOK": {"main":[[{"node":"READ SHEETS","type":"main","index":0}]]},
    "READ SHEETS": {"main":[[{"node":"SEPARAR","type":"main","index":0}]]}
}

wf = {"name": WORKFLOW_NAME, "nodes": nodes, "connections": connections, "settings": {"executionOrder":"v1"}}

# deploy
print("Buscando existente...")
code, resp = api("GET", "/workflows?limit=250")
existing_id = None
for w in resp.get("data",[]):
    if w.get("name") == WORKFLOW_NAME:
        existing_id = w.get("id"); break
if existing_id:
    print(f"desativando {existing_id}"); api("POST", f"/workflows/{existing_id}/deactivate")
    code, resp = api("PUT", f"/workflows/{existing_id}", wf)
    wf_id = existing_id
else:
    code, resp = api("POST", "/workflows", wf); wf_id = resp.get("id")
print(f"code={code} id={wf_id}")
if code >= 300:
    print(json.dumps(resp)[:500]); raise SystemExit(1)
code, resp = api("POST", f"/workflows/{wf_id}/activate")
print(f"activated: code={code} active={resp.get('active')}")
print(f"\nEndpoint: {N8N_BASE}/webhook/{WEBHOOK_PATH}")
