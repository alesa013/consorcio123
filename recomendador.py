"""
recomendador.py - Pessoa B (contrato v3.1, secoes 4 a 8, 10 e 11)

Parte 1: constantes, indicadores e validacao do perfil.
Mais tarde entram: decidir(), ranquear() e sugerir_ajustes().
"""

import pandas as pd

# --- Constantes do contrato (secao 6) ---
RENDA_MINIMA = 1500
LIMITE_COMPROMETIMENTO = 0.40
COMPROMETIMENTO_IDEAL = 0.20
NOTA_MINIMA = 60
ENTRADA_REF = 0.20
LIMITE_CREDITO_RENDA = 6
TAXA_ADMIN = 0.15  # ficticia

# --- Constantes do ranking (secao 10) ---
# O contrato diz que a nota da parcela "diminui proporcionalmente ate 0", mas nao
# diz onde chega a 0. Interpretacao adotada: chega a 0 quando o comprometimento
# alcanca o DOBRO do limite (80%). Para mudar a regra, mude so esta linha.
COMPROMETIMENTO_NOTA_ZERO = 2 * LIMITE_COMPROMETIMENTO
COLUNAS_RANKING = ["id", "categoria", "credito", "prazo", "parcela", "nome",
                   "score", "justificativa"]

# --- Listas aceitas (secao 4) ---
VINCULOS = ["CLT", "Servidor público", "Autônomo/MEI", "Empresário",
            "Aposentado/Pensionista"]
OBJETIVOS = ["Imóvel", "Veículo", "Serviço"]
PRAZOS_ACEITOS = [36, 60, 80, 120, 180]

# Os 9 campos do perfil, sem acento nas chaves (secao 4)
CAMPOS_PERFIL = ["renda", "vinculo", "tempo_vinculo", "dividas_mensais",
                 "restricao", "entrada", "objetivo", "credito", "prazo"]


def calcular_indicadores(perfil):
    """Calcula os 4 indicadores da secao 5.
    Importante: so chame depois de validar_perfil() devolver lista vazia
    (renda e credito precisam ser maiores que zero)."""
    renda = perfil["renda"]
    credito = perfil["credito"]
    entrada = perfil["entrada"]

    parcela_estimada = (credito - entrada) * (1 + TAXA_ADMIN) / perfil["prazo"]
    return {
        "parcela_estimada": parcela_estimada,
        "comprometimento": (perfil["dividas_mensais"] + parcela_estimada) / renda,
        "entrada_pct": entrada / credito,
        "credito_renda": credito / (renda * 12),
    }


# ---------------------------------------------------------------------------
# Validacao (secao 7)
# ---------------------------------------------------------------------------
def _reais(valor):
    """1234.5 -> 'R$ 1.234,50' (formato brasileiro)."""
    texto = f"{valor:,.2f}"  # 1,234.50
    texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


def _eh_numero(valor):
    """True para int/float. Em Python True/False contam como numero, entao
    excluimos bool de proposito."""
    return isinstance(valor, (int, float)) and not isinstance(valor, bool)


def _validar_numero(erros, valor, rotulo, minimo, maximo, formato, inteiro=False):
    """Confere se 'valor' e numero dentro da faixa. Se nao for, acrescenta uma
    mensagem em 'erros'. Devolve True quando esta tudo certo."""
    if not _eh_numero(valor) or (inteiro and not isinstance(valor, int)):
        erros.append(f"{rotulo}: informe um número{' inteiro' if inteiro else ''}.")
        return False
    # "not (a <= v <= b)" tambem pega NaN, que falha em qualquer comparacao
    if not (minimo <= valor <= maximo):
        erros.append(f"{rotulo} deve estar entre {formato(minimo)} e {formato(maximo)}.")
        return False
    return True


