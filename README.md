# SAS — Sistema de Apontamento de Paradas

Aplicação web para registro e análise de paradas de máquina no chão de fábrica.
O operador aciona o botão **PAROU**, o sistema cria o evento com carimbo de tempo
automático e exige a classificação do **motivo**; ao acionar **RETOMOU**, a duração
é calculada e o registro é fechado para análise (Pareto, MTTR, programado × não programado).

Projeto Integrador — UNIVESP.

---

## Requisitos do trabalho e onde estão atendidos

| Requisito | Implementação | Arquivos |
|---|---|---|
| Framework web | Flask 3 (*application factory* + *blueprints*) | `app/__init__.py`, `app/api.py` |
| Banco de dados | SQLite relacional, 4 tabelas em 3FN, chaves estrangeiras e `CHECK` | `app/schema.sql`, `app/db.py` |
| Script web (JavaScript) | JS puro (ES2021): `fetch`, cronômetro, validação, render dinâmico | `app/static/js/app.js`, `dashboard.js` |
| Nuvem | Dockerfile, `Procfile` (gunicorn) e `render.yaml` com disco persistente e *health check* | `Dockerfile`, `render.yaml`, `Procfile` |
| Uso de API | API REST própria versionada (`/api/v1`), consumida pelo front-end | `app/api.py` |
| Acessibilidade | WCAG 2.1 AA: `lang`, *skip link*, ARIA, `aria-live`, foco visível, contraste, alvos ≥ 44 px, tabela alternativa ao gráfico | `app/templates/*`, `app/static/css/style.css` |
| Controle de versão | Repositório Git + `.gitignore` + pipeline CI no GitHub Actions | `.github/workflows/ci.yml` |
| Testes | 15 testes automatizados com pytest (regras de negócio, erros e acessibilidade) | `tests/test_api.py` |
| Análise de dados (opcional) | Pareto com percentual acumulado, KPIs e MTTR + gráfico Chart.js | `/dashboard`, `app/api.py` |

## Como executar

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

export FLASK_APP=app          # Windows: set FLASK_APP=app
flask init-db                 # cria o esquema e o catálogo de motivos
flask run                     # http://127.0.0.1:5000
```

Testes: `pytest -v`
Docker: `docker build -t sas . && docker run -p 8000:8000 sas`

## Modelo de dados

```
usuario ──┐
equipamento ──┼──< parada >── motivo
```

`parada` guarda `inicio`, `fim`, `duracao_min` e `status`
(`ABERTA` → `AGUARDANDO_MOTIVO` → `FECHADA`). A regra impede duas paradas
simultâneas no mesmo equipamento.

## API REST

| Método | Rota | Descrição |
|---|---|---|
| GET | `/api/v1/health` | Verificação de saúde (usada pelo provedor de nuvem) |
| GET | `/api/v1/equipamentos` | Equipamentos ativos |
| GET | `/api/v1/motivos` | Catálogo de motivos padronizados |
| GET | `/api/v1/paradas` | Lista com filtros `status`, `equipamento`, `desde`, `ate` |
| POST | `/api/v1/paradas` | Abre a parada (botão PAROU) |
| PATCH | `/api/v1/paradas/{id}` | Informa motivo e observação |
| POST | `/api/v1/paradas/{id}/retomar` | Fecha a parada e calcula a duração |
| GET | `/api/v1/analytics/pareto` | Minutos por motivo + % acumulado |
| GET | `/api/v1/analytics/resumo` | KPIs consolidados |

Exemplo:

```bash
curl -X POST http://localhost:5000/api/v1/paradas \
     -H "Content-Type: application/json" \
     -d '{"equipamento_id": 1, "usuario_id": 1}'
```

## Catálogo de motivos

Carregado no `seed` com os códigos padronizados da planta, agrupados por
categoria (MAN, OPE, QUA, UTI, ADM) e classificados em **Programado** ou
**Não programado** — o que permite separar disponibilidade planejada de perdas.

## Controle de versão sugerido

`main` (estável) ← `develop` ← `feature/*`. Commits no padrão *Conventional
Commits* (`feat:`, `fix:`, `test:`, `docs:`). Cada *pull request* roda a suíte de
testes automaticamente no GitHub Actions.

## Evoluções previstas

Integração com o historiador PI para captura automática do tempo de parada,
autenticação por crachá/QR Code e exportação para o Power BI.


## Alterações (out/2026)
- Equipamentos fixos: **Máquina 01 a Máquina 10** (carga inicial em `app/db.py`).
- **Operador digitável**: o operador digita o nome; o sistema cadastra na 1ª vez e reaproveita depois (autocompletar). O nome fica salvo no aparelho.
- O banco é criado automaticamente ao iniciar o app (não precisa rodar `flask init-db` no Render).
- `render.yaml` ajustado ao plano free (sem disco; banco em `/tmp`, **apagado a cada deploy/reinício**).
  Para guardar os dados: `plan: starter` + bloco `disk` com `mountPath: /var/data` e `DATABASE_URL=/var/data/sas.sqlite`.
- Power BI: Obter dados → Web → `https://SUA-URL.onrender.com/api/v1/paradas`.
