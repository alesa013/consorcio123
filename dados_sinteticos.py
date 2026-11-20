"""
dados_sinteticos.py - Pessoa B (contrato v3.1, secao 9)

Gera perfis FICTICIOS e os rotula (Aprovado/Recusado) para treinar o modelo.
Nao e analise de credito real.
"""
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from recomendador import (
    CAMPOS_PERFIL,
    COMPROMETIMENTO_IDEAL,
    ENTRADA_REF,
    LIMITE_COMPROMETIMENTO,
    LIMITE_CREDITO_RENDA,
    NOTA_MINIMA,
    RENDA_MINIMA,
    calcular_indicadores,
)

# --- Constantes do contrato (secao 9) ---
N_PERFIS = 10000
RUIDO_ROTULOS = 0.05
SEMENTE = 42

# --- Distribuicoes de referencia (secao 9) ---
RENDA_MEDIANA = 3800
RENDA_SIGMA = 0.6
RENDA_MIN, RENDA_MAX = 900, 40000

PROB_VINCULO = {
    "CLT": 0.45,
    "Servidor público": 0.12,
    "Autônomo/MEI": 0.20,
    "Empresário": 0.08,
    "Aposentado/Pensionista": 0.15,
}
MEDIA_TEMPO_MESES = {
    "CLT": 36,
    "Servidor público": 90,
    "Autônomo/MEI": 30,
    "Empresário": 60,
    "Aposentado/Pensionista": 120,
}
BASE_VINCULO = {  # usado so na pontuacao
    "Servidor público": 1.0,
    "Aposentado/Pensionista": 1.0,
    "CLT": 0.8,
    "Empresário": 0.6,
    "Autônomo/MEI": 0.5,
}
PROB_OBJETIVO = {"Imóvel": 0.40, "Veículo": 0.40, "Serviço": 0.20}
FAIXA_CREDITO = {  # (minimo, maximo) por objetivo
    "Imóvel": (60000, 600000),
    "Veículo": (20000, 180000),
    "Serviço": (5000, 40000),
}
PRAZOS_POR_OBJETIVO = {
    "Imóvel": [120, 180],
    "Veículo": [60, 80, 120],
    "Serviço": [36, 60],
}
PROB_RESTRICAO = 0.10

PASTA_RAIZ = Path(__file__).resolve().parent


def gerar_perfis(n=N_PERFIS, semente=SEMENTE):
    """Devolve um DataFrame com os 9 campos do perfil + a coluna 'aprovado'
    (1 = Aprovado, 0 = Recusado). Mesma semente = mesmos perfis."""
    rng = np.random.default_rng(semente)  # o "baralho embaralhado sempre igual"

    # Renda: lognormal com mediana 3.800, limitada entre 900 e 40.000
    renda = rng.lognormal(np.log(RENDA_MEDIANA), RENDA_SIGMA, n)
    renda = np.clip(renda, RENDA_MIN, RENDA_MAX)

    vinculo = rng.choice(list(PROB_VINCULO), size=n, p=list(PROB_VINCULO.values()))

    # Tempo no vinculo: exponencial, com media diferente para cada tipo de vinculo
    medias = pd.Series(vinculo).map(MEDIA_TEMPO_MESES).to_numpy()
    tempo_vinculo = np.clip(np.round(rng.exponential(medias)), 1, 480).astype(int)

    # Dividas: uma fatia da renda (Beta 1,5 e 7 = quase sempre pequena)
    dividas = renda * rng.beta(1.5, 7, n)

    restricao = rng.random(n) < PROB_RESTRICAO

    objetivo = rng.choice(list(PROB_OBJETIVO), size=n, p=list(PROB_OBJETIVO.values()))

    # O credito acompanha a renda (aviso do contrato) e respeita a faixa do objetivo
    credito = renda * 12 * rng.uniform(0.25, 2.2, n)
    minimos = pd.Series(objetivo).map(lambda o: FAIXA_CREDITO[o][0]).to_numpy()
    maximos = pd.Series(objetivo).map(lambda o: FAIXA_CREDITO[o][1]).to_numpy()
    credito = np.clip(credito, minimos, maximos)
    credito = np.round(credito / 1000) * 1000  # arredonda ao milhar

    # Prazo: sorteado entre as opcoes de cada objetivo
    prazo = np.zeros(n, dtype=int)
    for nome_objetivo, opcoes in PRAZOS_POR_OBJETIVO.items():
        mascara = objetivo == nome_objetivo
        prazo[mascara] = rng.choice(opcoes, size=int(mascara.sum()))

    entrada = credito * rng.uniform(0, 0.40, n)

    df = pd.DataFrame({
        "renda": np.round(renda, 2),
        "vinculo": vinculo,
        "tempo_vinculo": tempo_vinculo,
        "dividas_mensais": np.round(dividas, 2),
        "restricao": restricao,
        "entrada": np.round(entrada, 2),
        "objetivo": objetivo,
        "credito": credito,
        "prazo": prazo,
    })[CAMPOS_PERFIL]

    # Rotulo base + ruido: inverte EXATAMENTE 5% dos rotulos, sorteados
    aprovado = rotulo_base(df).to_numpy().copy()
    quantos = int(round(n * RUIDO_ROTULOS))
    sorteados = rng.choice(n, size=quantos, replace=False)
    aprovado[sorteados] = ~aprovado[sorteados]
    df["aprovado"] = aprovado.astype(int)
    return df


