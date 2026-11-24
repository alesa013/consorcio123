# teste_consistencia_politica.py
# Confere se as duas versões da regra da política dão sempre a mesma resposta:
#   - decidir()                 em recomendador.py      (um perfil por vez)
#   - recusado_pela_politica()  em dados_sinteticos.py  (tabela inteira)
# Escrito pela Pessoa A. Só compara resultados: não altera nada.
# Como rodar:  python teste_consistencia_politica.py   (pode levar até 1 minuto)

import pandas as pd

import dados_sinteticos
import recomendador

N = 2000
SEMENTE_TESTE = 123  # diferente da semente do treino (42): são perfis "novos"


def montar_perfil(linha):
    """Converte uma linha da tabela no dicionário do contrato (tipos certos)."""
    return {
        "renda": float(linha["renda"]),
        "vinculo": str(linha["vinculo"]),
        "tempo_vinculo": int(round(linha["tempo_vinculo"])),
        "dividas_mensais": float(linha["dividas_mensais"]),
        "restricao": bool(linha["restricao"]),
        "entrada": float(linha["entrada"]),
        "objetivo": str(linha["objetivo"]),
        "credito": float(linha["credito"]),
        "prazo": int(linha["prazo"]),
    }


def pela_tabela(perfil):
    """Resposta da versão em tabela para UM perfil (tabela de 1 linha)."""
    resposta = dados_sinteticos.recusado_pela_politica(pd.DataFrame([perfil]))
    return bool(resposta.iloc[0])


def pela_decidir(perfil):
    """Resposta da decidir(): True se a política recusou."""
    return recomendador.decidir(perfil)["origem"] == "Política"


# ---------------------------------------------------------------------------
print(f"\n=== 1. {N} perfis novos (semente {SEMENTE_TESTE}) ===")
df = dados_sinteticos.gerar_perfis(N, SEMENTE_TESTE)
perfis = [montar_perfil(linha) for linha in df.to_dict("records")]

# decidir() espera perfis já validados: separa os válidos
validos = [p for p in perfis if recomendador.validar_perfil(p) == []]
print(f"{len(validos)} perfis válidos de {len(perfis)} gerados.")
if not validos:
    raise SystemExit("Nenhum perfil válido para comparar. Mande esta mensagem para a Pessoa A.")

tabela = pd.DataFrame(validos)
por_tabela = dados_sinteticos.recusado_pela_politica(tabela)

divergencias = []
recusados = 0
for i, perfil in enumerate(validos):
    a = pela_decidir(perfil)
    b = bool(por_tabela.iloc[i])
    recusados += a
    if a != b:
        divergencias.append((perfil, a, b))

print(f"Recusados pela política: {recusados} de {len(validos)} "
      f"({recusados / len(validos) * 100:.1f}%)")
print(f"Divergências entre as duas versões: {len(divergencias)}")
for perfil, a, b in divergencias[:5]:
    print(f"  decidir={a} | tabela={b} | perfil={perfil}")

# ---------------------------------------------------------------------------
print("\n=== 2. Casos de fronteira ===")
BASE = {"renda": 4500.0, "vinculo": "CLT", "tempo_vinculo": 36,
        "dividas_mensais": 500.0, "restricao": False, "entrada": 20000.0,
        "objetivo": "Imóvel", "credito": 120000.0, "prazo": 120}


def com(**mudancas):
    novo = dict(BASE)
    novo.update(mudancas)
    return novo


# (descrição, perfil, o que o contrato espera: True = recusa pela política)
FRONTEIRA = [
    ("renda 1.499,99 (abaixo do mínimo)",
     com(renda=1499.99, dividas_mensais=0.0, credito=20000.0, entrada=10000.0, prazo=60), True),
    ("renda 1.500,00 (igual ao mínimo: NÃO recusa)",
     com(renda=1500.0, dividas_mensais=0.0, credito=20000.0, entrada=10000.0, prazo=60), False),
    ("renda 1.500,01 (acima do mínimo)",
     com(renda=1500.01, dividas_mensais=0.0, credito=20000.0, entrada=10000.0, prazo=60), False),
    ("comprometimento exatamente 40% (igual ao limite: NÃO recusa)",
     com(renda=5000.0, dividas_mensais=850.0, credito=120000.0, entrada=0.0, prazo=120), False),
    ("comprometimento um pouco acima de 40%",
     com(renda=5000.0, dividas_mensais=851.0, credito=120000.0, entrada=0.0, prazo=120), True),
    ("restrição no nome com tudo o mais perfeito",
     com(renda=8000.0, vinculo="Servidor público", restricao=True), True),
]

fronteira_ok = True
for descricao, perfil, esperado in FRONTEIRA:
    erros = recomendador.validar_perfil(perfil)
    if erros:
        print(f"  (perfil inválido, ignorado) {descricao}: {erros}")
        continue
    a, b = pela_decidir(perfil), pela_tabela(perfil)
    concordam = a == b
    bate_contrato = a == esperado
    fronteira_ok = fronteira_ok and concordam
    print(f"  {'OK      ' if concordam else 'DIVERGE '}{descricao}: "
          f"decidir={a} | tabela={b} | contrato espera={esperado}"
          f"{'' if bate_contrato else '   <-- difere do contrato'}")

# ---------------------------------------------------------------------------
print("\n=== RESULTADO ===")
if not divergencias and fronteira_ok:
    print("As duas versões da regra da política CONCORDAM em todos os casos.")
else:
    print("As duas versões DIVERGEM. Copie tudo o que apareceu acima e mande para a Pessoa A.")