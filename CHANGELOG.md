# Histórico de versões

O projeto segue o **Versionamento Semântico** (`MAJOR.MINOR.PATCH`):
- **MAJOR**: mudança que quebra compatibilidade (ex.: novo banco, API alterada)
- **MINOR**: nova funcionalidade compatível
- **PATCH**: correção de erro

A versão atual fica no arquivo `VERSION`. Ela aparece no rodapé do site e em `/api/v1/health`.

## [2.1.0] — 2026-10-25
### Adicionado
- Indicador **MTBF** (tempo médio entre falhas), geral e por máquina, no dashboard e na rota `/api/v1/analytics/mtbf?dias=N`.
  - MTBF = horas em operação ÷ nº de falhas no período (7, 30, 90 dias ou 12 meses).
  - Falha = parada com motivo **não programado**. Paradas programadas não contam como falha, mas descontam do tempo em operação.
  - Mostra também o MTTR das falhas por máquina.
- Exportação da base em **Excel** (`/api/v1/export.xlsx`), com as abas Paradas, MTBF, Pareto e Resumo. Os horários vêm em horário de Brasília e as colunas já vêm com filtro.
- Testes do MTBF e do Excel (`tests/test_v21.py`).

### Alterado
- O botão "Baixar base (JSON)" do dashboard virou **"Baixar base (Excel)"**. A rota JSON `/api/v1/paradas` continua disponível para o Power BI.
- Novas dependências: `openpyxl` (Excel) e `tzdata` (fuso horário).

## [2.0.1] — 2026-10-23
### Corrigido
- Falha no deploy com PostgreSQL (`UniqueViolation: pg_type_typname_nsp_index`, chave `usuario`):
  os 2 workers do gunicorn criavam as tabelas ao mesmo tempo.
  - A criação do banco agora usa *advisory lock* do PostgreSQL (um worker por vez).
  - O gunicorn sobe com `--preload`, então o banco é preparado uma única vez.

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
