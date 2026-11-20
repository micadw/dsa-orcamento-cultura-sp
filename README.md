# Orçamento da Cultura em São Paulo — da proposta ao pagamento

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.24399304.svg)](https://doi.org/10.5281/zenodo.24399304) · **Site:** https://micadw.github.io/dsa-orcamento-cultura-sp/

> **Status:** em andamento · piloto (sprint 1)

Piloto de site para acesso e visualização dos dados públicos de planejamento, empenho e execução orçamentária da Prefeitura de São Paulo, com busca pelo **código da dotação**, resumos estatísticos, taxas de execução, série histórica 2003–2026 e acesso aos dados brutos. Estudo de caso: **Secretaria Municipal de Cultura (órgão 25)**, Fundo Municipal de Cultura (79) e a função 13 (Cultura) em todos os órgãos.

**Pergunta de pesquisa (provisória):** quanto o orçamento da cultura aprovado na LOA diverge do efetivamente executado em 2003–2026, e onde essa divergência se concentra (créditos adicionais, congelamentos, restos a pagar, emendas)?

**Palavras-chave:** orçamento público; execução orçamentária; política cultural; transparência; dados abertos; São Paulo.

## Como reproduzir

```bash
python -m src.coleta_seplan          # bases abertas da SEPLAN → site/data26.json e site/hist.json
python -m src.coleta_sof --teste     # API-SOF v4 (exige SOF_KEY e SOF_SECRET no ambiente)
python -m http.server -d site        # local: http://localhost:8000 · publicado: https://micadw.github.io/dsa-orcamento-cultura-sp/
```

Notebooks: `notebooks/001_coleta.ipynb`, `notebooks/002_eda.ipynb`
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/micadw/dsa-orcamento-cultura-sp/blob/main/notebooks/002_eda.ipynb)

## Fontes (somente dados abertos)

- SEPLAN/PMSP — Base de Dados da Execução Orçamentária (diária) e consolidada 2003–2026; QDD; PLOA/LOA
- SF/PMSP — API-SOF v4 (vitrine pública APILib, uso como cidadão, sujeita aos Termos de Uso)
- Câmara Municipal de São Paulo — emendas e pareceres do PLOA
- Diário Oficial da Cidade — decretos de crédito adicional

Ver `docs/benchmarking.md` para projetos semelhantes e o backlog.

## Aviso institucional

Projeto pessoal com dados abertos; não representa posição oficial da PMSP. Nenhuma informação obtida no exercício de cargo público é usada. CPF de credores pessoa física é mascarado (LGPD).

## Licença e citação

Código sob [MIT](LICENSE). Dados tratados, site, figuras e textos sob [CC BY 4.0](LICENSE-DATA.md). Para citar, use o arquivo [`CITATION.cff`](CITATION.cff) (botão "Cite this repository" no GitHub) ou o DOI de todas as versões [10.5281/zenodo.24399304](https://doi.org/10.5281/zenodo.24399304) (v0.1.0: [10.5281/zenodo.24399305](https://doi.org/10.5281/zenodo.24399305)).

---

## English summary

**Culture budget in São Paulo, from proposal to payment.** A pilot tool to search the City of São Paulo's budget by appropriation code (*dotação*), with execution rates (approved → adjusted → committed → paid), a 2003–2026 time series and raw-data access, using the Secretariat of Culture as a case study. Data are collected daily from the city's open budget files (SEPLAN) and the public SOF API. Built with open data only; does not represent an official position of the City of São Paulo.
