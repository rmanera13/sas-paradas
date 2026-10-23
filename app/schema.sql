PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS usuario (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL UNIQUE COLLATE NOCASE CHECK (length(trim(nome)) >= 2)
);

CREATE TABLE IF NOT EXISTS equipamento (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    nome  TEXT NOT NULL UNIQUE,
    ativo INTEGER NOT NULL DEFAULT 1 CHECK (ativo IN (0, 1))
);

CREATE TABLE IF NOT EXISTS motivo (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo     TEXT NOT NULL UNIQUE,
    descricao  TEXT NOT NULL,
    categoria  TEXT NOT NULL CHECK (categoria IN ('MAN','OPE','QUA','UTI','ADM')),
    programado INTEGER NOT NULL CHECK (programado IN (0, 1))
);

CREATE TABLE IF NOT EXISTS parada (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    equipamento_id INTEGER NOT NULL REFERENCES equipamento(id),
    usuario_id     INTEGER NOT NULL REFERENCES usuario(id),
    motivo_id      INTEGER REFERENCES motivo(id),
    inicio         TEXT NOT NULL,
    fim            TEXT,
    duracao_min    REAL CHECK (duracao_min IS NULL OR duracao_min >= 0),
    observacao     TEXT,
    status         TEXT NOT NULL DEFAULT 'ABERTA'
                   CHECK (status IN ('ABERTA','AGUARDANDO_MOTIVO','FECHADA'))
);

-- Impede duas paradas simultaneas no mesmo equipamento
CREATE UNIQUE INDEX IF NOT EXISTS ux_parada_aberta
    ON parada(equipamento_id) WHERE fim IS NULL;
CREATE INDEX IF NOT EXISTS ix_parada_inicio ON parada(inicio);