def validar_perfil(perfil):
    """Devolve uma lista de textos de erro. Lista vazia = perfil ok."""
    if not isinstance(perfil, dict):
        return ["O perfil precisa ser um dicionário."]
    ausentes = [campo for campo in CAMPOS_PERFIL if campo not in perfil]
    if ausentes:
        return ["Campos ausentes no perfil: " + ", ".join(ausentes) + "."]

    erros = []
    _validar_numero(erros, perfil["renda"], "Renda mensal", 0.01, 200000, _reais)
    _validar_numero(erros, perfil["dividas_mensais"], "Dívidas mensais", 0, 100000, _reais)
    _validar_numero(erros, perfil["tempo_vinculo"], "Tempo no vínculo atual (meses)",
                    0, 600, str, inteiro=True)
    credito_ok = _validar_numero(erros, perfil["credito"], "Crédito desejado",
                                 5000, 600000, _reais)

    # Entrada: >= 0 e menor que o credito
    entrada = perfil["entrada"]
    if not _eh_numero(entrada):
        erros.append("Entrada: informe um número.")
    elif not (entrada >= 0):
        erros.append("A entrada não pode ser negativa.")
    elif credito_ok and not (entrada < perfil["credito"]):
        erros.append("A entrada precisa ser menor que o crédito desejado.")

    if perfil["vinculo"] not in VINCULOS:
        erros.append("O vínculo precisa ser um destes: " + ", ".join(VINCULOS) + ".")
    if perfil["objetivo"] not in OBJETIVOS:
        erros.append("O objetivo precisa ser um destes: " + ", ".join(OBJETIVOS) + ".")
    if isinstance(perfil["prazo"], bool) or perfil["prazo"] not in PRAZOS_ACEITOS:
        erros.append("O prazo precisa ser um destes (em meses): "
                     + ", ".join(str(p) for p in PRAZOS_ACEITOS) + ".")
    if not isinstance(perfil["restricao"], bool):
        erros.append("Restrição no nome: responda Sim ou Não.")

    return erros


# ---------------------------------------------------------------------------
# decidir() - decisão em duas camadas (contrato, seção 8)
# Escrita pela Pessoa A, com a Pessoa B.
# ---------------------------------------------------------------------------


def _maiuscula(texto):
    """Deixa a primeira letra maiúscula: 'há restrição' -> 'Há restrição'."""
    return texto[0].upper() + texto[1:]


def decidir(perfil):
    """Devolve {"status", "probabilidade", "origem", "motivo", "fatores"}.

    Camada 1 (política): recusa direto, sem consultar o modelo.
    Camada 2 (modelo): nos demais casos, decide o avaliar_com_modelo().
    Espera um perfil que já passou por validar_perfil().
    """
    ind = calcular_indicadores(perfil)

    # --- Camada 1: política ---
    motivos = []
    if perfil["restricao"]:
        motivos.append("há restrição no nome")
    if perfil["renda"] < RENDA_MINIMA:
        minimo = f"{RENDA_MINIMA:,.0f}".replace(",", ".")
        motivos.append(f"a renda está abaixo do mínimo de R$ {minimo}")
    if ind["comprometimento"] > LIMITE_COMPROMETIMENTO:
        atual = f"{ind['comprometimento'] * 100:.1f}".replace(".", ",")
        limite = f"{LIMITE_COMPROMETIMENTO * 100:.0f}"
        motivos.append(
            f"o comprometimento da renda ({atual}%) passa do limite de {limite}%"
        )

    if motivos:
        return {
            "status": "Recusado",
            "probabilidade": 0.0,
            "origem": "Política",
            "motivo": "Recusado pela política: " + "; ".join(motivos) + ".",
            "fatores": [_maiuscula(m) for m in motivos[:3]],
        }

    # --- Camada 2: modelo de IA ---
    # O import fica aqui dentro (e não no topo) para evitar um "import circular":
    # o modelo.py também importa o recomendador.py.
    import modelo

    return modelo.avaliar_com_modelo(perfil)

# ---------------------------------------------------------------------------
# Ranking do catalogo (secao 10)
# ---------------------------------------------------------------------------
def _percentual(valor):
    """0.324 -> '32,4%' (formato brasileiro)."""
    return f"{valor * 100:.1f}%".replace(".", ",")


