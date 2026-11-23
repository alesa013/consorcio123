"""Testes da parte 1 do recomendador.py."""
from recomendador import calcular_indicadores, validar_perfil

BOM = {"renda": 5000.0, "vinculo": "CLT", "tempo_vinculo": 24,
       "dividas_mensais": 300.0, "restricao": False, "entrada": 10000.0,
       "objetivo": "Veículo", "credito": 50000.0, "prazo": 60}


def com(**mudancas):
    """Copia o perfil bom trocando so os campos pedidos."""
    return dict(BOM, **mudancas)


def deve_dar_erro(perfil, quantos=1):
    erros = validar_perfil(perfil)
    assert len(erros) == quantos, f"esperava {quantos} erro(s), veio: {erros}"
    return erros


# --- perfil correto ---
assert validar_perfil(BOM) == []
print("1) perfil correto OK")

# --- cada regra da secao 7 ---
print("   ", deve_dar_erro(com(renda=0))[0])
deve_dar_erro(com(renda=250000))
deve_dar_erro(com(renda="5000"))
deve_dar_erro(com(renda=True))
deve_dar_erro(com(renda=float("nan")))
deve_dar_erro(com(dividas_mensais=-1))
deve_dar_erro(com(tempo_vinculo=601))
deve_dar_erro(com(tempo_vinculo=12.5))
deve_dar_erro(com(credito=1000, entrada=0))
print("   ", deve_dar_erro(com(entrada=50000))[0])   # entrada = credito
deve_dar_erro(com(entrada=-5))
deve_dar_erro(com(vinculo="Outro"))
deve_dar_erro(com(objetivo="Casa"))
deve_dar_erro(com(prazo=48))
deve_dar_erro(com(restricao="não"))
print("2) regras de validacao OK")

# --- varios erros de uma vez, campo faltando, tipo errado ---
deve_dar_erro(com(renda=0, prazo=48, objetivo="Casa"), quantos=3)
semrenda = dict(BOM)
del semrenda["renda"]
assert "renda" in deve_dar_erro(semrenda)[0]
deve_dar_erro("isto nao e um dicionario")
print("3) varios erros, campo ausente e tipo errado OK")

# --- indicadores (conta feita a mao: (50000-10000)*1,15/60 = 766,67) ---
ind = calcular_indicadores(BOM)
assert round(ind["parcela_estimada"], 2) == 766.67
assert round(ind["comprometimento"], 4) == 0.2133   # (300 + 766,67) / 5000
assert round(ind["entrada_pct"], 4) == 0.2
assert round(ind["credito_renda"], 4) == 0.8333     # 50000 / 60000
print("4) indicadores OK:", ind)

# --- ranquear (secao 10): usa o consorcios.csv como catalogo, sem banco ---
from pathlib import Path

import pandas as pd

from recomendador import COLUNAS_RANKING, ranquear

catalogo = pd.read_csv(Path(__file__).resolve().parent / "consorcios.csv")
PERFIL_RANK = {"renda": 4500.0, "vinculo": "CLT", "tempo_vinculo": 36,
               "dividas_mensais": 500.0, "restricao": False, "entrada": 20000.0,
               "objetivo": "Imóvel", "credito": 120000.0, "prazo": 120}

ranking = ranquear(PERFIL_RANK, catalogo)
assert list(ranking.columns) == COLUNAS_RANKING
assert (ranking["categoria"] == "Imóvel").all()        # so a categoria do objetivo
assert list(ranking["id"]) == [1, 2, 3, 4], list(ranking["id"])
assert ranking["score"].is_monotonic_decreasing        # do melhor para o pior
assert ranking["score"].between(0, 100).all()
# Contas feitas a mao (secao 10):
#  id 1: credito 50*(1-40000/120000)=33,33 + prazo igual=25
#        + parcela (500+766,67)/4500=28% (<=40%)=25            -> 83,3
#  id 2: credito 50*(1-30000/120000)=37,5 + prazo 25*(1-60/120)=12,5
#        + parcela (500+958,33)/4500=32% (<=40%)=25            -> 75,0
assert ranking.loc[0, "score"] == 83.3
assert ranking.loc[1, "score"] == 75.0
assert ranking.loc[2, "score"] == 33.4   # credito 108% acima (0) + prazo 12,5 + parcela 46,6% (20,9)
print("5) ranquear: categoria, ordem e contas feitas a mao OK")

