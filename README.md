# Orçamento da Cultura em São Paulo — da proposta ao pagamento

> **Status:** rascunho · repositório privado · piloto (sprint 1)

Piloto de site para acesso e visualização dos dados públicos de planejamento, empenho e execução orçamentária da Prefeitura de São Paulo, com busca pelo **código da dotação**, resumos estatísticos, taxas de execução, série histórica 2003–2026 e acesso aos dados brutos. Estudo de caso: **Secretaria Municipal de Cultura (órgão 25)**, Fundo Municipal de Cultura (79) e a função 13 (Cultura) em todos os órgãos.

**Pergunta de pesquisa (provisória):** quanto o orçamento da cultura aprovado na LOA diverge do efetivamente executado em 2003–2026, e onde essa divergência se concentra (créditos adicionais, congelamentos, restos a pagar, emendas)?

**Palavras-chave:** orçamento público; execução orçamentária; política cultural; transparência; dados abertos; São Paulo.

## Como reproduzir

```bash
python -m src.coleta_seplan          # bases abertas da SEPLAN → site/data26.json e site/hist.json
python -m src.coleta_sof --teste     # API-SOF v4 (exige SOF_KEY e SOF_SECRET no ambiente)
python -m http.server -d site        # abre o site em http://localhost:8000
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

## Licenças

Código: MIT. Textos e figuras: CC BY 4.0. Dados: conforme licença da fonte.
