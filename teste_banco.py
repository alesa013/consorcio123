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
    
    # 5) salvar_recomendacoes: grava as linhas; chamar de novo nao duplica
    perfil_id = banco.ultimo_perfil(id1)["id"]
    ranking = banco.listar_consorcios().head(3).copy()  # o catalogo serve de ranking de teste
    ranking["score"] = [90.0, 80.0, 70.0]
    ranking["justificativa"] = ["a", "b", "c"]
    assert banco.salvar_recomendacoes(perfil_id, ranking) == 3
    assert banco.salvar_recomendacoes(perfil_id, ranking) == 3   # de novo: troca, nao soma
    with banco._conexao() as conn:
        assert banco._contar(conn, "recomendacoes") == 3
    assert banco.salvar_recomendacoes(perfil_id, ranking.head(0)) == 0  # vazio: nao mexe
    with banco._conexao() as conn:
        assert banco._contar(conn, "recomendacoes") == 3
    print("5) salvar_recomendacoes OK")

    # 6) recomendacao de perfil que nao existe e recusada
    try:
        banco.salvar_recomendacoes(9999, ranking)
        raise AssertionError("deveria ter recusado perfil inexistente")
    except sqlite3.IntegrityError:
        print("6) perfil inexistente foi recusado OK")

    # 7) excluir_dados_usuario: apaga so os dados daquele usuario
    id_cia = banco.upsert_usuario("cia@exemplo.com", "Cia")
    perfil_cia = banco.salvar_perfil(id_cia, PERFIL, DECISAO)
    banco.salvar_recomendacoes(perfil_cia, ranking)
    with banco._conexao() as conn:
        assert banco._contar(conn, "recomendacoes") == 6      # 3 da Ana + 3 da Cia
    apagados = banco.excluir_dados_usuario(id_cia)
    assert apagados == {"recomendacoes": 3, "perfis": 1, "usuarios": 1}, apagados
    assert banco.ultimo_perfil(id_cia) is None
    with banco._conexao() as conn:
        assert banco._contar(conn, "recomendacoes") == 3      # as da Ana continuam
        sobrou = conn.execute("SELECT COUNT(*) FROM usuarios WHERE id = ?", (id_cia,)).fetchone()[0]
    assert sobrou == 0
    assert banco.ultimo_perfil(id1) is not None                # a Ana continua la
    zeros = {"recomendacoes": 0, "perfis": 0, "usuarios": 0}
    assert banco.excluir_dados_usuario(9999) == zeros          # usuario inexistente: nada acontece
    print("7) excluir_dados_usuario OK")
    
    # 8) resumo_dashboard: so agregados (usa um banco novo, sem perfis de demonstracao)
    banco.CAMINHO_BANCO = Path(pasta) / "resumo.db"
    with banco._conexao() as conn:
        conn.executescript(banco.SQL_CRIAR_TABELAS)
    vazios = {"total": 0, "aprovados": 0}
    esperado_vazio = {"total_perfis": 0, "total_usuarios": 0, "taxa_aprovacao": 0.0,
                      "probabilidade_media": 0.0,
                      "por_objetivo": {"Imóvel": vazios, "Veículo": vazios, "Serviço": vazios}}
    assert banco.resumo_dashboard() == esperado_vazio, banco.resumo_dashboard()

    u = banco.upsert_usuario("x@exemplo.com", "X")
    banco.salvar_perfil(u, dict(PERFIL, objetivo="Imóvel"),
                        dict(DECISAO, status="Aprovado", probabilidade=0.9))
    banco.salvar_perfil(u, dict(PERFIL, objetivo="Imóvel"),
                        dict(DECISAO, status="Recusado", probabilidade=0.0))
    banco.salvar_perfil(u, dict(PERFIL, objetivo="Serviço"),
                        dict(DECISAO, status="Aprovado", probabilidade=0.7))
    r = banco.resumo_dashboard()
    assert r["total_perfis"] == 3 and r["total_usuarios"] == 1
    assert abs(r["taxa_aprovacao"] - 2 / 3) < 1e-9
    assert abs(r["probabilidade_media"] - (0.9 + 0.0 + 0.7) / 3) < 1e-9
    assert r["por_objetivo"] == {"Imóvel": {"total": 2, "aprovados": 1},
                                 "Veículo": {"total": 0, "aprovados": 0},
                                 "Serviço": {"total": 1, "aprovados": 1}}, r
    assert "x@exemplo.com" not in str(r)       # nada individual no resultado
    print("8) resumo_dashboard OK")

print("TUDO CERTO")