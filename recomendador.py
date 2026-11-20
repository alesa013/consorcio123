"""
recomendador.py - Pessoa B (contrato v3.1, secoes 4 a 8, 10 e 11)

Parte 1: constantes, indicadores e validacao do perfil.
Mais tarde entram: decidir(), ranquear() e sugerir_ajustes().
"""

# --- Constantes do contrato (secao 6) ---
RENDA_MINIMA = 1500
LIMITE_COMPROMETIMENTO = 0.40
COMPROMETIMENTO_IDEAL = 0.20
NOTA_MINIMA = 60
ENTRADA_REF = 0.20
LIMITE_CREDITO_RENDA = 6
TAXA_ADMIN = 0.15  # ficticia

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