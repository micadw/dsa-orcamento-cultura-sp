# Contexto para o Claude

- Projeto pessoal e acadêmico de Mica (micadw) sobre o orçamento da cultura na PMSP. Somente dados abertos e canais públicos (vitrine APILib como cidadão). Nunca usar acesso interno ao SOF nem informação obtida no cargo.
- Legislação e classificação: apenas brasileiras (Lei 4.320/64, LRF, LOM-SP, MCASP, manual de classificação da despesa da PMSP). Projetos estrangeiros servem só como referência de interface.
- Credenciais só por variáveis de ambiente / GitHub Secrets (`SOF_KEY`, `SOF_SECRET`). Nunca commitar `.env` nem dados brutos (`data/raw`).
- Mascarar CPF de pessoa física antes de qualquer publicação.
- Commits em Conventional Commits em português (`feat(site): ...`, `fix(coleta): ...`).
- Funções reutilizáveis em `src/`; notebooks importam de `src/`.
- Revisões mínimas e com registro claro das mudanças.
