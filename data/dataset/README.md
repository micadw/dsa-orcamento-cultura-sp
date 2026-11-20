# Orçamento da Cultura em São Paulo — base tratada v0.1.0

Recorte da base aberta de execução orçamentária da Prefeitura de São Paulo (SEPLAN/SOF) para a cultura, com série 2003–2026 corrigida pelo IPCA.

| Arquivo | Conteúdo |
|---|---|
| `execucao_2026_cultura.csv` | Uma linha por dotação/registro, exercício 2026 (01/01/2026–30/11/2026, extração 19/11/2026) |
| `serie_2003_2026.csv` | Totais anuais nominais e reais (IPCA, base 2026-10) para SMC (órgão 25), função 13 e Fundo Municipal de Cultura (79) |
| `ipca_fatores.csv` | Fatores de correção (BCB/SGS 433) |
| `datapackage.json` | Descrição no padrão Frictionless / Fiscal Data Package |

**Método.** Valores em R$. Real = nominal × fator, fator = IPCA de 2026-10 ÷ IPCA de dezembro do ano (ano corrente: 1). O Fundo Municipal de Cultura não aparece como órgão próprio na base consolidada de 2018 a 2025; 2026 é exercício parcial.

**Proteção de dados (LGPD).** A base não contém CPF, CNPJ nem dados de credores. Por minimização, nomes de pessoa física que aparecem na descrição oficial de ações orçamentárias (ex.: "Organização: …") foram substituídos por `[pessoa física]`; nomes de pessoas jurídicas foram mantidos. Os demais campos reproduzem a publicação oficial.

**Fontes.** SEPLAN/PMSP — Base de Dados da Execução Orçamentária (dados abertos; Política Municipal de Dados Abertos, Lei 17.901/2023); BCB/SGS série 433 (IPCA/IBGE).

**Licença.** CC BY 4.0 (tratamento). Dados de origem conforme as fontes. Código: https://github.com/micadw/dsa-orcamento-cultura-sp (MIT) · DOI do software: 10.5281/zenodo.24399304.

**Autor.** Amilcar Ferraz Farina (LAB_MicaDataWise) · ORCID 0009-0000-5263-4919. Projeto pessoal com dados abertos; não representa posição oficial da Prefeitura de São Paulo.
