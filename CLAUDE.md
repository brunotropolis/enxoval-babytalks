# Enxoval Descomplicado — Isca digital Baby Talks

Landing gratuita pra captação de leads via e-book **Enxoval Descomplicado** da Dayane. Deploy 16/Jul/2026.

## Arquitetura em 1 parágrafo

Site estático em `enxoval.babytalks.com.br` (**GitHub Pages + Cloudflare proxied**, repo público `brunotropolis/enxoval-babytalks`, pasta `D:\CLAUDE\enxoval-babytalks\`) com `index.html` (form nome+WhatsApp+trimestre) e `download.html` (botão de download + CTA do evento personalizado por DDD). Submit envia POST pro n8n webhook `enxoval-lead` → workflow **`ENXOVAL | Webhook Lead`** (`JCAKSyjacWbZb1Xg`) normaliza (regiao = "Curitiba" se DDD=41 senão "Outros") e faz append na planilha **`MRN | Leads Enxoval Ebook`** (`1AKpEaKba0dHtgJkzK-820NDv8FF2hurYPfaSbqmXk7g`). Um workflow secundário **`ENXOVAL | Read Leads`** (`pZpRAQMFq9qLou5F`) expõe os leads separados via GET `webhook/enxoval-leads-<secret>` e a página admin **`conteudo.babytalks.com.br/leads-enxoval.html`** consome esse endpoint pra mostrar duas tabelas (Curitiba/Outros) + CSV export + link direto WhatsApp por lead.

## URLs
| O que | URL |
|---|---|
| Landing de captura | https://enxoval.babytalks.com.br |
| Página download+CTA | https://enxoval.babytalks.com.br/download.html |
| PDF do e-book (4.2MB) | https://enxoval.babytalks.com.br/ebook-enxoval-descomplicado.pdf |
| Painel admin dos leads | https://conteudo.babytalks.com.br/leads-enxoval.html |
| Planilha (fonte da verdade) | https://docs.google.com/spreadsheets/d/1AKpEaKba0dHtgJkzK-820NDv8FF2hurYPfaSbqmXk7g/edit |
| Webhook de submit | POST https://n8n-n8n.xktssy.easypanel.host/webhook/enxoval-lead |
| Webhook de leitura | GET https://n8n-n8n.xktssy.easypanel.host/webhook/enxoval-leads-`$ENXOVAL_READ_SECRET` |

Secret da leitura em `D:\CLAUDE\.env.meta` como `ENXOVAL_READ_SECRET`.

## Estrutura do repo

```
enxoval-babytalks/
├── CNAME                                # enxoval.babytalks.com.br
├── robots.txt                           # Disallow: /
├── index.html                           # form captura (Fraunces + DM Sans, azul-noite)
├── download.html                        # confirmação + download + convite evento (varia por DDD)
├── ebook-enxoval-descomplicado.pdf      # 4.2 MB, servido direto por GitHub Pages + Cloudflare
├── ebook-capa.jpg                       # thumb da capa mostrada no hero (gerada via fitz+PIL)
├── og-image.jpg                         # 1200x630 pra og:image (capa sobre fundo azul)
├── build_workflow.py                    # deploy workflow `ENXOVAL | Webhook Lead`
├── build_read_workflow.py               # deploy workflow `ENXOVAL | Read Leads`
└── CLAUDE.md                            # este arquivo
```

## Estética
Fundo azul-noite `#1F2A56` (mesmo `--azul` do Baby Talks light) + accent magenta `#C95FA3` + verde `#2EA66C` no CTA. Capa do e-book em mockup rotacionado no hero desktop; mobile empilhado. Fontes Google (Fraunces italic pros títulos, DM Sans no corpo). Formulário em card branco flutuando sobre o azul.

## Validação de telefone (client-side)
No `index.html`, função `isTelefoneValido`:
- Só dígitos, 10 ou 11 (DDD + número)
- Bloqueia repetição (`(\d)\1{4,}` → recusa `11111`, `00000`)
- DDD entre 11 e 99 (primeiro dígito ≠ 0)
- Se 11 dígitos, o 3º precisa ser 9 (celular BR)
- Bloqueia sequências óbvias (`123456`, `987654`)

Máscara aplicada no `input` event: `(41) 99999-9999`.

Segunda validação no servidor (nó `PARSE LEAD` do workflow) — se browser burlar, servidor rejeita.

## Lógica DDD na página de download
Ler `sessionStorage['ebook-lead']` (salvo pelo form). Se `ddd === '41'`:
- **"Você é de Curitiba!"** com convite pro evento + botões "Ver ingressos" (`diskingressos.com.br/event/3351`) e "Conhecer o evento" (`babytalks.com.br`).

Senão:
- **"Vem nos visitar em Curitiba — ou compartilha com quem é daqui"** + botão "Compartilhar o link" (usa `navigator.share` se disponível, fallback `clipboard.writeText`).

Personalização: se nome preenchido, saudação vira "Pronto, {primeiro-nome}, seu e-book está aqui."

## Google Sheets

**Planilha:** `MRN | Leads Enxoval Ebook` (id `1AKpEaKba0dHtgJkzK-820NDv8FF2hurYPfaSbqmXk7g`)
- **Dono:** `brunosampa5@gmail.com` (Bruno pessoal — foi a conta logada no Chrome quando criada)
- **Editores:** `contato@brunotropolis.com.br` (essa é a conta OAuth da credencial n8n `8fMI5lX6WRmrn4Cy`) — sem esse compartilhamento, o append dá `Forbidden - perhaps check your credentials?`
- **Aba única `Página1`** com 8 colunas: `criado_em | nome | telefone | ddd | regiao | trimestre | origem | user_agent`
  - `regiao` é calculada no PARSE LEAD (não vem do form): `Curitiba` se ddd=41, `Outros` caso contrário

## Workflows n8n

### `ENXOVAL | Webhook Lead` (`JCAKSyjacWbZb1Xg`)
POST `/webhook/enxoval-lead` com body `{nome, telefone, ddd, trimestre, origem, criado_em, user_agent}` → responde 200 imediatamente (`onReceived`) e processa assincronamente:
1. **WEBHOOK** (CORS `Access-Control-Allow-Origin: *`)
2. **PARSE LEAD** (Code) — valida, normaliza `telefone` só dígitos, adiciona `regiao`
3. **APPEND SHEETS** — append na Página1

Redeploy: `python D:\CLAUDE\enxoval-babytalks\build_workflow.py` (idempotente).

### `ENXOVAL | Read Leads` (`pZpRAQMFq9qLou5F`)
GET `/webhook/enxoval-leads-<secret>` → responde JSON:
```json
{
  "curitiba": [{criado_em, nome, telefone, ddd, trimestre, origem}, ...],
  "outros": [...],
  "total": N,
  "total_curitiba": N,
  "total_outros": N,
  "atualizado_em": "ISO"
}
```
- **READ SHEETS** com `alwaysOutputData: true` (senão dá "No item to return" quando planilha vazia)
- **SEPARAR** (Code) — filtra vazias, agrupa por `regiao`, ordena por `criado_em` desc
- CORS aberto pra ser lido do domínio do hub

Redeploy: `python D:\CLAUDE\enxoval-babytalks\build_read_workflow.py`.

## Página admin — `conteudo.babytalks.com.br/leads-enxoval.html`
Arquivo em `D:\CLAUDE\babytalks-conteudo\leads-enxoval.html` + card "Leads Enxoval" adicionado no `index.html` do hub (magenta, gradient rosa).

**Features:**
- 3 KPIs no topo: Curitiba (destaque magenta), Outros, Total
- Botões: "Atualizar", "Baixar CSV · Curitiba", "Baixar CSV · Outros", "Abrir planilha"
- Duas tabelas separadas (nome | WhatsApp clicável | trimestre badge colorido | data)
- Link do WhatsApp abre `wa.me/55<num>?text=<msg-oi>` — 1 clique pra iniciar conversa
- Endpoint hardcoded no script (secret embutido — página é `noindex,nofollow` mas fica na rede pública; se preocupar, migrar pra header customizado no futuro)

## DNS
Cloudflare zone `babytalks.com.br` (`850fb1db7b7bbb29fc503249aeba97ff`):
- CNAME `enxoval` → `brunotropolis.github.io` (Proxied)

Criado via UI Cloudflare (API interna do dash retorna 403 pra POST direto — bug conhecido, ver CLAUDE-babytalks.md).

## Deploy
Push em `main` → GitHub Pages publica em 30-60s → Cloudflare cacheia. Depois de mudanças, **purgar cache** no dash Cloudflare babytalks.com.br → Caching → Configuration → Purge Everything.

```bash
cd /d/CLAUDE/enxoval-babytalks && git add -A && \
  git -c user.email="contato@brunotropolis.com.br" -c user.name="brunotropolis" \
  commit -m "msg" && git push -q origin main
```

## Bugs corrigidos nesta sessão
1. **Credencial n8n dá `Forbidden`** — a cred `8fMI5lX6WRmrn4Cy` OAuth2 é da conta `contato@brunotropolis.com.br`. Planilha criada pelo Bruno logado como `brunosampa5@gmail.com` não é acessível por default. Fix: adicionar `contato@brunotropolis.com.br` como Editor.
2. **`READ SHEETS` retorna "No item to return"** quando planilha só tem headers e nenhum dado → nós posteriores não rodam. Fix: `alwaysOutputData: true` no node.
3. **`type` em cell do Sheets não interpreta `\t`** como avanço de célula em single-cell edit — cola tudo como texto único em A1. Fix: usar `navigator.clipboard.writeText` + `Ctrl+V` pra colar como cells separadas.

## Pendências / próximos passos
- **Storage do Bruno em 81%** — a planilha nova ocupa espaço; nada crítico, mas monitorar
- **Considerar Purchase pixel Meta na `download.html`** — se o Bruno rodar tráfego pago pra essa isca, precisa medir conversão
- **Auto-envio do e-book por WhatsApp/e-mail** — hoje o lead precisa clicar no botão download. Se quiser: adicionar node "WHAPI SEND" com PDF anexo depois do APPEND SHEETS
- **Dedup por telefone** — se o mesmo número submeter 2x, hoje entra 2 linhas. Se virar problema, adicionar Read+Filter antes do append
