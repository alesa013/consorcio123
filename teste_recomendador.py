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

print("TUDO CERTO")