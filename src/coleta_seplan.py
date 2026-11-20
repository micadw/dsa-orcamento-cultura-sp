#!/usr/bin/env python3
"""
Coleta das bases abertas de execução orçamentária da SEPLAN/PMSP (sem token)
e geração dos JSON usados pelo site (site/data26.json e site/hist.json).

Fonte: https://prefeitura.sp.gov.br/web/planejamento/w/execucao_orcamentaria
Só biblioteca padrão. Uso:
    python -m src.coleta_seplan               # ano corrente, recorte Cultura
    python -m src.coleta_seplan --bruto data/raw   # também guarda os CSV originais
"""
import argparse, csv, datetime as dt, io, json, re, urllib.request
from pathlib import Path

BASE = "https://prefeitura.sp.gov.br/cidade/secretarias/upload/seplan/arquivos/Exercicio_{ano}/"
ARQ_ANO = "basedadosexecucao_{ano}.csv"
ARQ_HIST = "basedadosexecucaoconsolidados_{ano}.csv"

# Recorte do piloto: função 13 (Cultura) + órgãos ligados à cultura
FUNCAO_CULTURA = "13"
ORGAOS_CULTURA = {"15", "25", "79", "85", "88", "95", "97"}

CAMPOS = ["Cd_Orgao", "Cd_Unidade", "Cd_Funcao", "Cd_SubFuncao", "Cd_Programa", "ProjetoAtividade",
          "Cd_Despesa", "Cd_Fonte", "Cd_Nro_Emenda_Dotacao", "TXT_TIP_CRED_ORCM"]
VALORES = ["Vl_Orcado_Ano", "Vl_Suplementado", "Vl_Reduzido", "Vl_Orcado_Atualizado", "Vl_CongeladoLiquido",
           "Vl_ReservadoLiquido", "Vl_EmpenhadoLiquido", "Vl_Liquidado", "Vl_Pago"]
DICTS = {"org": ("Cd_Orgao", "Ds_Orgao"), "prog": ("Cd_Programa", "Ds_Programa"),
         "pa": ("ProjetoAtividade", "Ds_Projeto_Atividade"), "desp": ("Cd_Despesa", "Ds_Despesa"),
         "fonte": ("Cd_Fonte", "Ds_Fonte"), "sub": ("Cd_SubFuncao", "Ds_SubFuncao")}


def baixar(url: str, tentativas: int = 3) -> str:
    """Baixa o arquivo identificando o projeto. Repete só em falhas temporárias (429/5xx);
    uma recusa (403) é respeitada e propagada."""
    import time, urllib.error
    for i in range(tentativas):
        req = urllib.request.Request(url, headers={"User-Agent": "dsa-orcamento-cultura-sp (pesquisa, dados abertos)"})
        try:
            with urllib.request.urlopen(req, timeout=300) as r:   # segue o redirecionamento para drive.prefeitura
                raw = r.read()
            break
        except urllib.error.HTTPError as e:
            if i == tentativas - 1 or e.code not in (429, 500, 502, 503, 504):
                raise
            time.sleep(30 * (i + 1))
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("cp1252")


def num(s: str) -> float:
    """'1.234,56' ou '1234,56' → 1234.56 (a base usa vírgula decimal, sem separador de milhar)."""
    s = (s or "0").strip().replace(".", "").replace(",", ".") if "," in (s or "") else (s or "0")
    try:
        return round(float(s), 2)
    except ValueError:
        return 0.0


# LGPD (minimização): nomes de pessoa física em descrições de ações ("Organização: Fulana de Tal")
# são substituídos; pessoas jurídicas (associação, instituto, coletivo etc.) são mantidas.
_RE_ORG = re.compile(r"((?:Organiza[çc][ãa]o|Proponente|Organizador[a]?|Realiza[çc][ãa]o)\s*:\s*)([^.;\"]+)", re.I)
_PJ = re.compile(r"\b(associa[çc][ãa]o|instituto|coletivo|grupo|cia\.?|companhia|funda[çc][ãa]o|cooperativa|ltda|eireli|"
                 r"\bme\b|mei|s/?a|sociedade|centro|movimento|federa[çc][ãa]o|sindicato|clube|n[úu]cleo|rede|uni[ãa]o|"
                 r"academia|escola|universidade|ong|oscip|produ[çc][õo]es|editora|teatro|banda|orquestra|festival)\b", re.I)
