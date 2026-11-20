#!/usr/bin/env python3
"""
Gera a base tratada para depósito (data/dataset/) a partir de site/*.json.
Uso: python -m src.dataset --versao 0.1.0
"""
import argparse, csv, datetime as dt, json
from pathlib import Path

COLS = ["dotacao", "orgao_cod", "orgao", "unidade", "funcao", "subfuncao", "programa_cod", "programa", "acao_cod", "acao",
        "natureza_cod", "natureza", "fonte_cod", "fonte", "emenda", "tipo_credito", "orcado", "suplementado", "reduzido",
        "atualizado", "congelado", "reservado", "empenhado", "liquidado", "pago"]


def nat(d: str) -> str:
    return f"{d[0]}.{d[1]}.{d[2]}{d[3]}.{d[4]}{d[5]}.{d[6]}{d[7]}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--versao", default="0.1.0")
    ap.add_argument("--site", default="site")
    ap.add_argument("--saida", default="data/dataset")
    a = ap.parse_args()
    p = json.load(open(Path(a.site, "data26.json"), encoding="utf-8"))
    h = json.load(open(Path(a.site, "hist.json"), encoding="utf-8"))
    ip = json.load(open(Path(a.site, "ipca.json"), encoding="utf-8"))
    out = Path(a.saida); out.mkdir(parents=True, exist_ok=True)
    d = p["dict"]
    with open(out / "execucao_2026_cultura.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(COLS)
        for r in p["data"]:
            w.writerow([f"{r[0]}.{r[1]}.{r[2]}.{r[3]}.{r[4]}.{r[5]}.{nat(r[6])}.{r[7]}", r[0], d["org"].get(r[0], ""), r[1], r[2], r[3],
                        r[4], d["prog"].get(r[4], ""), r[5], d["pa"].get(r[5], ""), nat(r[6]), d["desp"].get(r[6], ""),
                        r[7], d["fonte"].get(r[7], ""), r[8], r[9]] + r[10:19])
    with open(out / "serie_2003_2026.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["recorte", "ano", "orcado", "atualizado", "empenhado", "liquidado", "pago", "fator_ipca", "orcado_real",
                    "atualizado_real", "empenhado_real", "liquidado_real", "pago_real", "orcamento_pmsp_orcado", "orcamento_pmsp_atualizado"])
        for k in ("SMC", "F13", "FMC"):
            for y, v in sorted(h[k].items()):
                fz = ip["fator"].get(y, 1); pm = h["PMSP"].get(y, [None, None])
                w.writerow([k, y] + v + [fz] + [round(x * fz) for x in v] + pm)
    with open(out / "ipca_fatores.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["ano", "ipca_ano_pct", "fator_para_" + ip["base"]])
        for y in sorted(ip["fator"]):
            w.writerow([y, ip["ipca_ano"][y], ip["fator"][y]])
    dp = json.load(open("data/datapackage.json", encoding="utf-8"))
    dp.update({"version": a.versao, "created": dt.date.today().isoformat(),
               "contributors": [{"title": "Amilcar Ferraz Farina", "role": "author", "organization": "LAB_MicaDataWise",
                                 "path": "https://orcid.org/0009-0000-5263-4919"}]})
    dp["resources"] = [
        {"name": "execucao-2026-cultura", "path": "execucao_2026_cultura.csv", "format": "csv", "encoding": "utf-8",
         "description": f"Execução por dotação, {p['ini']} a {p['fim']}, extração {p['extr']}. Recorte: função 13 e órgãos 15, 25, 79, 85, 88, 95, 97.",
         "schema": {"fields": [{"name": c, "type": "number" if c in COLS[16:] else "string"} for c in COLS]}},
        {"name": "serie-2003-2026", "path": "serie_2003_2026.csv", "format": "csv", "encoding": "utf-8",
         "description": "Totais anuais: SMC = órgão 25; F13 = função Cultura em todos os órgãos; FMC = órgão 79. Nominais e reais (IPCA, base " + ip["base"] + ")."},
        {"name": "ipca-fatores", "path": "ipca_fatores.csv", "format": "csv", "encoding": "utf-8", "description": ip["metodo"] + " · " + ip["fonte"]}]
    json.dump(dp, open(out / "datapackage.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    (out / "README.md").write_text(f"""# Orçamento da Cultura em São Paulo — base tratada v{a.versao}

Recorte da base aberta de execução orçamentária da Prefeitura de São Paulo (SEPLAN/SOF) para a cultura, com série 2003–2026 corrigida pelo IPCA.

| Arquivo | Conteúdo |
|---|---|
| `execucao_2026_cultura.csv` | Uma linha por dotação/registro, exercício 2026 ({p['ini']}–{p['fim']}, extração {p['extr']}) |
| `serie_2003_2026.csv` | Totais anuais nominais e reais (IPCA, base {ip['base']}) para SMC (órgão 25), função 13 e Fundo Municipal de Cultura (79) |
| `ipca_fatores.csv` | Fatores de correção (BCB/SGS 433) |
| `datapackage.json` | Descrição no padrão Frictionless / Fiscal Data Package |

**Método.** Valores em R$. Real = nominal × fator, fator = IPCA de {ip['base']} ÷ IPCA de dezembro do ano (ano corrente: 1). O Fundo Municipal de Cultura não aparece como órgão próprio na base consolidada de 2018 a 2025; 2026 é exercício parcial.

**Proteção de dados (LGPD).** A base não contém CPF, CNPJ nem dados de credores. Por minimização, nomes de pessoa física que aparecem na descrição oficial de ações orçamentárias (ex.: "Organização: …") foram substituídos por `[pessoa física]`; nomes de pessoas jurídicas foram mantidos. Os demais campos reproduzem a publicação oficial.

**Fontes.** SEPLAN/PMSP — Base de Dados da Execução Orçamentária (dados abertos; Política Municipal de Dados Abertos, Lei 17.901/2023); BCB/SGS série 433 (IPCA/IBGE).

**Licença.** CC BY 4.0 (tratamento). Dados de origem conforme as fontes. Código: https://github.com/micadw/dsa-orcamento-cultura-sp (MIT) · DOI do software: 10.5281/zenodo.24399304.

**Autor.** Amilcar Ferraz Farina (LAB_MicaDataWise) · ORCID 0009-0000-5263-4919. Projeto pessoal com dados abertos; não representa posição oficial da Prefeitura de São Paulo.
""", encoding="utf-8")
    print(f"dataset v{a.versao} em {out}")


if __name__ == "__main__":
    main()
