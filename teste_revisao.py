# teste_revisao.py - revisão automática do código da Pessoa B contra o contrato v3.3
# Escrito pela Pessoa A. Só chama funções e compara resultados: não altera nada.
# Como rodar:  python teste_revisao.py

import importlib
import time
from pathlib import Path

import recomendador

PASTA = Path(__file__).resolve().parent

# ----- Perfis de referência (os mesmos do README) -----
P1 = {"renda": 8000.0, "vinculo": "Servidor público", "tempo_vinculo": 96,
      "dividas_mensais": 500.0, "restricao": False, "entrada": 40000.0,
      "objetivo": "Imóvel", "credito": 200000.0, "prazo": 180}
P2 = {"renda": 4500.0, "vinculo": "CLT", "tempo_vinculo": 36,
      "dividas_mensais": 500.0, "restricao": False, "entrada": 20000.0,
      "objetivo": "Imóvel", "credito": 120000.0, "prazo": 120}
P3 = {**P1, "restricao": True}
P4 = {"renda": 1200.0, "vinculo": "CLT", "tempo_vinculo": 36,
      "dividas_mensais": 0.0, "restricao": False, "entrada": 4000.0,
      "objetivo": "Imóvel", "credito": 20000.0, "prazo": 60}
P5 = {"renda": 4500.0, "vinculo": "CLT", "tempo_vinculo": 36,
      "dividas_mensais": 500.0, "restricao": False, "entrada": 0.0,
      "objetivo": "Imóvel", "credito": 400000.0, "prazo": 36}
P6 = {"renda": 6000.0, "vinculo": "Servidor público", "tempo_vinculo": 60,
      "dividas_mensais": 400.0, "restricao": False, "entrada": 20000.0,
      "objetivo": "Veículo", "credito": 80000.0, "prazo": 60}
P7 = {"renda": 5000.0, "vinculo": "CLT", "tempo_vinculo": 48,
      "dividas_mensais": 300.0, "restricao": False, "entrada": 5000.0,
      "objetivo": "Serviço", "credito": 20000.0, "prazo": 36}

resultados = []  # guarda True ou False de cada verificação
divergencias = []  # guarda o texto das que falharam


def rodar(descricao, funcao):
    """Roda uma verificação. Se devolver True, escreve OK; se devolver False
    ou der erro, escreve DIVERGE."""
    try:
        ok = bool(funcao())
        detalhe = ""
    except Exception as erro:
        ok = False
        detalhe = f"  (erro: {type(erro).__name__}: {erro})"
    resultados.append(ok)
    linha = ("OK       " if ok else "DIVERGE  ") + descricao + detalhe
    print(linha)
    if not ok:
        divergencias.append(linha)


def com(perfil, **mudancas):
    """Cópia do perfil com alguns campos trocados."""
    novo = dict(perfil)
    novo.update(mudancas)
    return novo


def perto(a, b, tolerancia):
    return abs(float(a) - float(b)) <= tolerancia


def eh_valido(perfil):
    return recomendador.validar_perfil(perfil) == []


def eh_invalido(perfil):
    erros = recomendador.validar_perfil(perfil)
    return isinstance(erros, list) and len(erros) > 0


# ---------------------------------------------------------------------------
print("\n=== 1. Constantes (contrato, seção 6) ===")
ESPERADAS = {
    "RENDA_MINIMA": 1500,
    "LIMITE_COMPROMETIMENTO": 0.40,
    "COMPROMETIMENTO_IDEAL": 0.20,
    "NOTA_MINIMA": 60,
    "ENTRADA_REF": 0.20,
    "LIMITE_CREDITO_RENDA": 6,
    "TAXA_ADMIN": 0.15,
    "COMPROMETIMENTO_NOTA_ZERO": 0.80,
}


def achar_constante(nome):
    """Procura a constante nos arquivos da Pessoa B."""
    for nome_modulo in ["recomendador", "dados_sinteticos", "modelo"]:
        try:
            modulo = importlib.import_module(nome_modulo)
        except Exception:
            continue
        if hasattr(modulo, nome):
            return getattr(modulo, nome)
    raise LookupError(f"constante {nome} não encontrada")


for nome, esperado in ESPERADAS.items():
    rodar(f"{nome} = {esperado}",
          lambda n=nome, e=esperado: perto(achar_constante(n), e, 1e-9))