def _nota_credito(credito_catalogo, credito):
    """0 a 50: quanto mais perto do credito desejado, melhor."""
    return 50 * max(0, 1 - abs(credito_catalogo - credito) / credito)


def _nota_prazo(prazo_catalogo, prazo):
    """0 a 25: 25 se o prazo e igual; senao perde pontos com a diferenca."""
    if prazo_catalogo == prazo:
        return 25
    return 25 * max(0, 1 - abs(prazo_catalogo - prazo) / prazo)


def _nota_parcela(comprometimento):
    """0 a 25: 25 se a parcela cabe no limite; acima dele, a nota cai em linha
    reta e chega a 0 em COMPROMETIMENTO_NOTA_ZERO."""
    if comprometimento <= LIMITE_COMPROMETIMENTO:
        return 25
    excesso = ((comprometimento - LIMITE_COMPROMETIMENTO)
               / (COMPROMETIMENTO_NOTA_ZERO - LIMITE_COMPROMETIMENTO))
    return 25 * max(0, 1 - excesso)


def _justificativa(consorcio, perfil, comprometimento):
    """Texto simples explicando por que este consorcio recebeu esta nota."""
    pedido = perfil["credito"]
    if consorcio["credito"] == pedido:
        credito = "crédito igual ao desejado"
    else:
        diferenca = abs(consorcio["credito"] - pedido) / pedido
        sentido = "acima" if consorcio["credito"] > pedido else "abaixo"
        credito = (f"crédito de {_reais(consorcio['credito'])}, "
                   f"{_percentual(diferenca)} {sentido} do desejado")

    prazo = int(consorcio["prazo"])
    if prazo == perfil["prazo"]:
        texto_prazo = f"prazo de {prazo} meses, igual ao desejado"
    else:
        texto_prazo = f"prazo de {prazo} meses (você pediu {perfil['prazo']})"

    limite = f"{LIMITE_COMPROMETIMENTO * 100:.0f}%"
    situacao = "dentro" if comprometimento <= LIMITE_COMPROMETIMENTO else "acima"
    parcela = (f"parcela de {_reais(consorcio['parcela'])} leva o comprometimento "
               f"da renda a {_percentual(comprometimento)} ({situacao} do limite de {limite})")

    return f"Este consórcio tem {credito}; {texto_prazo}; {parcela}."


def ranquear(perfil, catalogo=None):
    """Ranking do catalogo para o perfil (secao 10). So consorcios da categoria
    igual ao objetivo, com score de 0 a 100, do melhor para o pior.
    Devolve um DataFrame com as colunas de COLUNAS_RANKING (vazio se nenhum
    consorcio combinar). 'catalogo' e opcional: sem ele, le do banco.
    So chame depois de validar_perfil() devolver lista vazia."""
    if catalogo is None:
        import banco  # dentro da funcao: este arquivo nao depende do banco para o resto
        catalogo = banco.listar_consorcios()

    candidatos = catalogo[catalogo["categoria"] == perfil["objetivo"]]
    if candidatos.empty:
        return pd.DataFrame(columns=COLUNAS_RANKING)

    linhas = []
    for _, c in candidatos.iterrows():
        comprometimento = (perfil["dividas_mensais"] + c["parcela"]) / perfil["renda"]
        score = (_nota_credito(c["credito"], perfil["credito"])
                 + _nota_prazo(c["prazo"], perfil["prazo"])
                 + _nota_parcela(comprometimento))
        linhas.append({
            "id": int(c["id"]), "categoria": c["categoria"],
            "credito": float(c["credito"]), "prazo": int(c["prazo"]),
            "parcela": float(c["parcela"]), "nome": c["nome"],
            "score": round(float(score), 1),
            "justificativa": _justificativa(c, perfil, comprometimento),
        })

    ranking = pd.DataFrame(linhas, columns=COLUNAS_RANKING)
    # kind="stable": em caso de empate, mantem a ordem do catalogo
    return ranking.sort_values("score", ascending=False, kind="stable").reset_index(drop=True)