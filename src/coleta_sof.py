#!/usr/bin/env python3
"""
Coleta de empenhos da API-SOF v4 (Prefeitura de São Paulo) — piloto Cultura.

Usa só a biblioteca padrão do Python (3.9+). Credenciais vêm de variáveis de
ambiente, nunca do código:

  SOF_KEY, SOF_SECRET   Consumer Key / Consumer Secret da sua aplicação na APILib
                        (o script gera um token novo a cada execução)
  ou
  SOF_TOKEN             um Token de Acesso já gerado (para testes rápidos)

  SOF_TOKEN_URL         opcional; padrão https://gateway.apilib.prefeitura.sp.gov.br/token

Exemplos:
  python coletar_sof.py --teste                       # 1 página, órgão 25, mês corrente
  python coletar_sof.py --orgaos 25 79 --ano 2026 --mes 11
"""
import argparse, base64, csv, datetime as dt, json, os, re, sys, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path

BASE = "https://gateway.apilib.prefeitura.sp.gov.br/sf/sof/v4"
TOKEN_URL = os.environ.get("SOF_TOKEN_URL", "https://gateway.apilib.prefeitura.sp.gov.br/token")


def obter_token() -> str:
    if os.environ.get("SOF_TOKEN"):
        return os.environ["SOF_TOKEN"]
    key, secret = os.environ.get("SOF_KEY"), os.environ.get("SOF_SECRET")
    if not (key and secret):
        sys.exit("Defina SOF_KEY e SOF_SECRET (ou SOF_TOKEN) como variáveis de ambiente.")
    basic = base64.b64encode(f"{key}:{secret}".encode()).decode()
    req = urllib.request.Request(TOKEN_URL, data=b"grant_type=client_credentials",
                                 headers={"Authorization": f"Basic {basic}",
                                          "Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)["access_token"]
    except urllib.error.HTTPError as e:
        sys.exit(f"Falha ao gerar token em {TOKEN_URL}: HTTP {e.code}. Confira a URL de token na aba "
                 "'Chaves de Produção' da APILib e ajuste SOF_TOKEN_URL.")


_TOKEN = {"atual": None}


def get(recurso: str, params: dict, token: str, tentativas: int = 4) -> dict:
    """Repete só falhas temporárias (429/5xx). Num 401 (token expirado ou trocado), gera um
    token novo uma única vez; não vale para SOF_TOKEN fixo."""
    url = f"{BASE}/{recurso}?{urllib.parse.urlencode(params)}"
    renovou = False
    for i in range(tentativas):
        tk = _TOKEN["atual"] or token
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {tk}", "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 401 and not renovou and not os.environ.get("SOF_TOKEN"):
                print("  401: gerando token novo e repetindo a página", file=sys.stderr)
                _TOKEN["atual"], renovou = obter_token(), True
                continue
            if e.code in (429, 500, 502, 503, 504) and i < tentativas - 1:
                time.sleep(2 ** i * 2)          # espera exponencial: 2, 4, 8 s
                continue
            raise SystemExit(f"HTTP {e.code} em {recurso} {params}: {e.read()[:300]!r}")


def lista_de(resp: dict) -> list:
    """A resposta traz 'metadados' + uma lista (ex.: lstEmpenhos). Pega a primeira lista."""
    for k, v in resp.items():
        if isinstance(v, list):
            return v
    return []


def mascarar_cpf(doc: str) -> str:
    """LGPD: CPF (11 dígitos) vira ***.456.789-** ; CNPJ fica como está."""
    d = re.sub(r"\D", "", str(doc or ""))
    return f"***.{d[3:6]}.{d[6:9]}-**" if len(d) == 11 else (doc or "")


def coletar_empenhos(token: str, ano: int, mes: int, orgao: str, max_paginas: int | None = None) -> list:
    """Percorre as páginas (50 registros cada). Segue enquanto vierem páginas cheias, mesmo que
    os metadados não informem o total de páginas (comportamento observado na v4)."""
    linhas, pagina, total_pags, tam = [], 1, None, 50
    while True:
        resp = get("empenhos", {"anoEmpenho": ano, "mesEmpenho": f"{mes:02d}", "codOrgao": orgao, "numPagina": pagina}, token)
        meta = resp.get("metadados", {}) or {}
        if pagina == 1:
            print(f"  metadados v4: { {k: v for k, v in meta.items() if 'txt' not in k.lower() or 'status' in k.lower()} }", file=sys.stderr)
        if meta.get("txtStatus") == "SEM_REGISTROS":
            break
        if total_pags is None:
            for k, v in meta.items():
                if "pagina" in k.lower() and str(v).isdigit() and int(v) > 0:
                    total_pags = int(v)
        lote = lista_de(resp)
        linhas += lote
        print(f"  órgão {orgao} · página {pagina}/{total_pags or '?'} · {len(linhas)} empenhos", file=sys.stderr)
        fim = (total_pags is not None and pagina >= total_pags and len(lote) < tam) or len(lote) < tam or not lote
        if fim or (max_paginas and pagina >= max_paginas) or pagina >= 2000:
            break
        pagina += 1
        time.sleep(0.3)                          # gentileza com o servidor
    for l in linhas:
        if "numCpfCnpj" in l:
            l["numCpfCnpj"] = mascarar_cpf(l["numCpfCnpj"])
    return linhas


def main():
    hoje = dt.date.today()
    ap = argparse.ArgumentParser()
    ap.add_argument("--ano", type=int, default=hoje.year)
    ap.add_argument("--mes", type=int, default=hoje.month, help="acumulado até este mês")
    ap.add_argument("--orgaos", nargs="+", default=["25", "79"])
    ap.add_argument("--saida", default="dados/empenhos")
    ap.add_argument("--teste", action="store_true", help="só 1 página do primeiro órgão")
    a = ap.parse_args()

    token = obter_token()
    pasta = Path(a.saida) / hoje.isoformat()          # uma "foto" por dia → série diária por diferença
    pasta.mkdir(parents=True, exist_ok=True)
    orgaos = a.orgaos[:1] if a.teste else a.orgaos
    for org in orgaos:
        linhas = coletar_empenhos(token, a.ano, a.mes, org, max_paginas=1 if a.teste else None)
        if not linhas:
            print(f"órgão {org}: sem registros", file=sys.stderr)
            continue
        arq = pasta / f"empenhos_{a.ano}_{a.mes:02d}_org{org}.csv"
        campos = sorted({k for l in linhas for k in l})
        with open(arq, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=campos, delimiter=";")
            w.writeheader(); w.writerows(linhas)
        print(f"órgão {org}: {len(linhas)} empenhos → {arq}")
        if a.teste:
            ex = linhas[0]
            print("Campos:", ", ".join(campos))
            print("Exemplo:", {k: ex.get(k) for k in ("codEmpenho", "datEmpenho", "codProcesso", "txtRazaoSocial",
                                                     "codProjetoAtividade", "valEmpenhadoLiquido", "valPagoExercicio")})


if __name__ == "__main__":
    main()
