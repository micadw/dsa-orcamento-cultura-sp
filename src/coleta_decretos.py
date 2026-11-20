#!/usr/bin/env python3
"""
Créditos adicionais de 2026 (decretos, portarias e resoluções) no Catálogo de Legislação
Municipal da Prefeitura (legislacao.prefeitura.sp.gov.br), ligados à dotação.

Fonte pública, sem login. Cada ato traz tabelas com o código da ação
(órgão.unidade.função.subfunção.programa.projeto-atividade) e, na linha seguinte, a natureza
com a fonte (ex.: 33503900.00.1.500.7016.1 → natureza 3.3.50.39.00, fonte 00), mais o valor.
O artigo que precede a tabela diz o sentido: "suplementar"/"especial" soma; "cobertura" anula.

Coleta educada e incremental: identificação honesta, uma requisição por segundo, repete só
429/5xx, e só baixa os atos que ainda não estão no cache (data/decretos/atos_<ano>.json).
Nenhum dado pessoal é guardado (só número, data, códigos e valores).
"""
import argparse, json, re, sys, time, urllib.error, urllib.parse, urllib.request
from html.parser import HTMLParser
from pathlib import Path

from src.coleta_seplan import FUNCAO_CULTURA, ORGAOS_CULTURA

BASE = "https://legislacao.prefeitura.sp.gov.br"
UA = "dsa-orcamento-cultura-sp (pesquisa, dados abertos; github.com/micadw/dsa-orcamento-cultura-sp)"
ASSUNTO = "abre crédito adicional"
MESES = {m: i for i, m in enumerate("janeiro fevereiro marco abril maio junho julho agosto setembro outubro novembro dezembro".split(), 1)}
RE_ACAO = re.compile(r"^(\d{2})\.(\d{2})\.(\d{2})\.(\d{3})\.(\d{4})\.(\d{4})$")
RE_NAT = re.compile(r"^(\d{8})\.(\d{2})\.")
RE_SLUG = re.compile(r"^/leis/(?P<tipo>[a-z0-9-]+?)-(?P<num>\d+)-de-(?P<d>\d{1,2})-de-(?P<m>[a-z]+)-de-(?P<a>\d{4})$")


def baixar(url: str, tentativas: int = 3) -> str:
    for i in range(tentativas):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and i < tentativas - 1:
                time.sleep(10 * (i + 1)); continue
            raise
        except urllib.error.URLError:
            if i < tentativas - 1:
                time.sleep(10 * (i + 1)); continue
            raise


class _Leitor(HTMLParser):
    """Guarda, em ordem, o último parágrafo antes de cada tabela e as linhas da tabela."""
    def __init__(self):
        super().__init__(); self.tabelas, self._par, self._buf = [], "", []
        self._em_tab = 0; self._linhas = None; self._linha = None; self._cel = None; self._links = []

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self._em_tab += 1
            if self._em_tab == 1:
                self._linhas = []
        elif self._em_tab and tag == "tr":
            self._linha = []
        elif self._em_tab and tag in ("td", "th"):
            self._cel = []
        elif not self._em_tab and tag == "p":
            self._buf = []
        elif tag == "a":
            href = dict(attrs).get("href") or ""
            if href.startswith("/leis/"):
                self._links.append(href.split("?")[0])

    def handle_endtag(self, tag):
        if tag == "table" and self._em_tab:
            self._em_tab -= 1
            if self._em_tab == 0:
                self.tabelas.append((self._par, self._linhas))
        elif self._em_tab and tag in ("td", "th") and self._cel is not None:
            self._linha.append(" ".join("".join(self._cel).split())); self._cel = None
        elif self._em_tab and tag == "tr" and self._linha is not None:
            self._linhas.append(self._linha); self._linha = None
        elif not self._em_tab and tag == "p":
            t = " ".join("".join(self._buf).split())
            if t:
                self._par = t

    def handle_data(self, data):
        if self._cel is not None:
            self._cel.append(data)
        elif not self._em_tab:
            self._buf.append(data)


def valor(s: str) -> float:
    s = (s or "").strip()
    return float(s.replace(".", "").replace(",", ".")) if re.fullmatch(r"-?[\d.]+,\d{2}", s) else 0.0


