# formatacao.py - funções para formatar números na tela (Pessoa A)


def moeda(valor):
    """Formata como moeda brasileira: 1234.5 -> R$ 1.234,50"""
    texto = f"{float(valor):,.2f}"
    texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


def percentual(valor):
    """Fração em porcentagem: 0.324 -> 32,4%"""
    return f"{float(valor) * 100:.1f}%".replace(".", ",")


def razao(valor):
    """Razão com 'x': 2.2222 -> 2,22x"""
    return f"{float(valor):.2f}".replace(".", ",") + "x"