# Benchmarking — projetos abertos com propósito semelhante

Levantamento feito em 20/11/2026. Projetos estrangeiros servem **apenas como referência de interface e lógica de dados**; leis, classificação orçamentária e ciclo do orçamento seguem exclusivamente a legislação brasileira (Lei 4.320/64, LRF, LOM-SP, MCASP, Manual de Classificação da Despesa da Cidade de São Paulo).

## Nacionais

| Projeto | Código | O que fazem | O que aproveitamos |
|---|---|---|---|
| **Orçamentômetro** (Agência Mural, 2026) | GitHub (Python/Pandas, execução diária) | Baixa a planilha oficial da PMSP todo dia, calcula executado por subprefeitura e secretaria, separa emendas; busca por CEP | Mesmo padrão de coleta diária e baixo custo (GitHub Actions); ler o código antes de duplicar esforço |
| **Cuidando do Meu Bairro** (Colab-EACH-USP, 2012–) | GitLab `cuidandodomeubairro` (inclui `esic-livre`) | Mapa da execução com cores por status (planejado, empenhado, liquidado); geocodifica despesas pelo texto | Código de cores por estágio; ideia de gerar pedido de LAI quando o dado falta; literatura acadêmica (SBC, relatório CC BY 4.0) |
| **Querido Diário** (Open Knowledge Brasil) | GitHub `okfn-brasil` (Scrapy, FastAPI, MIT) | Raspagem e busca em diários oficiais municipais, API pública com limite de 60 req/min | Etiqueta de uso de API, documentação comunitária; para a capital usar a API *Diario_Oficial* da APILib |
| Prêmio SOF/ENAP 2022 — séries históricas municipais | artigo | Método para séries de execução municipal pós-1989 com correção pelo IPCA | Metodologia de deflação da série 2003–2026 |
| Revista da CGU (2023) — conformidade dos portais municipais | artigo | Avalia dados de execução nos portais das capitais | Referencial teórico de transparência |

## Internacionais (só interface e lógica)

| Projeto | Código | Ideias de interface/lógica |
|---|---|---|
| **BudgetKey / Open Budget** (Hasadna, Israel) | GitHub `OpenBudget` | Busca textual em 20+ anos de orçamento; percurso do dinheiro "da dotação ao beneficiário"; base de *alterações orçamentárias* como dado próprio; tutorial em formato de conversa; Sankey; servidor MCP sobre a API |
| **USAspending.gov** (Tesouro dos EUA) | GitHub `fedspendingtransparency` (React + Django) | *Spending Explorer* com drill-down função → órgão → natureza; ligação entre gasto "por conta" e gasto "por contrato/beneficiário" (≈ dotação ↔ empenho); perfil por órgão com "status dos recursos"; download customizado com filtros |
| **Vulekamali** (Tesouro da África do Sul + OpenUp) | GitHub `vulekamali` (Django + CKAN + OpenSpending) | Portal de dados (catálogo) separado do portal de histórias; página por órgão reunindo dados e documentos oficiais; ênfase em acessibilidade |
| **OpenSpending / Fiscal Data Package** (Open Knowledge) | GitHub `openspending`, specs Frictionless | Padrão aberto `datapackage.json` para dados de orçamento e gasto; facilita reuso, Zenodo e citação |

## Decisões de arquitetura

- **Manter site estático** (GitHub Pages/Quarto + JSON/Parquet) com coleta diária no GitHub Actions, como o Orçamentômetro. Evitar a pilha pesada de BudgetKey/USAspending (Elasticsearch, Kubernetes, CKAN) enquanto o projeto for individual.
- **Publicar os dados como Fiscal Data Package** (`data/datapackage.json`), o que também serve à versão com DOI no Zenodo.

## Backlog priorizado (MoSCoW)

**Must — sprints 2 e 3**
1. ✅ (sprint 2, 2026-11-20) Ligação dotação ↔ empenho com drill-down até o credor (API-SOF `/empenhos`; órgãos 25, 79, 85 e 15) — USAspending/BudgetKey. Pendente: `/liquidacoes` e FUNDURB/subprefeituras (função 13).
2. Ficha da dotação com linha do tempo: PLOA → emenda → LOA → créditos/congelamentos → empenho → pagamento → restos a pagar — BudgetKey.
3. Valores reais (IPCA) além de nominais — ENAP.
4. Endereço compartilhável por dotação (`#dot-25-10-13-392-4032-6364`).
5. `datapackage.json` (Fiscal Data Package) e download filtrado real (no GitHub Pages, sem a restrição do sandbox).
6. Glossário embutido (tooltips) a partir do Glossário/Caderno do Orçamento da SEPLAN.

**Should**
7. Sankey órgão → programa → natureza → credor.
8. Alertas automáticos por regra (ex.: atualizado < 50% do orçado, como o Fundo Municipal de Cultura em 2026).
9. Comparação ano a ano da mesma ação.

**Could**
10. Gerador de pedido de LAI quando um dado não existir em aberto — Cuidando do Meu Bairro.
11. Servidor MCP sobre os dados do projeto — BudgetKey.
12. Regionalização (Detalhamento da Ação) e busca por subprefeitura.

**Won't (por ora)**: contas de usuário, CKAN próprio, Elasticsearch.
