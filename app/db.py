"""Camada de banco de dados.

- DATABASE_URL começando com postgres:// ou postgresql://  -> PostgreSQL (produção, dados permanentes)
- Qualquer outro valor (caminho de arquivo)                -> SQLite (uso local e testes)
"""
import os
import sqlite3
from datetime import datetime, timezone
from decimal import Decimal

import click
from flask import current_app, g

try:
    import psycopg
    from psycopg.rows import dict_row
except ImportError:  # SQLite continua funcionando sem o driver
    psycopg = None

from .versao import __version__

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

INTEGRITY_ERRORS = (sqlite3.IntegrityError,) + ((psycopg.IntegrityError,) if psycopg else ())


def is_postgres(url):
    return str(url).startswith(("postgres://", "postgresql://"))


def _limpa(row):
    return {k: (float(v) if isinstance(v, Decimal) else v) for k, v in dict(row).items()}


class DB:
    """Interface única para SQLite e PostgreSQL (SQL escrito com '?')."""

    def __init__(self, url):
        self.pg = is_postgres(url)
        if self.pg:
            if psycopg is None:
                raise RuntimeError("Instale psycopg para usar PostgreSQL.")
            self.conn = psycopg.connect(url, row_factory=dict_row)
        else:
            os.makedirs(os.path.dirname(os.path.abspath(url)), exist_ok=True)
            self.conn = sqlite3.connect(url, timeout=10)
            self.conn.row_factory = sqlite3.Row
            self.conn.execute("PRAGMA foreign_keys = ON")

    def _sql(self, sql):
        return sql.replace("?", "%s") if self.pg else sql

    def execute(self, sql, args=()):
        return self.conn.execute(self._sql(sql), args)

    def all(self, sql, args=()):
        return [_limpa(r) for r in self.execute(sql, args).fetchall()]

    def one(self, sql, args=()):
        r = self.execute(sql, args).fetchone()
        return _limpa(r) if r else None

    def script(self, texto):
        if self.pg:
            self.conn.execute(texto)
        else:
            self.conn.executescript(texto)

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        self.conn.close()


def get_db():
    if "db" not in g:
        g.db = DB(current_app.config["DATABASE"])
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def _schema(db):
    nome = "schema_postgres.sql" if db.pg else "schema_sqlite.sql"
    with current_app.open_resource(nome) as f:
        db.script(f.read().decode("utf8"))


def seed(db):
    for n in EQUIPAMENTOS:
        db.execute("INSERT INTO equipamento (nome) VALUES (?) ON CONFLICT (nome) DO NOTHING", (n,))
    # Mantém ativas só as máquinas da lista (as antigas ficam inativas, sem perder histórico)
    marc = ",".join("?" * len(EQUIPAMENTOS))
    db.execute(f"UPDATE equipamento SET ativo = CASE WHEN nome IN ({marc}) THEN 1 ELSE 0 END",
               EQUIPAMENTOS)
    for m in MOTIVOS:
        db.execute("INSERT INTO motivo (codigo, descricao, categoria, programado) VALUES (?, ?, ?, ?) "
                   "ON CONFLICT (codigo) DO NOTHING", m)
    db.execute("INSERT INTO versao_schema (versao, aplicada_em) VALUES (?, ?) "
               "ON CONFLICT (versao) DO NOTHING",
               (__version__, datetime.now(timezone.utc).replace(microsecond=0).isoformat()))
    db.commit()


def ensure_db():
    """Cria as tabelas que faltarem e a carga inicial. NUNCA apaga dados."""
    db = get_db()
    _schema(db)
    seed(db)
    close_db()


@click.command("init-db")
@click.option("--apagar", is_flag=True, help="Apaga TODAS as tabelas antes de recriar.")
def init_db_command(apagar):
    """Cria o banco. Com --apagar, recria do zero (perde os dados)."""
    db = get_db()
    if apagar:
        for t in ("parada", "motivo", "equipamento", "usuario", "versao_schema"):
            db.execute(f"DROP TABLE IF EXISTS {t}")
        db.commit()
    _schema(db)
    seed(db)
    click.echo(f"Banco pronto ({'PostgreSQL' if db.pg else 'SQLite'}) — versão {__version__}.")


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
