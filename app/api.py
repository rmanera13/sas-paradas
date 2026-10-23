from datetime import datetime, timezone
from flask import Blueprint, jsonify, request
from .db import get_db, INTEGRITY_ERRORS
from .versao import __version__

bp = Blueprint("api", __name__, url_prefix="/api/v1")

SELECT_PARADA = """
SELECT p.id, p.equipamento_id, e.nome AS equipamento, u.nome AS operador,
       p.motivo_id, m.codigo AS motivo_codigo, m.descricao AS motivo,
       m.categoria, m.programado, p.inicio, p.fim, p.duracao_min,
       p.observacao, p.status
FROM parada p
JOIN equipamento e ON e.id = p.equipamento_id
JOIN usuario u     ON u.id = p.usuario_id
LEFT JOIN motivo m ON m.id = p.motivo_id
"""


def agora():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def erro(msg, code=400):
    return jsonify({"erro": msg}), code


def buscar(pid):
    return get_db().one(SELECT_PARADA + " WHERE p.id = ?", (pid,))


def operador_id(nome):
    """Operador e digitado: cria o cadastro na primeira vez e reaproveita depois."""
    db = get_db()
    achou = db.one("SELECT id FROM usuario WHERE lower(nome) = lower(?)", (nome,))
    if achou:
        return achou["id"]
    return db.one("INSERT INTO usuario (nome) VALUES (?) RETURNING id", (nome,))["id"]


@bp.get("/health")
def health():
    db = get_db()
    db.one("SELECT 1 AS ok")
    return jsonify({"status": "ok", "versao": __version__,
                    "banco": "postgresql" if db.pg else "sqlite"})


@bp.get("/equipamentos")
def equipamentos():
    rows = get_db().all("""
        SELECT e.id, e.nome,
               (SELECT p.id FROM parada p WHERE p.equipamento_id = e.id AND p.fim IS NULL) AS parada_aberta_id
        FROM equipamento e WHERE e.ativo = 1 ORDER BY e.nome""")
    return jsonify(rows)


@bp.get("/motivos")
def motivos():
    return jsonify(get_db().all("SELECT * FROM motivo ORDER BY codigo"))


@bp.get("/operadores")
def operadores():
    rows = get_db().all("SELECT nome FROM usuario ORDER BY nome")
    return jsonify([r["nome"] for r in rows])


@bp.get("/paradas")
def listar():
    sql, args = SELECT_PARADA + " WHERE 1=1", []
    if request.args.get("status"):
        sql += " AND p.status = ?"; args.append(request.args["status"])
    if request.args.get("equipamento"):
        sql += " AND p.equipamento_id = ?"; args.append(request.args["equipamento"])
    if request.args.get("desde"):
        sql += " AND p.inicio >= ?"; args.append(request.args["desde"])
    if request.args.get("ate"):
        sql += " AND p.inicio <= ?"; args.append(request.args["ate"])
    sql += " ORDER BY p.inicio DESC, p.id DESC"
    return jsonify(get_db().all(sql, args))


@bp.post("/paradas")
def abrir():
    dados = request.get_json(silent=True) or {}
    eq = dados.get("equipamento_id")
    nome = (dados.get("operador") or "").strip()
    if not eq:
        return erro("Informe o equipamento.")
    if len(nome) < 2:
        return erro("Digite o nome do operador (mínimo 2 caracteres).")
    if len(nome) > 80:
        return erro("Nome do operador muito longo (máximo 80).")
    db = get_db()
    if not db.one("SELECT 1 AS ok FROM equipamento WHERE id = ? AND ativo = 1", (eq,)):
        return erro("Equipamento não encontrado.", 404)
    try:
        novo = db.one(
            "INSERT INTO parada (equipamento_id, usuario_id, inicio, status) "
            "VALUES (?, ?, ?, 'ABERTA') RETURNING id",
            (eq, operador_id(nome), agora()))
        db.commit()
    except INTEGRITY_ERRORS:
        db.rollback()
        return erro("Já existe uma parada aberta neste equipamento.", 409)
    return jsonify(buscar(novo["id"])), 201


@bp.patch("/paradas/<int:pid>")
def classificar(pid):
    p = buscar(pid)
    if not p:
        return erro("Parada não encontrada.", 404)
    if p["status"] == "FECHADA":
        return erro("Parada já fechada.", 409)
    dados = request.get_json(silent=True) or {}
    mid = dados.get("motivo_id")
    db = get_db()
    if not mid or not db.one("SELECT 1 AS ok FROM motivo WHERE id = ?", (mid,)):
        return erro("Informe um motivo válido.")
    novo = "FECHADA" if p["status"] == "AGUARDANDO_MOTIVO" else "ABERTA"
    db.execute("UPDATE parada SET motivo_id = ?, observacao = ?, status = ? WHERE id = ?",
               (mid, (dados.get("observacao") or "").strip()[:500] or None, novo, pid))
    db.commit()
    return jsonify(buscar(pid))


@bp.post("/paradas/<int:pid>/retomar")
def retomar(pid):
    p = buscar(pid)
    if not p:
        return erro("Parada não encontrada.", 404)
    if p["fim"]:
        return erro("Parada já retomada.", 409)
    fim = agora()
    dur = round((datetime.fromisoformat(fim) - datetime.fromisoformat(p["inicio"])).total_seconds() / 60, 2)
    status = "FECHADA" if p["motivo_id"] else "AGUARDANDO_MOTIVO"
    db = get_db()
    db.execute("UPDATE parada SET fim = ?, duracao_min = ?, status = ? WHERE id = ?",
               (fim, dur, status, pid))
    db.commit()
    return jsonify(buscar(pid))


@bp.get("/analytics/pareto")
def pareto():
    rows = get_db().all("""
        SELECT m.codigo, m.descricao, m.programado,
               ROUND(CAST(SUM(p.duracao_min) AS NUMERIC), 2) AS minutos,
               COUNT(*) AS ocorrencias
        FROM parada p JOIN motivo m ON m.id = p.motivo_id
        WHERE p.status = 'FECHADA'
        GROUP BY m.id, m.codigo, m.descricao, m.programado ORDER BY minutos DESC""")
    total = sum(r["minutos"] or 0 for r in rows)
    acum, out = 0, []
    for i, r in enumerate(rows, 1):
        acum += r["minutos"] or 0
        d = dict(r)
        d["pct_acumulado"] = round(acum / total * 100, 1) if total else round(i / len(rows) * 100, 1)
        out.append(d)
    return jsonify(out)


@bp.get("/analytics/resumo")
def resumo():
    db = get_db()
    d = db.one("""
        SELECT COUNT(*) AS total_paradas,
               COALESCE(ROUND(CAST(SUM(p.duracao_min) AS NUMERIC), 2), 0) AS minutos_total,
               COALESCE(ROUND(CAST(AVG(p.duracao_min) AS NUMERIC), 2), 0) AS mttr_min,
               COALESCE(ROUND(CAST(SUM(CASE WHEN m.programado = 1 THEN p.duracao_min END) AS NUMERIC), 2), 0) AS min_programado,
               COALESCE(ROUND(CAST(SUM(CASE WHEN m.programado = 0 THEN p.duracao_min END) AS NUMERIC), 2), 0) AS min_nao_programado
        FROM parada p JOIN motivo m ON m.id = p.motivo_id
        WHERE p.status = 'FECHADA'""")
    d["paradas_abertas"] = db.one(
        "SELECT COUNT(*) AS n FROM parada WHERE status <> 'FECHADA'")["n"]
    return jsonify(d)