# Parcela acima do limite perde pontos, mas nao zera de uma vez
veiculo = dict(PERFIL_RANK, objetivo="Veículo", renda=2000.0, dividas_mensais=300.0,
               credito=50000.0, prazo=80, entrada=5000.0)
rank_v = ranquear(veiculo, catalogo)
assert rank_v.loc[0, "id"] == 6                        # credito e prazo iguais ao pedido
assert rank_v.loc[0, "score"] == 93.2                  # 50 + 25 + 25*(1-(0,509-0,4)/0,4)
print("6) ranquear: parcela acima do limite perde pontos OK")

# Justificativa em texto simples, e catalogo sem a categoria -> tabela vazia
assert ranking.loc[0, "justificativa"].startswith("Este consórcio tem")
assert "R$" in ranking.loc[0, "justificativa"] and "%" in ranking.loc[0, "justificativa"]
vazio = ranquear(PERFIL_RANK, catalogo[catalogo["categoria"] != "Imóvel"])
assert vazio.empty and list(vazio.columns) == COLUNAS_RANKING
print("7) ranquear: justificativa e catalogo sem a categoria OK")

# --- sugerir_ajustes (secao 11): usa a decidir() de verdade (precisa do modelo) ---
from recomendador import _ajustes_numericos, decidir, sugerir_ajustes

REF = {"renda": 4500.0, "vinculo": "CLT", "tempo_vinculo": 36,
       "dividas_mensais": 500.0, "restricao": False, "entrada": 20000.0,
       "objetivo": "Imóvel", "credito": 120000.0, "prazo": 120}
APROVADO = {"renda": 8000.0, "vinculo": "Servidor público", "tempo_vinculo": 96,
            "dividas_mensais": 500.0, "restricao": False, "entrada": 40000.0,
            "objetivo": "Imóvel", "credito": 200000.0, "prazo": 180}

# Perfil ja aprovado: nada a sugerir
assert decidir(APROVADO)["status"] == "Aprovado"
assert sugerir_ajustes(APROVADO) == []
print("8) sugerir_ajustes: perfil aprovado nao recebe sugestoes OK")

# So a restricao barra: a sugestao e regularizar
so_restricao = dict(REF, restricao=True, credito=80000.0, entrada=30000.0, dividas_mensais=100.0)
texto = sugerir_ajustes(so_restricao)
assert len(texto) == 1 and "restrição" in texto[0] and "aprovado" in texto[0], texto
# Renda abaixo do minimo: nenhum ajuste resolve, e o texto explica
texto = sugerir_ajustes(dict(REF, renda=1200.0, dividas_mensais=0.0))
assert len(texto) == 1 and "mínimo de R$ 1.500,00" in texto[0], texto
print("9) sugerir_ajustes: restricao e renda abaixo do minimo OK")

# Perfil recusado pelo MODELO: toda sugestao tem que aprovar de verdade
assert decidir(REF)["status"] == "Recusado", "o perfil de referencia deveria ser recusado"
ajustes = _ajustes_numericos(REF)
assert ajustes, "deveria haver pelo menos um ajuste"
for campo, valor in ajustes.items():
    assert decidir(dict(REF, **{campo: valor}))["status"] == "Aprovado", (campo, valor)
assert len(sugerir_ajustes(REF)) == len(ajustes)       # um texto por ajuste
# O credito sugerido e o MAIOR (mais perto do pedido) que aprova: 1.000 a mais recusa
if "credito" in ajustes:
    assert ajustes["credito"] < REF["credito"]
    assert decidir(dict(REF, credito=ajustes["credito"] + 1000))["status"] == "Recusado"
print("10) sugerir_ajustes: toda sugestao foi testada e aprova OK:", ajustes)

print("TUDO CERTO")