# Histórico de versões

O projeto segue o **Versionamento Semântico** (`MAJOR.MINOR.PATCH`):
- **MAJOR**: mudança que quebra compatibilidade (ex.: novo banco, API alterada)
- **MINOR**: nova funcionalidade compatível
- **PATCH**: correção de erro

A versão atual fica no arquivo `VERSION`. Ela aparece no rodapé do site e em `/api/v1/health`.

## [2.0.0] — 2026-10-23
### Adicionado
- Banco **PostgreSQL** para produção: os dados ficam salvos permanentemente (não se perdem em deploy ou reinício).
- Logo **Weise** no cabeçalho, no painel do operador (marca d'água), no rodapé e como ícone da aba.
- Controle de versão: arquivos `VERSION` e `CHANGELOG.md`, tabela `versao_schema` no banco, versão exibida no rodapé e na API.
- CI no GitHub Actions testando em SQLite **e** PostgreSQL.
- Teste que garante que os dados continuam após reiniciar o app.

### Alterado
- Título do sistema: **Paradas de Máquina**; layout com as cores da Weise (azul, preto e branco).
- Equipamentos: **Máquina 01 a Máquina 05**.
- Operador passou a ser **campo digitável**, com autocompletar.
- `flask init-db` não apaga mais os dados; para recriar do zero use `flask init-db --apagar`.
- `render.yaml`: `DATABASE_URL` agora é informada no painel do Render (não fica no GitHub).

### Removido
- Banco SQLite em `/tmp` no Render (perdia os dados a cada reinício).

## [1.0.0]
- Versão inicial (Projeto Integrador UNIVESP): apontamento PAROU/RETOMOU, catálogo de motivos, Pareto, MTTR e API REST.
