"""
banco.py - Alessandra (contrato v3.1, secoes 11, 12 e 13)

Cuida do banco SQLite (consorcio.db). Nenhuma regra de negocio aqui:
so guardar e ler dados.
"""
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

import pandas as pd

# --- Caminhos (sempre relativos a ESTE arquivo, nao a pasta do terminal) ---
PASTA_RAIZ = Path(__file__).resolve().parent
CAMINHO_BANCO = PASTA_RAIZ / "consorcio.db"
CAMINHO_CSV = PASTA_RAIZ / "consorcios.csv"

# Colunas do catalogo, na ordem do contrato (secao 13)
COLUNAS_CATALOGO = ["id", "categoria", "credito", "prazo", "parcela", "nome"]

# --- As 4 tabelas (secao 12). IF NOT EXISTS = so cria se ainda nao existir ---
SQL_CRIAR_TABELAS = """
CREATE TABLE IF NOT EXISTS usuarios (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    email     TEXT NOT NULL UNIQUE,
    nome      TEXT,
    criado_em TEXT
);

CREATE TABLE IF NOT EXISTS perfis (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id      INTEGER NOT NULL REFERENCES usuarios(id),
    criado_em       TEXT,
    renda           REAL,
    vinculo         TEXT,
    tempo_vinculo   INTEGER,
    dividas_mensais REAL,
    restricao       INTEGER,   -- SQLite nao tem True/False: guarda 1 ou 0
    entrada         REAL,
    objetivo        TEXT,
    credito         REAL,
    prazo           INTEGER,
    status          TEXT,      -- "Aprovado" ou "Recusado"
    probabilidade   REAL,      -- 0 a 1
    origem          TEXT,      -- "Politica" ou "Modelo"
    motivo          TEXT
);

CREATE TABLE IF NOT EXISTS consorcios (
    id        INTEGER PRIMARY KEY,
    categoria TEXT,
    credito   REAL,
    prazo     INTEGER,
    parcela   REAL,
    nome      TEXT
);

CREATE TABLE IF NOT EXISTS recomendacoes (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    perfil_id     INTEGER NOT NULL REFERENCES perfis(id),
    consorcio_id  INTEGER NOT NULL REFERENCES consorcios(id),
    score         REAL,
    justificativa TEXT,
    criado_em     TEXT
);
"""

# --- Perfis de demonstracao (FICTICIOS). Os valores de status/probabilidade
# sao ilustrativos, porque o modelo de IA ainda nao existe. ---
PERFIS_DEMO = [
    {
        "email": "demo1@exemplo.com", "nome": "Usuário demo 1",
        "perfil": {"renda": 8000.0, "vinculo": "Servidor público", "tempo_vinculo": 96,
                   "dividas_mensais": 500.0, "restricao": False, "entrada": 40000.0,
                   "objetivo": "Imóvel", "credito": 200000.0, "prazo": 180},
        "decisao": {"status": "Aprovado", "probabilidade": 0.93, "origem": "Modelo",
                    "motivo": "Parcela cabe na renda e o vínculo é estável"},
    },
    {
        "email": "demo2@exemplo.com", "nome": "Usuário demo 2",
        "perfil": {"renda": 3000.0, "vinculo": "Autônomo/MEI", "tempo_vinculo": 18,
                   "dividas_mensais": 300.0, "restricao": True, "entrada": 2000.0,
                   "objetivo": "Veículo", "credito": 60000.0, "prazo": 80},
        "decisao": {"status": "Recusado", "probabilidade": 0.0, "origem": "Política",
                    "motivo": "Há restrição no nome"},
    },
    {
        "email": "demo3@exemplo.com", "nome": "Usuário demo 3",
        "perfil": {"renda": 2500.0, "vinculo": "CLT", "tempo_vinculo": 12,
                   "dividas_mensais": 900.0, "restricao": False, "entrada": 0.0,
                   "objetivo": "Veículo", "credito": 50000.0, "prazo": 60},
        "decisao": {"status": "Recusado", "probabilidade": 0.0, "origem": "Política",
                    "motivo": "Comprometimento da renda acima de 40%"},
    },
    {
        "email": "demo4@exemplo.com", "nome": "Usuário demo 4",
        "perfil": {"renda": 2000.0, "vinculo": "Autônomo/MEI", "tempo_vinculo": 6,
                   "dividas_mensais": 200.0, "restricao": False, "entrada": 0.0,
                   "objetivo": "Veículo", "credito": 30000.0, "prazo": 60},
        "decisao": {"status": "Recusado", "probabilidade": 0.12, "origem": "Modelo",
                    "motivo": "Comprometimento perto do limite e sem entrada"},
    },
]


