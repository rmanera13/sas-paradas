import os
import sqlite3
import click
from flask import current_app, g

EQUIPAMENTOS = [f"Máquina {i:02d}" for i in range(1, 6)]  # Máquina 01 ... Máquina 05

MOTIVOS = [
    # codigo, descricao, categoria, programado
    ("MAN-01", "Quebra mecânica", "MAN", 0),
    ("MAN-02", "Falha elétrica / automação", "MAN", 0),
    ("MAN-03", "Manutenção preventiva", "MAN", 1),
    ("OPE-01", "Setup / troca de formato", "OPE", 1),
    ("OPE-02", "Ajuste operacional", "OPE", 0),
    ("OPE-03", "Falta de operador", "OPE", 0),
    ("OPE-04", "Limpeza programada", "OPE", 1),
    ("QUA-01", "Problema de qualidade", "QUA", 0),
    ("UTI-01", "Falta de energia", "UTI", 0),
    ("UTI-02", "Falta de ar comprimido / vapor", "UTI", 0),
    ("ADM-01", "Falta de material", "ADM", 0),
    ("ADM-02", "Sem programação", "ADM", 1),
    ("ADM-03", "Reunião / treinamento", "ADM", 1),
]


def get_db():
    if "db" not in g:
        path = current_app.config["DATABASE"]
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        g.db = sqlite3.connect(path, timeout=10)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def seed(db):
    db.executemany("INSERT OR IGNORE INTO equipamento (nome) VALUES (?)",
                   [(n,) for n in EQUIPAMENTOS])
    # Mantem ativas somente as maquinas da lista (desativa as antigas, sem apagar historico)
    db.execute("UPDATE equipamento SET ativo = CASE WHEN nome IN (%s) THEN 1 ELSE 0 END"
               % ",".join("?" * len(EQUIPAMENTOS)), EQUIPAMENTOS)
    db.executemany("INSERT OR IGNORE INTO motivo (codigo, descricao, categoria, programado) "
                   "VALUES (?, ?, ?, ?)", MOTIVOS)
    db.commit()


def ensure_db():
    """Cria o esquema se nao existir e garante a carga inicial (idempotente)."""
    db = get_db()
    with current_app.open_resource("schema.sql") as f:
        db.executescript(f.read().decode("utf8"))
    seed(db)
    close_db()


def init_db():
    db = get_db()
    db.executescript("DROP TABLE IF EXISTS parada; DROP TABLE IF EXISTS motivo; "
                     "DROP TABLE IF EXISTS equipamento; DROP TABLE IF EXISTS usuario;")
    with current_app.open_resource("schema.sql") as f:
        db.executescript(f.read().decode("utf8"))
    seed(db)


@click.command("init-db")
def init_db_command():
    """Recria o banco do zero (APAGA os dados)."""
    init_db()
    click.echo("Banco recriado com Máquina 01-05 e catálogo de motivos.")


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
