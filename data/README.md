# Dados

Dados grandes **nunca** entram no git.

| Camada | Onde | Conteúdo |
|---|---|---|
| bronze | Google Drive (pasta do projeto, Nível 4/5) | CSV originais da SEPLAN e fotos diárias da API-SOF (`data/raw/`, `data/empenhos/`) |
| prata | `site/*.json` (no git, pequenos) | Recorte da Cultura gerado por `src/coleta_seplan.py` |
| pública | Zenodo (DOI, quando `status: publicado`) | Fiscal Data Package descrito em `datapackage.json` |

Fontes: SEPLAN/PMSP (execução orçamentária, dados abertos); SF/PMSP API-SOF v4; Câmara Municipal de São Paulo; Diário Oficial da Cidade.
