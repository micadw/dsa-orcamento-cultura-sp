#!/usr/bin/env python3
"""
Agrega os empenhos da API-SOF por dotação e gera site/empenhos26.json para a ficha.

Entrada: os CSV (separador ;) gravados por src.coleta_sof em data/empenhos/<data>/.
Roda no CI logo após a coleta. Os CSV brutos ficam fora do git.

Chave de ligação com a base da SEPLAN (a mesma da ficha):
  órgão.unidade.função.subfunção.programa.projeto-atividade + 6 primeiros dígitos
  da natureza (categoria, grupo, modalidade, elemento). Dentro de cada chave, os
  valores também são separados por fonte de recursos.

LGPD: o nome do credor só aparece quando o documento é um CNPJ (14 dígitos) e a
razão social não é a de um MEI (que contém o nome do titular).
Pessoa física, ou documento ausente ou ilegível, vira "[pessoa física]", e o CPF
fica mascarado (src.coleta_sof.mascarar_cpf).
"""
import argparse, csv, json, re, sys
from collections import defaultdict
from pathlib import Path

from src.coleta_sof import mascarar_cpf

# Nomes de campo possíveis (a v4 nem sempre segue a documentação); comparação sem maiúsculas.
CAMPOS = {
    "org": ["codOrgao"], "uni": ["codUnidade"], "fun": ["codFuncao"], "sub": ["codSubFuncao"],
    "prog": ["codPrograma"], "pa": ["codProjetoAtividade", "codProjAtividade"],
    "cat": ["codCategoria", "codCategoriaEconomica"], "grp": ["codGrupo", "codGrupoDespesa"],
    "mod": ["codModalidade", "codModalidadeAplicacao"], "ele": ["codElemento", "codElementoDespesa"],
    "nat": ["codNaturezaDespesa", "codNatureza", "codDespesa"],
    "fonte": ["codFonteRecurso", "codFonte", "codFonteRecursos"],
    "num": ["codEmpenho", "numEmpenho"], "data": ["datEmpenho", "dataEmpenho"],
    "proc": ["codProcesso", "numProcesso"], "doc": ["numCpfCnpj", "numCnpjCpf"],
    "nome": ["txtRazaoSocial", "nomCredor", "txtCredor"],
    "emp": ["valEmpenhadoLiquido", "valTotalEmpenhado", "valEmpenhado"],
    "liq": ["valLiquidado", "valTotalLiquidado"], "pago": ["valPagoExercicio", "valPago", "valTotalPago"],
}
LARG = {"org": 2, "uni": 2, "fun": 2, "sub": 3, "prog": 4, "pa": 4}
PF = "[pessoa física]"
MEI = "[microempreendedor individual]"
# Razão social de MEI = 8 primeiros dígitos do CNPJ + nome completo do titular (pessoa natural).
_RE_MEI = re.compile(r"^\s*\d{8}\s+\D")


def nome_publicavel(nome: str) -> str:
    """LGPD: o nome do titular de um MEI é dado pessoal; mostra só a categoria."""
    return MEI if _RE_MEI.match(nome or "") else nome


def mapear(cabecalho: list) -> dict:
    baixo = {c.lower(): c for c in cabecalho}
    return {k: next((baixo[c.lower()] for c in cands if c.lower() in baixo), None) for k, cands in CAMPOS.items()}


def num(v) -> float:
    s = str(v or "").strip()
    if not s:
        return 0.0
    if "," in s:                       # 1.234,56
        s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return 0.0


def digitos(v) -> str:
    return re.sub(r"\D", "", str(v or ""))


def natureza6(r: dict, m: dict) -> str | None:
    if all(m[k] for k in ("cat", "grp", "mod", "ele")):
        p = [digitos(r[m["cat"]]), digitos(r[m["grp"]]), digitos(r[m["mod"]]).zfill(2), digitos(r[m["ele"]]).zfill(2)]
        return "".join(p) if all(p) else None
    if m["nat"]:
        d = digitos(r[m["nat"]])
        return d[:6] if len(d) >= 6 else None
    return None


def chave(r: dict, m: dict) -> str | None:
    partes = []
    for k, w in LARG.items():
        d = digitos(r[m[k]]) if m[k] else ""
        if not d:
            return None
        partes.append(d.zfill(w))
    nat = natureza6(r, m)
    if not nat:
        return None
    return ".".join(partes + [nat[0], nat[1], nat[2:4], nat[4:6]])


def fonte(r: dict, m: dict) -> str:
    """Fonte no padrão da SEPLAN (2 dígitos). A v4 traz o código novo de 10 dígitos
    (ex.: 0015009001); os 2 primeiros são a fonte antiga (00 Tesouro, 02 transferências federais)."""
    d = digitos(r[m["fonte"]]) if m["fonte"] else ""
    return (d[:2] if len(d) > 2 else d.zfill(2)) if d else ""