def recusado_pela_politica(df):
    """Camada 1 da decisao (secao 8), para a tabela inteira de uma vez."""
    ind = calcular_indicadores(df)  # a MESMA formula serve para a tabela toda
    return (
        df["restricao"]
        | (df["renda"] < RENDA_MINIMA)
        | (ind["comprometimento"] > LIMITE_COMPROMETIMENTO)
    )


def calcular_nota(df):
    """Pontuacao de 0 a 100 (secao 9). So serve para rotular os dados de treino."""
    ind = calcular_indicadores(df)

    n_comprometimento = 40 * np.clip(
        (LIMITE_COMPROMETIMENTO - ind["comprometimento"])
        / (LIMITE_COMPROMETIMENTO - COMPROMETIMENTO_IDEAL),
        0, 1,
    )
    base = df["vinculo"].map(BASE_VINCULO)
    n_estabilidade = 25 * (0.6 * base + 0.4 * np.minimum(df["tempo_vinculo"] / 24, 1))
    n_entrada = 20 * np.minimum(ind["entrada_pct"] / ENTRADA_REF, 1)
    n_credito_renda = 15 * np.clip(1 - ind["credito_renda"] / LIMITE_CREDITO_RENDA, 0, 1)

    return n_comprometimento + n_estabilidade + n_entrada + n_credito_renda


def rotulo_base(df):
    """Aprovado (True) se a politica nao recusa e a nota >= NOTA_MINIMA."""
    return (~recusado_pela_politica(df)) & (calcular_nota(df) >= NOTA_MINIMA)


def conferencias(df):
    """As 3 conferencias obrigatorias do contrato. Devolve um dicionario."""
    politica = recusado_pela_politica(df)
    nota = calcular_nota(df)
    fronteira = (~politica) & (nota >= 52) & (nota <= 68)

    pct_politica = float(politica.mean())
    pct_aprovados = float(df["aprovado"].mean())
    pct_fronteira = float(fronteira.mean())
    return {
        "recusados_pela_politica": pct_politica,
        "aprovados_no_total": pct_aprovados,
        "fronteira": pct_fronteira,
        "ok_politica": 0.30 <= pct_politica <= 0.45,
        "ok_aprovados": 0.40 <= pct_aprovados <= 0.60,
        "ok_fronteira": pct_fronteira >= 0.10,
    }


def _texto_conferencias(df, c):
    def marca(ok):
        return "OK" if ok else "FORA DA FAIXA"
    return "\n".join([
        f"Perfis gerados: {len(df)} (semente {SEMENTE})",
        f"- Recusados pela política: {c['recusados_pela_politica']:.1%} "
        f"(esperado 30% a 45%) -> {marca(c['ok_politica'])}",
        f"- Aprovados no total: {c['aprovados_no_total']:.1%} "
        f"(esperado 40% a 60%) -> {marca(c['ok_aprovados'])}",
        f"- Perfis de fronteira (nota 52 a 68, fora da política): {c['fronteira']:.1%} "
        f"(esperado pelo menos 10%) -> {marca(c['ok_fronteira'])}",
    ])


# Roda so com "python dados_sinteticos.py"
if __name__ == "__main__":
    perfis = gerar_perfis()
    resultado = conferencias(perfis)
    texto = _texto_conferencias(perfis, resultado)
    print(texto)

    # Dados de treino ficam so no seu computador (.gitignore)
    perfis.to_csv(PASTA_RAIZ / "dados_treino.csv", index=False, encoding="utf-8")

    # Registro nas docs (o contrato manda registrar a conferencia)
    pasta_docs = PASTA_RAIZ / "docs"
    pasta_docs.mkdir(exist_ok=True)
    (pasta_docs / "conferencias_dados_sinteticos.md").write_text(
        f"# Conferências dos dados sintéticos\n\nGerado em {date.today():%d/%m/%Y}.\n\n"
        + texto + "\n",
        encoding="utf-8",
    )