# ---------------------------------------------------------------------------
print("\n=== 2. Indicadores do perfil P2 (contrato, seção 5) ===")
ind = recomendador.calcular_indicadores(P2)
rodar("parcela_estimada = 958,33",
      lambda: perto(ind["parcela_estimada"], 958.33, 0.01))
rodar("comprometimento = 32,4%",
      lambda: perto(ind["comprometimento"], 0.3241, 0.0005))
rodar("entrada_pct = 16,7%",
      lambda: perto(ind["entrada_pct"], 0.1667, 0.0005))
rodar("credito_renda = 2,22",
      lambda: perto(ind["credito_renda"], 2.2222, 0.0005))

# ---------------------------------------------------------------------------
print("\n=== 3. Validação (contrato, seção 7) ===")
rodar("perfil P2 válido", lambda: eh_valido(P2))
rodar("perfil P1 válido", lambda: eh_valido(P1))
rodar("limite: crédito 5.000 aceito", lambda: eh_valido(com(P2, credito=5000.0, entrada=0.0)))
rodar("limite: crédito 600.000 aceito", lambda: eh_valido(com(P2, credito=600000.0)))
rodar("limite: renda 200.000 aceita", lambda: eh_valido(com(P2, renda=200000.0)))
rodar("limite: tempo 0 e 600 aceitos",
      lambda: eh_valido(com(P2, tempo_vinculo=0)) and eh_valido(com(P2, tempo_vinculo=600)))
rodar("limite: dívidas 0 e 100.000 aceitas",
      lambda: eh_valido(com(P2, dividas_mensais=0.0)) and eh_valido(com(P2, dividas_mensais=100000.0)))
rodar("recusa: renda 0", lambda: eh_invalido(com(P2, renda=0.0)))
rodar("recusa: renda 200.001", lambda: eh_invalido(com(P2, renda=200001.0)))
rodar("recusa: dívidas negativas", lambda: eh_invalido(com(P2, dividas_mensais=-1.0)))
rodar("recusa: dívidas 100.001", lambda: eh_invalido(com(P2, dividas_mensais=100001.0)))
rodar("recusa: tempo negativo", lambda: eh_invalido(com(P2, tempo_vinculo=-1)))
rodar("recusa: tempo 601", lambda: eh_invalido(com(P2, tempo_vinculo=601)))
rodar("recusa: crédito 4.999", lambda: eh_invalido(com(P2, credito=4999.0, entrada=0.0)))
rodar("recusa: crédito 600.001", lambda: eh_invalido(com(P2, credito=600001.0)))
rodar("recusa: entrada igual ao crédito", lambda: eh_invalido(com(P2, entrada=120000.0)))
rodar("recusa: entrada maior que o crédito", lambda: eh_invalido(com(P2, entrada=130000.0)))
rodar("recusa: vínculo desconhecido", lambda: eh_invalido(com(P2, vinculo="Outro")))
rodar("recusa: objetivo desconhecido", lambda: eh_invalido(com(P2, objetivo="Casa")))
rodar("recusa: prazo 24", lambda: eh_invalido(com(P2, prazo=24)))
rodar("recusa: restrição como texto", lambda: eh_invalido(com(P2, restricao="Sim")))

# ---------------------------------------------------------------------------
print("\n=== 4. Decisão (contrato, seção 8) ===")
CHAVES = {"status", "probabilidade", "origem", "motivo", "fatores"}


def decisao_ok(perfil, status, origem):
    d = recomendador.decidir(perfil)
    return d["status"] == status and d["origem"] == origem


def formato_ok(perfil):
    d = recomendador.decidir(perfil)
    return (set(d.keys()) == CHAVES
            and d["origem"] in ("Política", "Modelo")
            and 0.0 <= d["probabilidade"] <= 1.0
            and isinstance(d["fatores"], list)
            and len(d["fatores"]) <= 3
            and all(isinstance(f, str) and f for f in d["fatores"]))


rodar("P1: Aprovado pelo Modelo, acima de 90%",
      lambda: decisao_ok(P1, "Aprovado", "Modelo") and recomendador.decidir(P1)["probabilidade"] > 0.90)
rodar("P2: Recusado pelo Modelo, entre 30% e 50%",
      lambda: decisao_ok(P2, "Recusado", "Modelo") and 0.30 < recomendador.decidir(P2)["probabilidade"] < 0.50)
