"""
modelo.py - Alessandra (contrato v3.2, secao 9)

Modelo de IA oficial: REGRESSAO LOGISTICA. A arvore de decisao da v3.1 ficou
so para a comparacao (python modelo.py comparar).

Funcoes do contrato: treinar_modelo(), carregar_modelo(),
avaliar_com_modelo(perfil) e metricas().
"""
import sys
from datetime import date
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, confusion_matrix,
                             precision_score, recall_score)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier

from dados_sinteticos import gerar_perfis, recusado_pela_politica
from recomendador import calcular_indicadores

# --- Caminhos (relativos a ESTE arquivo, como no banco.py) ---
PASTA_RAIZ = Path(__file__).resolve().parent
# NOVO v3.2: o nome do arquivo leva a versao do contrato. O modelo.joblib antigo
# (arvore) nao serve mais; com outro nome, ele nunca e carregado por engano.
CAMINHO_MODELO = PASTA_RAIZ / "modelo_v3_2.joblib"

# --- Constantes do contrato (secao 9) ---
FRACAO_TESTE = 0.20
RANDOM_STATE = 42
LIMIAR_APROVACAO = 0.5  # secao 8: Aprovado se probabilidade >= 0,5

# Constantes da arvore da v3.1 (usadas so na comparacao)
MAX_DEPTH = 5
MIN_SAMPLES_LEAF = 50

# Campos do perfil que entram no modelo (todos, exceto "objetivo")
CAMPOS_DO_MODELO = ["renda", "vinculo", "tempo_vinculo", "dividas_mensais",
                    "restricao", "entrada", "credito", "prazo"]

# Colunas numericas das entradas (tudo, menos "vinculo", que e texto)
COLUNAS_NUMERICAS = ["renda", "tempo_vinculo", "dividas_mensais", "restricao",
                     "entrada", "credito", "prazo", "parcela_estimada",
                     "comprometimento", "entrada_pct", "credito_renda"]

# NOVO v3.2: o modelo fica guardado aqui depois da primeira leitura, para nao
# abrir o arquivo toda vez que decidir() for chamada (o Simulador chama ~20x).
_modelo_em_memoria = None

# NOVO (Tarefa 5): os fatores individuais comparam o perfil com um perfil
# "tipico" entre os que o modelo avalia. Esse perfil tipico fica guardado aqui.
_referencia_em_memoria = None

# NOVO (Tarefa 5): os 4 temas dos fatores (os mesmos 4 pedacos da nota do contrato).
# Colunas parecidas andam juntas, para o texto nao se repetir nem se contradizer.
# ("restricao" nao entra: quem tem restricao nem chega ao modelo.)
TEMAS_FATORES = {
    "comprometimento": ["comprometimento", "dividas_mensais", "parcela_estimada", "prazo"],
    "estabilidade": ["vinculo", "tempo_vinculo"],
    "entrada": ["entrada", "entrada_pct"],
    "credito_renda": ["credito_renda", "credito", "renda"],
}
LIMITE_FATOR = 0.05  # efeitos menores que isso sao ruido e nao viram fator


# ---------------------------------------------------------------------------
# Entradas e divisao dos dados
# ---------------------------------------------------------------------------
def montar_entradas(dados):
    """Monta a tabela que o modelo recebe: os campos do perfil (sem objetivo)
    + os 4 indicadores. Aceita um DataFrame (muitos perfis) ou um
    dicionario (um perfil so)."""
    if isinstance(dados, dict):
        dados = pd.DataFrame([dados])  # transforma 1 perfil em tabela de 1 linha

    entradas = dados[CAMPOS_DO_MODELO].copy()
    entradas["restricao"] = entradas["restricao"].astype(int)  # True/False -> 1/0

    # Os 4 indicadores, calculados pela MESMA funcao do recomendador.py
    for nome, valor in calcular_indicadores(dados).items():
        entradas[nome] = valor
    return entradas


def dividir_dados():
    """Gera os 10.000 perfis e separa 80% para treino e 20% para teste.
    Devolve: entradas_treino, entradas_teste, alvo_treino, alvo_teste."""
    perfis = gerar_perfis()  # mesma semente = mesmos perfis em qualquer maquina
    entradas = montar_entradas(perfis)
    alvo = perfis["aprovado"]
    return train_test_split(
        entradas, alvo,
        test_size=FRACAO_TESTE,
        stratify=alvo,
        random_state=RANDOM_STATE,
    )