def credor(r: dict, m: dict) -> tuple[str, str]:
    doc = digitos(r[m["doc"]]) if m["doc"] else ""
    bruto = str(r[m["doc"]]) if m["doc"] else ""
    if len(doc) == 14 and "*" not in bruto:
        return nome_publicavel(str(r[m["nome"]] or "").strip() if m["nome"] else ""), doc
    return PF, mascarar_cpf(doc) if len(doc) == 11 else (bruto if "*" in bruto else "")


def diagnostico(cab: list, m: dict, linhas: list) -> None:
    """Só estrutura: nomes de colunas e tamanhos dos códigos. Nenhum valor de credor."""
    print(f"  colunas ({len(cab)}): {', '.join(cab)}", file=sys.stderr)
    print(f"  mapeamento: { {k: v for k, v in m.items()} }", file=sys.stderr)
    for k in ("org", "uni", "fun", "sub", "prog", "pa", "cat", "grp", "mod", "ele", "nat", "fonte"):
        if m[k]:
            tams = sorted({len(digitos(l[m[k]])) for l in linhas[:500]})
            print(f"  {k}: tamanhos {tams}", file=sys.stderr)


def agregar(arquivos: list[Path], top: int = 10, ultimos: int = 15) -> dict:
    dot = defaultdict(lambda: {"f": defaultdict(lambda: [0, 0.0, 0.0, 0.0]), "cred": defaultdict(lambda: [0.0, 0]), "ult": []})
    sem_chave, total, mostrou = 0, 0, False
    for arq in arquivos:
        with open(arq, encoding="utf-8") as f:
            rd = csv.DictReader(f, delimiter=";")
            linhas = list(rd)
        m = mapear(rd.fieldnames or [])
        if not mostrou:
            diagnostico(rd.fieldnames or [], m, linhas)
            mostrou = True
        for r in linhas:
            total += 1
            k = chave(r, m)
            if not k:
                sem_chave += 1
                continue
            fo, e = fonte(r, m), num(r[m["emp"]]) if m["emp"] else 0.0
            a = dot[k]["f"][fo]
            a[0] += 1; a[1] += e
            a[2] += num(r[m["liq"]]) if m["liq"] else 0.0
            a[3] += num(r[m["pago"]]) if m["pago"] else 0.0
            nome, doc = credor(r, m)
            c = dot[k]["cred"][(nome, doc)]
            c[0] += e; c[1] += 1
            dot[k]["ult"].append([str(r[m["num"]]) if m["num"] else "", str(r[m["data"]])[:10] if m["data"] else "",
                                  nome, round(e, 2), str(r[m["proc"]]) if m["proc"] else "", fo])
    saida = {}
    for k, v in dot.items():
        cred = sorted(([n, d, round(x, 2), q] for (n, d), (x, q) in v["cred"].items()), key=lambda z: -z[2])
        ult = sorted(v["ult"], key=lambda z: _ordem_data(z[1]), reverse=True)[:ultimos]
        saida[k] = {"f": {fo: [a[0], round(a[1], 2), round(a[2], 2), round(a[3], 2)] for fo, a in v["f"].items()},
                    "cred": cred[:top], "ncred": len(cred), "ult": ult}
    print(f"  {total} empenhos lidos · {len(saida)} dotações · {sem_chave} sem chave completa", file=sys.stderr)
    return {"n": total, "sem_chave": sem_chave, "dot": saida}


def _ordem_data(s: str) -> str:
    """Aceita aaaa-mm-dd ou dd/mm/aaaa."""
    m = re.match(r"(\d{2})/(\d{2})/(\d{4})", s or "")
    return f"{m[3]}-{m[2]}-{m[1]}" if m else (s or "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--entrada", default="data/empenhos", help="pasta com as fotos diárias")
    ap.add_argument("--saida", default="site/empenhos26.json")
    a = ap.parse_args()
    fotos = sorted(p for p in Path(a.entrada).glob("*") if p.is_dir())
    if not fotos:
        sys.exit(f"Nenhuma foto de empenhos em {a.entrada}.")
    arquivos = sorted(fotos[-1].glob("empenhos_*.csv"))
    if not arquivos:
        sys.exit(f"Nenhum CSV em {fotos[-1]}.")
    res = agregar(arquivos)
    if not res["dot"]:
        sys.exit("Nenhuma dotação montada; veja o diagnóstico acima. JSON anterior mantido.")
    res["extr"] = fotos[-1].name
    res["fonte_dados"] = "API-SOF v4 (APILib, Prefeitura de São Paulo)"
    Path(a.saida).write_text(json.dumps(res, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"→ {a.saida} ({Path(a.saida).stat().st_size/1e6:.1f} MB)")


if __name__ == "__main__":
    main()
