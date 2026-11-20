#!/usr/bin/env python3
"""
Fatores de correção pelo IPCA (BCB/SGS, série 433) para trazer valores anuais
a preços do último mês disponível. Gera site/ipca.json. Só biblioteca padrão.

Método: fator(ano) = índice do mês-base ÷ índice de dezembro do ano;
para o ano corrente (sem dezembro), fator = 1.
"""
import datetime as dt, json, urllib.request
from pathlib import Path

URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados?formato=json&dataInicial=01/01/2003&dataFinal={fim}"


def fatores(serie: list[dict]) -> dict:
    nivel, idx = 100.0, {}
    for x in serie:                                   # x = {"data": "dd/mm/aaaa", "valor": "0.45"}
        nivel *= 1 + float(x["valor"]) / 100
        idx[f"{x['data'][6:]}-{x['data'][3:5]}"] = nivel
    base = max(idx)
    ini, fim = int(min(idx)[:4]), int(base[:4])
    out = {"fonte": "BCB/SGS série 433 (IPCA mensal, IBGE)", "base": base,
           "metodo": "fator = índice do mês-base ÷ índice de dezembro do ano (ano corrente: mês-base)",
           "fator": {}, "ipca_ano": {}}
    for y in range(ini, fim + 1):
        k = f"{y}-12" if f"{y}-12" in idx else base
        out["fator"][str(y)] = round(idx[base] / idx[k], 5)
        out["ipca_ano"][str(y)] = round((idx[k] / idx.get(f"{y-1}-12", 100.0) - 1) * 100, 2)
    return out


def main(saida: str = "site/ipca.json"):
    fim = dt.date.today().strftime("%d/%m/%Y")
    with urllib.request.urlopen(URL.format(fim=fim), timeout=60) as r:
        serie = json.load(r)
    Path(saida).write_text(json.dumps(fatores(serie), ensure_ascii=False), encoding="utf-8")
    print(f"IPCA: base {fatores(serie)['base']}")


if __name__ == "__main__":
    main()