# ---------------------------------------------------------------------------
# Os dois modelos
# ---------------------------------------------------------------------------
def criar_pipeline_logistica():
    """Modelo OFICIAL (v3.2). Linha de montagem ainda sem treinar:
    estacao 1 = OneHotEncoder no vinculo + StandardScaler nos numeros
    estacao 2 = regressao logistica."""
    preparo = ColumnTransformer([
        ("vinculo", OneHotEncoder(handle_unknown="ignore"), ["vinculo"]),
        ("numeros", StandardScaler(), COLUNAS_NUMERICAS),
    ])
    regressao = LogisticRegression(max_iter=1000, random_state=RANDOM_STATE)
    return Pipeline([("preparo", preparo), ("regressao", regressao)])


def criar_pipeline_arvore():
    """Arvore da v3.1. Fica so para a comparacao (python modelo.py comparar)."""
    preparo = ColumnTransformer(
        [("vinculo", OneHotEncoder(handle_unknown="ignore"), ["vinculo"])],
        remainder="passthrough",
    )
    arvore = DecisionTreeClassifier(
        max_depth=MAX_DEPTH,
        min_samples_leaf=MIN_SAMPLES_LEAF,
        random_state=RANDOM_STATE,
    )
    return Pipeline([("preparo", preparo), ("arvore", arvore)])


# ---------------------------------------------------------------------------
# Treinar e carregar (funcoes do contrato)
# ---------------------------------------------------------------------------
def treinar_modelo():
    """Treina a regressao logistica, salva em modelo_v3_2.joblib, deixa o
    modelo na memoria e devolve as metricas (o mesmo dicionario de metricas())."""
    global _modelo_em_memoria, _referencia_em_memoria

    entradas_treino, _, alvo_treino, _ = dividir_dados()

    pipeline = criar_pipeline_logistica()
    pipeline.fit(entradas_treino, alvo_treino)  # aqui o modelo "estuda"

    joblib.dump(pipeline, CAMINHO_MODELO)  # congela o modelo pronto no arquivo
    _modelo_em_memoria = pipeline          # e ja deixa pronto na memoria
    _referencia_em_memoria = None          # o perfil tipico sera recalculado
    return metricas()


def carregar_modelo():
    """Devolve o modelo. Ordem: 1) ja esta na memoria? usa; 2) existe o
    arquivo? le e guarda na memoria; 3) senao, treina antes (contrato)."""
    global _modelo_em_memoria

    if _modelo_em_memoria is None:
        if CAMINHO_MODELO.exists():
            _modelo_em_memoria = joblib.load(CAMINHO_MODELO)
        else:
            treinar_modelo()  # ela mesma deixa o modelo na memoria
    return _modelo_em_memoria


# ---------------------------------------------------------------------------
# Metricas
# ---------------------------------------------------------------------------
def _calcular_metricas(alvo_real, alvo_previsto):
    """Calcula as 4 medidas para um conjunto de perfis."""
    # labels=[0, 1] fixa a ordem: linha/coluna 0 = Recusado, 1 = Aprovado
    matriz = confusion_matrix(alvo_real, alvo_previsto, labels=[0, 1])
    return {
        "n": int(len(alvo_real)),
        "acuracia": float(accuracy_score(alvo_real, alvo_previsto)),
        "precisao": float(precision_score(alvo_real, alvo_previsto, zero_division=0)),
        "revocacao": float(recall_score(alvo_real, alvo_previsto, zero_division=0)),
        # [[recusou certo, aprovou errado], [recusou errado, aprovou certo]]
        "matriz_confusao": matriz.tolist(),
    }


def _avaliar_pipeline(pipeline, entradas_teste, alvo_teste):
    """Mede um pipeline ja treinado nos dois recortes:
    1) todos os perfis do teste; 2) so os que a politica NAO recusa."""
    previsto = pipeline.predict(entradas_teste)

    # Recorte 2: reaproveita a regra da politica do dados_sinteticos.py
    com_booleano = entradas_teste.copy()
    com_booleano["restricao"] = com_booleano["restricao"].astype(bool)
    faixa = ~recusado_pela_politica(com_booleano)

    return {
        "todos": _calcular_metricas(alvo_teste, previsto),
        "faixa_intermediaria": _calcular_metricas(
            alvo_teste[faixa], previsto[faixa.to_numpy()]
        ),
    }


