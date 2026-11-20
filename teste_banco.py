"""Teste das funcoes de usuario e perfil do banco.py (usa um banco temporario)."""
import sqlite3
import tempfile
from pathlib import Path

import banco

PERFIL = {"renda": 5000.0, "vinculo": "CLT", "tempo_vinculo": 24,
          "dividas_mensais": 300.0, "restricao": False, "entrada": 10000.0,
          "objetivo": "Veículo", "credito": 50000.0, "prazo": 60}
DECISAO = {"status": "Aprovado", "probabilidade": 0.8, "origem": "Modelo",
           "motivo": "Teste", "fatores": ["a", "b"]}

with tempfile.TemporaryDirectory() as pasta:
    # Aponta o banco para um arquivo temporario que some no final
    banco.CAMINHO_BANCO = Path(pasta) / "teste.db"
    banco.iniciar_banco()

    # 1) upsert: mesmo e-mail = mesmo id; o nome e atualizado
    id1 = banco.upsert_usuario("ana@exemplo.com", "Ana")
    id2 = banco.upsert_usuario("ana@exemplo.com", "Ana Silva")
    assert id1 == id2, "mesmo e-mail deveria dar o mesmo id"
    id3 = banco.upsert_usuario("bia@exemplo.com", "Bia")
    assert id3 != id1, "e-mail diferente deveria dar outro id"
    print("1) upsert_usuario OK")

    # 2) usuario sem perfil -> None
    assert banco.ultimo_perfil(id1) is None
    print("2) ultimo_perfil sem perfil devolve None OK")

    # 3) salva dois perfis; o ultimo deve ser o segundo
    banco.salvar_perfil(id1, PERFIL, DECISAO)
    segundo = dict(PERFIL, credito=60000.0, restricao=True)
    banco.salvar_perfil(id1, segundo, dict(DECISAO, status="Recusado"))
    ultimo = banco.ultimo_perfil(id1)
    assert ultimo["credito"] == 60000.0
    assert ultimo["restricao"] is True          # voltou como bool, nao como 1
    assert ultimo["status"] == "Recusado"
    print("3) salvar_perfil / ultimo_perfil OK:", ultimo)

    # 4) o banco recusa perfil de usuario que nao existe
    try:
        banco.salvar_perfil(9999, PERFIL, DECISAO)
        raise AssertionError("deveria ter recusado usuario inexistente")
    except sqlite3.IntegrityError:
        print("4) usuario inexistente foi recusado OK")

print("TUDO CERTO")