MASCARA_PF = "[pessoa física]"


def mascarar_pf(desc: str) -> str:
    """Substitui nomes de pessoa física após 'Organização:' (e similares) por [pessoa física]."""
    if not desc:
        return desc
    return _RE_ORG.sub(lambda m: m.group(1) + (m.group(2) if _PJ.search(m.group(2)) else MASCARA_PF), desc)


def ler(texto: str):
    return csv.DictReader(io.StringIO(texto), delimiter=";")


def no_recorte(r: dict) -> bool:
    return r.get("Cd_Funcao") == FUNCAO_CULTURA or r.get("Cd_Orgao") in ORGAOS_CULTURA


def pacote_ano(texto: str) -> dict:
    linhas = [r for r in ler(texto)]
    sel = [r for r in linhas if no_recorte(r)]
    dic = {k: {} for k in DICTS}
    for r in sel:
        for k, (c, d) in DICTS.items():
            dic[k][r[c]] = mascarar_pf(r[d])
    data = [[r[c] or "" for c in CAMPOS] + [num(r[v]) for v in VALORES] for r in sel]
    p = linhas[0] if linhas else {}
    return {"extr": p.get("DataExtracao"), "ini": p.get("DataInicial"), "fim": p.get("DataFinal"),
            "dict": dic, "data": data}


def pacote_hist(texto: str) -> dict:
    """Agrega por ano: [orçado, atualizado, empenhado, liquidado, pago] para SMC, FMC, função 13 e PMSP."""
    agg = {"SMC": {}, "FMC": {}, "F13": {}, "PMSP": {}}
    for r in ler(texto):
        ano = r.get("Cd_AnoExecucao") or r.get("Cd_Exercicio")
        if not (ano and ano.isdigit() and len(ano) == 4):
            continue
        chaves = ["PMSP"]
        if r.get("Cd_Orgao") == "25": chaves.append("SMC")
        if r.get("Cd_Orgao") == "79": chaves.append("FMC")
        if r.get("Cd_Funcao") == FUNCAO_CULTURA: chaves.append("F13")
        vals = [num(r.get(v)) for v in ("Vl_Orcado_Ano", "Vl_Orcado_Atualizado", "Vl_EmpenhadoLiquido", "Vl_Liquidado", "Vl_Pago")]
        for k in chaves:
            a = agg[k].setdefault(ano, [0.0] * 5)
            for i, v in enumerate(vals):
                a[i] += v
    for k in agg:
        agg[k] = {a: [round(x) for x in v] for a, v in sorted(agg[k].items())}
    agg["PMSP"] = {a: v[:2] for a, v in agg["PMSP"].items()}
    return agg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ano", type=int, default=dt.date.today().year)
    ap.add_argument("--site", default="site")
    ap.add_argument("--bruto", help="pasta para guardar os CSV originais (fora do git)")
    a = ap.parse_args()
    base = BASE.format(ano=a.ano)
    txt_ano = baixar(base + ARQ_ANO.format(ano=a.ano))
    txt_hist = baixar(base + ARQ_HIST.format(ano=a.ano))
    if a.bruto:
        d = Path(a.bruto) / dt.date.today().isoformat(); d.mkdir(parents=True, exist_ok=True)
        (d / ARQ_ANO.format(ano=a.ano)).write_text(txt_ano, encoding="utf-8")
        (d / ARQ_HIST.format(ano=a.ano)).write_text(txt_hist, encoding="utf-8")
    p = pacote_ano(txt_ano)
    h = pacote_hist(txt_hist)
    Path(a.site).mkdir(exist_ok=True)
    Path(a.site, "data26.json").write_text(json.dumps(p, ensure_ascii=False), encoding="utf-8")
    Path(a.site, "hist.json").write_text(json.dumps(h), encoding="utf-8")
    orc_smc = sum(r[10] for r in p["data"] if r[0] == "25")
    print(f"{len(p['data'])} dotações no recorte · extração {p['extr']} · SMC orçado inicial R$ {orc_smc:,.0f}")


if __name__ == "__main__":
    main()