rodar("P3 (restrição): Recusado pela Política, 0%",
      lambda: decisao_ok(P3, "Recusado", "Política") and recomendador.decidir(P3)["probabilidade"] == 0.0)
rodar("P4 (renda baixa): Recusado pela Política, 0%",
      lambda: decisao_ok(P4, "Recusado", "Política") and recomendador.decidir(P4)["probabilidade"] == 0.0)
rodar("P5 (comprometimento alto): Recusado pela Política, 0%",
      lambda: decisao_ok(P5, "Recusado", "Política") and recomendador.decidir(P5)["probabilidade"] == 0.0)
rodar("P6 (Veículo): Aprovado pelo Modelo, acima de 90%",
      lambda: decisao_ok(P6, "Aprovado", "Modelo") and recomendador.decidir(P6)["probabilidade"] > 0.90)
rodar("P7 (Serviço): Aprovado pelo Modelo, acima de 90%",
      lambda: decisao_ok(P7, "Aprovado", "Modelo") and recomendador.decidir(P7)["probabilidade"] > 0.90)

for nome_perfil, perfil in [("P1", P1), ("P2", P2), ("P3", P3), ("P4", P4),
                            ("P5", P5), ("P6", P6), ("P7", P7)]:
    rodar(f"{nome_perfil}: formato da decisão (chaves, origem, 0 a 1, até 3 fatores)",
          lambda p=perfil: formato_ok(p))

rodar("fatores INDIVIDUAIS: mudam quando a entrada de P1 vai a zero",
      lambda: recomendador.decidir(P1)["fatores"]
      != recomendador.decidir(com(P1, entrada=0.0))["fatores"])

# ---------------------------------------------------------------------------
print("\n=== 5. Ranking e sugestões (contrato, seção 10) ===")
COLUNAS = ["id", "categoria", "credito", "prazo", "parcela", "nome", "score", "justificativa"]


def ranking_ok():
    r = recomendador.ranquear(P1)
    notas = list(r["score"])
    return (list(r.columns) == COLUNAS
            and len(r) > 0
            and set(r["categoria"]) == {"Imóvel"}
            and notas == sorted(notas, reverse=True)
            and all(0 <= n <= 100 for n in notas))


rodar("ranquear(P1): colunas, só Imóvel, ordem decrescente, nota de 0 a 100", ranking_ok)
rodar("ranquear(P6): só Veículo",
      lambda: set(recomendador.ranquear(P6)["categoria"]) == {"Veículo"})
rodar("ranquear(P7): só Serviço",
      lambda: set(recomendador.ranquear(P7)["categoria"]) == {"Serviço"})
rodar("sugerir_ajustes(P1) é lista vazia (perfil aprovado)",
      lambda: recomendador.sugerir_ajustes(P1) == [])
rodar("sugerir_ajustes(P2) devolve textos",
      lambda: len(recomendador.sugerir_ajustes(P2)) > 0
      and all(isinstance(s, str) for s in recomendador.sugerir_ajustes(P2)))
rodar("sugerir_ajustes(P3): a primeira sugestão fala da restrição",
      lambda: "restri" in recomendador.sugerir_ajustes(P3)[0].lower())

# ---------------------------------------------------------------------------
print("\n=== 6. Modelo de IA (contrato, seção 9) ===")
modelo = importlib.import_module("modelo")


def cache_ok():
    modelo.carregar_modelo()  # a primeira chamada pode treinar
    inicio = time.time()
    modelo.carregar_modelo()
    modelo.carregar_modelo()
    return (time.time() - inicio) < 0.2


rodar("arquivo modelo_v3_2.joblib existe na raiz do projeto",
      lambda: (PASTA / "modelo_v3_2.joblib").exists())
rodar("carregar_modelo() usa cache (chamadas seguintes são rápidas)", cache_ok)
rodar("avaliar_com_modelo(P1) devolve o formato da decisão",
      lambda: set(modelo.avaliar_com_modelo(P1).keys()) == CHAVES)
rodar("metricas() roda e devolve um dicionário",
      lambda: isinstance(modelo.metricas(), dict) and len(modelo.metricas()) > 0)

# ---------------------------------------------------------------------------
print("\n=== RESUMO ===")
print(f"{sum(resultados)} de {len(resultados)} verificações OK")
if divergencias:
    print("\nAs que DIVERGEM (copie e mande para a Pessoa A):")
    for linha in divergencias:
        print(" ", linha)