def metricas():
    """Mede o modelo oficial na 'prova' (os 2.000 perfis de teste)."""
    _, entradas_teste, _, alvo_teste = dividir_dados()
    return _avaliar_pipeline(carregar_modelo(), entradas_teste, alvo_teste)


# ---------------------------------------------------------------------------
# Decisao do modelo (formato da secao 8)
# ---------------------------------------------------------------------------
def _pct(valor):
    """0.324 -> '32,4%' """
    return f"{valor * 100:.1f}%".replace(".", ",")


def _transformar(modelo, entradas):
    """Passa as entradas pela estacao 1 do pipeline e devolve uma tabela de numeros."""
    x = modelo.named_steps["preparo"].transform(entradas)
    return x.toarray() if hasattr(x, "toarray") else np.asarray(x)


def _tema_da_coluna(nome_coluna):
    """'numeros__entrada_pct' -> 'entrada'. Devolve None se a coluna nao tem tema."""
    if nome_coluna.startswith("vinculo__"):
        base = "vinculo"  # as 5 caixinhas do vinculo contam como uma coisa so
    else:
        base = nome_coluna.split("__", 1)[1]
    for tema, colunas in TEMAS_FATORES.items():
        if base in colunas:
            return tema
    return None


def _carregar_referencia(modelo):
    """Perfil 'tipico' entre os que o MODELO avalia (a politica nao recusa),
    calculado uma vez com os dados de treino e guardado na memoria."""
    global _referencia_em_memoria
    if _referencia_em_memoria is None:
        entradas_treino, _, _, _ = dividir_dados()
        com_booleano = entradas_treino.copy()
        com_booleano["restricao"] = com_booleano["restricao"].astype(bool)
        avaliados = entradas_treino[~recusado_pela_politica(com_booleano)]
        _referencia_em_memoria = _transformar(modelo, avaliados).mean(axis=0)
    return _referencia_em_memoria


def _descrever_tema(tema, linha):
    """Texto simples, com os valores do proprio perfil e sem nomes de variavel."""
    if tema == "comprometimento":
        return f"Comprometimento da renda de {_pct(linha['comprometimento'])}"
    if tema == "estabilidade":
        meses = int(linha["tempo_vinculo"])
        unidade = "mês" if meses == 1 else "meses"
        return f"Vínculo {linha['vinculo']} há {meses} {unidade}"
    if tema == "entrada":
        return f"Entrada de {_pct(linha['entrada_pct'])} do crédito"
    vezes = f"{linha['credito_renda']:.1f}".replace(".", ",")
    return f"Crédito equivalente a {vezes}x a renda anual"


def _fatores_do_modelo(modelo, entradas, quantos=3):
    """Fatores INDIVIDUAIS: o que mais empurrou a chance deste perfil para cima
    ou para baixo, em comparacao com o perfil tipico que o modelo avalia.
    (efeito de cada coluna = peso x (valor do perfil - valor tipico))"""
    x = _transformar(modelo, entradas)[0]
    referencia = _carregar_referencia(modelo)
    pesos = modelo.named_steps["regressao"].coef_[0]
    nomes = modelo.named_steps["preparo"].get_feature_names_out()

    # Soma o efeito das colunas de cada tema
    efeito = {tema: 0.0 for tema in TEMAS_FATORES}
    for nome, peso, valor, tipico in zip(nomes, pesos, x, referencia):
        tema = _tema_da_coluna(nome)
        if tema is not None:
            efeito[tema] += peso * (valor - tipico)

    # Os temas de maior efeito (positivo ou negativo) viram texto
    linha = entradas.iloc[0]
    textos = []
    for tema, valor in sorted(efeito.items(), key=lambda par: abs(par[1]), reverse=True):
        if abs(valor) < LIMITE_FATOR:
            break  # os proximos sao ainda menores
        sentido = "ajuda na aprovação" if valor > 0 else "pesa contra a aprovação"
        textos.append(f"{_descrever_tema(tema, linha)}: {sentido}")
    return textos[:quantos]


def avaliar_com_modelo(perfil):
    """Decisao do modelo para UM perfil (formato da secao 8 do contrato).
    So chame depois de validar_perfil() devolver lista vazia."""
    modelo = carregar_modelo()
    entradas = montar_entradas(perfil)
    probabilidade = float(modelo.predict_proba(entradas)[0, 1])
    aprovado = probabilidade >= LIMIAR_APROVACAO
    return {
        "status": "Aprovado" if aprovado else "Recusado",
        "probabilidade": probabilidade,
        "origem": "Modelo",
        "motivo": ("O modelo estimou chance de aprovação de "
                   f"{probabilidade:.0%} para este perfil."),
        "fatores": _fatores_do_modelo(modelo, entradas),
    }