# ---------------------------------------------------------------------------
# Utilitarios internos (o "_" no comeco significa: so este arquivo usa)
# ---------------------------------------------------------------------------
@contextmanager
def _conexao():
    """Abre a conexao, entrega para o 'with', salva (commit) se deu certo,
    desfaz (rollback) se deu erro, e SEMPRE fecha no final."""
    conn = sqlite3.connect(CAMINHO_BANCO)
    conn.execute("PRAGMA foreign_keys = ON")  # faz o banco respeitar os "pertence a"
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _agora():
    """Data e hora atuais como texto, ex.: 2026-11-19T21:30:00"""
    return datetime.now().isoformat(timespec="seconds")


def _contar(conn, tabela):
    """Quantas linhas a tabela tem. (Nome da tabela vem do nosso codigo,
    nunca do usuario, por isso e seguro usar f-string aqui.)"""
    return conn.execute(f"SELECT COUNT(*) FROM {tabela}").fetchone()[0]


def _inserir_perfil(conn, usuario_id, perfil, decisao):
    """Grava um perfil + decisao. Sera reutilizada por salvar_perfil()."""
    cursor = conn.execute(
        """INSERT INTO perfis
           (usuario_id, criado_em, renda, vinculo, tempo_vinculo, dividas_mensais,
            restricao, entrada, objetivo, credito, prazo,
            status, probabilidade, origem, motivo)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (usuario_id, _agora(), perfil["renda"], perfil["vinculo"],
         perfil["tempo_vinculo"], perfil["dividas_mensais"], int(perfil["restricao"]),
         perfil["entrada"], perfil["objetivo"], perfil["credito"], perfil["prazo"],
         decisao["status"], decisao["probabilidade"], decisao["origem"],
         decisao["motivo"]),
    )
    return cursor.lastrowid  # numero (id) da linha que acabou de ser criada


def _carregar_catalogo(conn):
    """Le o consorcios.csv e coloca cada linha na tabela consorcios."""
    if not CAMINHO_CSV.exists():
        raise FileNotFoundError(f"Não achei o catálogo: {CAMINHO_CSV}")
    df = pd.read_csv(CAMINHO_CSV, encoding="utf-8-sig")  # aceita UTF-8 com ou sem BOM
    faltando = [c for c in COLUNAS_CATALOGO if c not in df.columns]
    if faltando:
        raise ValueError(f"consorcios.csv sem as colunas: {faltando}")
    conn.executemany(
        """INSERT INTO consorcios (id, categoria, credito, prazo, parcela, nome)
           VALUES (:id, :categoria, :credito, :prazo, :parcela, :nome)""",
        df[COLUNAS_CATALOGO].to_dict("records"),
    )


def _carregar_perfis_demo(conn):
    """Cria os usuarios e perfis de demonstracao."""
    for item in PERFIS_DEMO:
        conn.execute(
            "INSERT OR IGNORE INTO usuarios (email, nome, criado_em) VALUES (?, ?, ?)",
            (item["email"], item["nome"], _agora()),
        )
        usuario_id = conn.execute(
            "SELECT id FROM usuarios WHERE email = ?", (item["email"],)
        ).fetchone()[0]
        _inserir_perfil(conn, usuario_id, item["perfil"], item["decisao"])


# ---------------------------------------------------------------------------
# Funcoes do contrato (secao 11)
# ---------------------------------------------------------------------------
def iniciar_banco():
    """Cria as tabelas e, se estiverem vazias, carrega o catalogo e os
    perfis de demonstracao. Pode rodar quantas vezes quiser."""
    with _conexao() as conn:
        conn.executescript(SQL_CRIAR_TABELAS)
        if _contar(conn, "consorcios") == 0:
            _carregar_catalogo(conn)
        if _contar(conn, "perfis") == 0:
            _carregar_perfis_demo(conn)


def listar_consorcios():
    """Devolve o catalogo como DataFrame (tabela do pandas)."""
    with _conexao() as conn:
        return pd.read_sql_query(
            "SELECT id, categoria, credito, prazo, parcela, nome "
            "FROM consorcios ORDER BY id",
            conn,
        )

def upsert_usuario(email, nome):
    """Cria o usuario se o e-mail for novo; se ja existir, atualiza o nome.
    Devolve o id do usuario."""
    with _conexao() as conn:
        conn.execute(
            """INSERT INTO usuarios (email, nome, criado_em) VALUES (?, ?, ?)
               ON CONFLICT(email) DO UPDATE SET nome = excluded.nome""",
            (email, nome, _agora()),
        )
        return conn.execute(
            "SELECT id FROM usuarios WHERE email = ?", (email,)
        ).fetchone()[0]


def salvar_perfil(usuario_id, perfil, decisao):
    """Grava o perfil junto com a decisao. Devolve o id do perfil.
    (Quem chama deve validar o perfil antes: erro de preenchimento nao grava.)"""
    with _conexao() as conn:
        return _inserir_perfil(conn, usuario_id, perfil, decisao)


def ultimo_perfil(usuario_id):
    """Devolve o perfil mais recente do usuario como dicionario,
    ou None se ele nunca enviou um perfil."""
    with _conexao() as conn:
        cursor = conn.execute(
            "SELECT * FROM perfis WHERE usuario_id = ? ORDER BY id DESC LIMIT 1",
            (usuario_id,),
        )
        linha = cursor.fetchone()
        if linha is None:
            return None
        nomes_das_colunas = [coluna[0] for coluna in cursor.description]
    perfil = dict(zip(nomes_das_colunas, linha))
    perfil["restricao"] = bool(perfil["restricao"])  # volta de 1/0 para True/False
    return perfil

def salvar_recomendacoes(perfil_id, df):
    """Grava o ranking (o DataFrame do ranquear) na tabela recomendacoes.
    Chamar duas vezes para o mesmo perfil NAO duplica: o ranking antigo
    daquele perfil e trocado pelo novo. Devolve quantas linhas gravou."""
    if df is None or df.empty:
        return 0  # nada para gravar: nao mexe em nada

    agora = _agora()
    linhas = [
        (perfil_id, int(linha["id"]), float(linha["score"]),
         str(linha["justificativa"]), agora)
        for _, linha in df.iterrows()
    ]
    with _conexao() as conn:
        conn.execute("DELETE FROM recomendacoes WHERE perfil_id = ?", (perfil_id,))
        conn.executemany(
            """INSERT INTO recomendacoes
               (perfil_id, consorcio_id, score, justificativa, criado_em)
               VALUES (?, ?, ?, ?, ?)""",
            linhas,
        )
    return len(linhas)


def excluir_dados_usuario(usuario_id):
    """Apaga os dados de UM usuario, nesta ordem: 1) as recomendacoes dos
    perfis dele, 2) os perfis, 3) o usuario. Tudo ou nada: se algo falhar,
    nada e apagado. Devolve quantas linhas saiu de cada tabela."""
    with _conexao() as conn:
        recomendacoes = conn.execute(
            """DELETE FROM recomendacoes
               WHERE perfil_id IN (SELECT id FROM perfis WHERE usuario_id = ?)""",
            (usuario_id,),
        ).rowcount
        perfis = conn.execute(
            "DELETE FROM perfis WHERE usuario_id = ?", (usuario_id,)
        ).rowcount
        usuarios = conn.execute(
            "DELETE FROM usuarios WHERE id = ?", (usuario_id,)
        ).rowcount
    return {"recomendacoes": recomendacoes, "perfis": perfis, "usuarios": usuarios}

# Roda so quando voce executa "python banco.py" (nao quando outro arquivo importa)
if __name__ == "__main__":
    iniciar_banco()
    with _conexao() as conn:
        for tabela in ["usuarios", "perfis", "consorcios", "recomendacoes"]:
            print(f"{tabela}: {_contar(conn, tabela)} linhas")
    print(listar_consorcios())