def ler_ato(html: str) -> list[list]:
    """Lista de [código_completo, sinal(+1/-1), valor] de todas as tabelas do ato."""
    lt = _Leitor(); lt.feed(html)
    itens = []
    for par, linhas in lt.tabelas:
        p = par.lower()
        if "cobertura" in p or "anula" in p:
            sinal = -1
        elif "suplementar" in p or "especial" in p or "extraordin" in p or "aberto" in p:
            sinal = 1
        else:
            continue
        acao = None
        for ln in linhas:
            if not ln:
                continue
            c = ln[0].strip()
            if RE_ACAO.match(c):
                acao = c
            elif acao and (m := RE_NAT.match(c)):
                n = m[1]
                cod = f"{acao}.{n[0]}.{n[1]}.{n[2:4]}.{n[4:6]}.{n[6:8]}.{m[2]}"
                itens.append([cod, sinal, valor(ln[-1] if len(ln) > 1 else "")])
    return itens


def listar(ano: int, conhecidos: set, max_pag: int = 200, pausa: float = 1.0) -> list[str]:
    """Percorre a busca (mais recentes primeiro) até sair do ano ou achar uma página só de atos já vistos."""
    q = urllib.parse.urlencode({"assunto": ASSUNTO, "ordem": "desc"})
    novos = []
    for n in range(1, max_pag + 1):
        url = f"{BASE}/busca?{q}" if n == 1 else f"{BASE}/busca/pg/{n}?{q}"
        lt = _Leitor(); lt.feed(baixar(url)); time.sleep(pausa)
        slugs = list(dict.fromkeys(s for s in lt._links if RE_SLUG.match(s)))
        if not slugs:
            break
        do_ano = [s for s in slugs if RE_SLUG.match(s)["a"] == str(ano)]
        novos += [s for s in do_ano if s not in conhecidos]
        if not do_ano and all(int(RE_SLUG.match(s)["a"]) < ano for s in slugs):
            break
        if do_ano and all(s in conhecidos for s in do_ano) and n > 2:
            break
    return list(dict.fromkeys(novos))


def rotulo(slug: str) -> tuple[str, str]:
    m = RE_SLUG.match(slug)
    t = m["tipo"].split("-")
    base = {"decreto": "Decreto", "portaria": "Portaria", "resolucao": "Resolução"}.get(t[0], t[0].capitalize())
    sigla = "-".join(x.upper() for x in t[1:][-2:] if len(x) <= 6 and x not in ("de", "da", "do", "das", "dos", "e")) if len(t) > 1 else ""
    tipo = f"{base} {sigla}".strip()
    data = f"{m['a']}-{MESES.get(m['m'], 0):02d}-{int(m['d']):02d}"
    return f"{tipo} nº {int(m['num']):,}".replace(",", "."), data


def da_cultura(cod: str) -> bool:
    p = cod.split(".")
    return p[2] == FUNCAO_CULTURA or p[0] in ORGAOS_CULTURA


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ano", type=int, default=2026)
    ap.add_argument("--cache", default=None)
    ap.add_argument("--saida", default=None)
    ap.add_argument("--max", type=int, default=1500, help="máximo de atos novos por execução")
    a = ap.parse_args()
    cache_p = Path(a.cache or f"data/decretos/atos_{a.ano}.json")
    saida_p = Path(a.saida or f"site/decretos{str(a.ano)[2:]}.json")
    cache = json.loads(cache_p.read_text(encoding="utf-8")) if cache_p.exists() else {}
    novos = listar(a.ano, set(cache))[: a.max]
    print(f"{len(novos)} atos novos de {a.ano} (já no cache: {len(cache)})", file=sys.stderr)
    for i, s in enumerate(novos, 1):
        try:
            cache[s] = ler_ato(baixar(BASE + s))
        except Exception as e:
            print(f"  falhou {s}: {e}", file=sys.stderr); continue
        time.sleep(1.0)
        if i % 50 == 0:
            print(f"  {i}/{len(novos)}", file=sys.stderr)
    cache_p.parent.mkdir(parents=True, exist_ok=True)
    cache_p.write_text(json.dumps(cache, ensure_ascii=False, separators=(",", ":"), sort_keys=True), encoding="utf-8")

    dot, atos = {}, set()
    for s, itens in cache.items():
        nome, data = rotulo(s)
        for cod, sinal, v in itens:
            if da_cultura(cod):
                dot.setdefault(cod, []).append([nome, data, sinal, v, s]); atos.add(s)
    for v in dot.values():
        v.sort(key=lambda z: z[1], reverse=True)
    res = {"extr": time.strftime("%Y-%m-%d"), "ano": a.ano, "atos_lidos": len(cache), "atos_cultura": len(atos),
           "fonte": "Catálogo de Legislação Municipal — legislacao.prefeitura.sp.gov.br", "dot": dot}
    saida_p.write_text(json.dumps(res, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"→ {saida_p}: {len(atos)} atos com dotações da cultura, {len(dot)} dotações", file=sys.stderr)


if __name__ == "__main__":
    main()