# ---------------------------------------------------------------------------
# Comparacao arvore x regressao logistica (python modelo.py comparar)
# ---------------------------------------------------------------------------
def comparar_com_regressao_logistica():
    """Treina arvore e regressao logistica (so na memoria, sem mexer no
    arquivo do modelo) com a MESMA divisao e devolve as metricas dos dois."""
    entradas_treino, entradas_teste, alvo_treino, alvo_teste = dividir_dados()

    arvore = criar_pipeline_arvore()
    arvore.fit(entradas_treino, alvo_treino)

    logistica = criar_pipeline_logistica()
    logistica.fit(entradas_treino, alvo_treino)

    return {
        "arvore": _avaliar_pipeline(arvore, entradas_teste, alvo_teste),
        "logistica": _avaliar_pipeline(logistica, entradas_teste, alvo_teste),
    }


def imprimir_comparacao():
    """Mostra a comparacao na tela e registra em docs/comparacao_modelos.md."""
    resultado = comparar_com_regressao_logistica()
    recortes = {"todos": "Todos os perfis do teste",
                "faixa_intermediaria": "Faixa intermediária (política não recusa)"}

    linhas = ["# Comparação de modelos: árvore x regressão logística", "",
              f"Gerado em {date.today():%d/%m/%Y}.", ""]
    for chave, titulo in recortes.items():
        arv = resultado["arvore"][chave]
        lg = resultado["logistica"][chave]
        # Referencia: acertos se o modelo chutasse "Aprovado" para todos
        chute = sum(arv["matriz_confusao"][1]) / arv["n"]
        linhas += [f"## {titulo} ({arv['n']} perfis)", "",
                   "| Medida | Árvore | Regressão logística |", "|---|---|---|"]
        for medida in ["acuracia", "precisao", "revocacao"]:
            linhas.append(f"| {medida} | {arv[medida]:.1%} | {lg[medida]:.1%} |")
        linhas += ["",
                   f"Matriz da árvore: {arv['matriz_confusao']}",
                   f"Matriz da logística: {lg['matriz_confusao']}",
                   f"Referência: chutar 'Aprovado' para todos acertaria {chute:.1%}.",
                   ""]

    texto = "\n".join(linhas)
    print(texto)

    pasta_docs = PASTA_RAIZ / "docs"
    pasta_docs.mkdir(exist_ok=True)
    (pasta_docs / "comparacao_modelos.md").write_text(texto + "\n", encoding="utf-8")


# Roda so com "python modelo.py"
if __name__ == "__main__":
    if "comparar" in sys.argv:  # python modelo.py comparar
        imprimir_comparacao()
        sys.exit()  # para aqui: nao treina nem imprime o resto

    resultado = treinar_modelo()
    nomes = {"todos": "Todos os perfis do teste",
             "faixa_intermediaria": "So a faixa intermediaria (politica nao recusa)"}
    for chave, titulo in nomes.items():
        m = resultado[chave]
        print(f"\n== {titulo} ({m['n']} perfis) ==")
        print(f"Acuracia:  {m['acuracia']:.1%}")
        print(f"Precisao:  {m['precisao']:.1%}")
        print(f"Revocacao: {m['revocacao']:.1%}")
        print("Matriz de confusao [[recusou certo, aprovou errado],")
        print("                    [recusou errado, aprovou certo]]:")
        print(m["matriz_confusao"])

    # Teste rapido com um perfil de exemplo
    exemplo = {"renda": 8000.0, "vinculo": "Servidor público", "tempo_vinculo": 96,
               "dividas_mensais": 500.0, "restricao": False, "entrada": 40000.0,
               "objetivo": "Imóvel", "credito": 200000.0, "prazo": 180}
    print("\nDecisao do perfil de exemplo:")
    print(avaliar_com_modelo(exemplo))
    # O mesmo perfil sem entrada: os fatores precisam MUDAR (teste de aceite)
    print("\nO mesmo perfil, sem entrada:")
    print(avaliar_com_modelo({**exemplo, "entrada": 0.0}))