"""
Build & deploy do workflow n8n `ENXOVAL | Webhook Lead`.

Recebe POST em /webhook/enxoval-lead com {nome, telefone, ddd, trimestre, origem, criado_em, user_agent}
-> normaliza (adiciona `regiao` = "Curitiba" se DDD=41, senão "Outros")
-> append na planilha "MRN | Leads Enxoval Ebook"

Idempotente: se o workflow ja existir, atualiza; senão cria novo.
"""
import os
import json
import urllib.request
import urllib.error

# ---- config
N8N_BASE = "https://n8n-n8n.xktssy.easypanel.host"
N8N_KEY = os.environ.get("N8N_API_KEY")
if not N8N_KEY:
    # carrega do .env.meta
    with open("D:/CLAUDE/.env.meta", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if line.startswith("N8N_API_KEY="):
                N8N_KEY = line.strip().split("=", 1)[1].strip('"')
                break

SHEETS_CRED_ID = "8fMI5lX6WRmrn4Cy"  # Google Sheets OAuth2 do Bruno (mesma do funil)
SHEET_ID = "1AKpEaKba0dHtgJkzK-820NDv8FF2hurYPfaSbqmXk7g"
SHEET_NAME = "Página1"
WORKFLOW_NAME = "ENXOVAL | Webhook Lead"
WEBHOOK_PATH = "enxoval-lead"

# ---- helpers
def api(method, path, body=None):
    url = f"{N8N_BASE}/api/v1{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "X-N8N-API-KEY": N8N_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        return e.code, {"error": body}

# ---- nodes
def node(name, ntype, params, position, extra=None):
    n = {
        "id": name.replace(" ", "_").lower(),
        "name": name,
        "type": ntype,
        "typeVersion": 1,
        "position": position,
        "parameters": params,
    }
    if extra:
        n.update(extra)
    return n

nodes = [
    node("WEBHOOK", "n8n-nodes-base.webhook", {
        "httpMethod": "POST",
        "path": WEBHOOK_PATH,
        "responseMode": "onReceived",
        "responseData": "allEntries",
        "options": {
            "responseHeaders": {
                "entries": [
                    {"name": "Access-Control-Allow-Origin", "value": "*"},
                    {"name": "Access-Control-Allow-Methods", "value": "POST, OPTIONS"},
                    {"name": "Access-Control-Allow-Headers", "value": "Content-Type"}
                ]
            }
        }
    }, [240, 300], extra={"typeVersion": 1.1, "webhookId": WEBHOOK_PATH}),

    node("PARSE LEAD", "n8n-nodes-base.code", {
        "language": "javaScript",
        "jsCode": """
const b = $input.first().json.body || $input.first().json;
const nome = (b.nome || '').toString().trim().slice(0, 100);
const telRaw = (b.telefone || '').toString().replace(/\\D/g, '');
const ddd = (b.ddd || telRaw.slice(0,2) || '').toString();
const trimestre = (b.trimestre || '').toString();
const origem = (b.origem || 'ebook-enxoval').toString();
const ua = (b.user_agent || '').toString().slice(0, 200);
const criado_em = b.criado_em || new Date().toISOString();

// validação defensiva no servidor também (browser já valida)
if (!nome || nome.length < 2) throw new Error('nome inválido');
if (telRaw.length < 10 || telRaw.length > 11) throw new Error('telefone inválido');
if (/(\\d)\\1{4,}/.test(telRaw)) throw new Error('telefone repetido');

const regiao = ddd === '41' ? 'Curitiba' : 'Outros';

return [{ json: {
  criado_em, nome, telefone: telRaw, ddd, regiao, trimestre, origem, user_agent: ua
}}];
"""
    }, [460, 300], extra={"typeVersion": 2}),

    node("APPEND SHEETS", "n8n-nodes-base.googleSheets", {
        "operation": "append",
        "documentId": {"__rl": True, "value": SHEET_ID, "mode": "id"},
        "sheetName": {"__rl": True, "value": "gid=0", "mode": "list", "cachedResultName": SHEET_NAME},
        "columns": {
            "mappingMode": "defineBelow",
            "value": {
                "criado_em": "={{ $json.criado_em }}",
                "nome": "={{ $json.nome }}",
                "telefone": "={{ $json.telefone }}",
                "ddd": "={{ $json.ddd }}",
                "regiao": "={{ $json.regiao }}",
                "trimestre": "={{ $json.trimestre }}",
                "origem": "={{ $json.origem }}",
                "user_agent": "={{ $json.user_agent }}"
            },
            "schema": [
                {"id": "criado_em", "displayName": "criado_em", "required": False, "defaultMatch": False, "canBeUsedToMatch": True, "type": "string"},
                {"id": "nome", "displayName": "nome", "required": False, "defaultMatch": False, "canBeUsedToMatch": True, "type": "string"},
                {"id": "telefone", "displayName": "telefone", "required": False, "defaultMatch": False, "canBeUsedToMatch": True, "type": "string"},
                {"id": "ddd", "displayName": "ddd", "required": False, "defaultMatch": False, "canBeUsedToMatch": True, "type": "string"},
                {"id": "regiao", "displayName": "regiao", "required": False, "defaultMatch": False, "canBeUsedToMatch": True, "type": "string"},
                {"id": "trimestre", "displayName": "trimestre", "required": False, "defaultMatch": False, "canBeUsedToMatch": True, "type": "string"},
                {"id": "origem", "displayName": "origem", "required": False, "defaultMatch": False, "canBeUsedToMatch": True, "type": "string"},
                {"id": "user_agent", "displayName": "user_agent", "required": False, "defaultMatch": False, "canBeUsedToMatch": True, "type": "string"}
            ]
        },
        "options": {}
    }, [680, 300], extra={
        "typeVersion": 4.5,
        "credentials": {"googleSheetsOAuth2Api": {"id": SHEETS_CRED_ID, "name": "Google Sheets Bruno"}}
    })
]

connections = {
    "WEBHOOK": {"main": [[{"node": "PARSE LEAD", "type": "main", "index": 0}]]},
    "PARSE LEAD": {"main": [[{"node": "APPEND SHEETS", "type": "main", "index": 0}]]}
}

# ---- monta payload
wf = {
    "name": WORKFLOW_NAME,
    "nodes": nodes,
    "connections": connections,
    "settings": {"executionOrder": "v1"}
}

# ---- procurar workflow existente pelo nome
print("Buscando workflow existente...")
code, resp = api("GET", "/workflows?limit=250")
existing_id = None
if code == 200:
    for w in resp.get("data", []):
        if w.get("name") == WORKFLOW_NAME:
            existing_id = w.get("id")
            print(f"  encontrado: {existing_id} (active={w.get('active')})")
            break

if existing_id:
    # desativar antes de PUT
    print(f"Desativando {existing_id}...")
    api("POST", f"/workflows/{existing_id}/deactivate")
    print(f"PUT /workflows/{existing_id}")
    code, resp = api("PUT", f"/workflows/{existing_id}", wf)
    print(f"  code={code}")
    if code != 200:
        print("  ERRO:", json.dumps(resp, ensure_ascii=False)[:600])
        raise SystemExit(1)
    wf_id = existing_id
else:
    print(f"POST /workflows (novo)")
    code, resp = api("POST", "/workflows", wf)
    print(f"  code={code}")
    if code >= 300:
        print("  ERRO:", json.dumps(resp, ensure_ascii=False)[:600])
        raise SystemExit(1)
    wf_id = resp.get("id")
    print(f"  criado: {wf_id}")

# ---- ativar
print(f"Ativando {wf_id}...")
code, resp = api("POST", f"/workflows/{wf_id}/activate")
print(f"  code={code} active={resp.get('active')}")

print(f"\n[OK] Workflow: {wf_id}")
print(f"     Webhook: {N8N_BASE}/webhook/{WEBHOOK_PATH}")
print(f"     Editor:  {N8N_BASE}/workflow/{wf_id}")
