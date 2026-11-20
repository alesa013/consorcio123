"""
modelo.py -  Alessandra

Parte 1: montar as entradas, treinar, salvar e carregar o modelo.
Mais tarde entram: metricas(), avaliar_com_modelo() e a comparacao
com a regressao logistica.
"""
import sys
from datetime import date
from pathlib import Path

import joblib
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
CAMINHO_MODELO = PASTA_RAIZ / "modelo.joblib"

# --- Constantes do contrato (secao 9) ---
MAX_DEPTH = 5
MIN_SAMPLES_LEAF = 50
FRACAO_TESTE = 0.20
RANDOM_STATE = 42

# Campos do perfil que entram no modelo (todos, exceto "objetivo")
CAMPOS_DO_MODELO = ["renda", "vinculo", "tempo_vinculo", "dividas_mensais", "restricao", "entrada", "credito", "prazo"]
LIMIAR_APROVACAO = 0.5  # contrato, secao 8: Aprovado se probabilidade >= 0,5


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


def criar_pipeline():
    """Cria a linha de montagem (ainda sem treinar):
    estacao 1 = OneHotEncoder no vinculo (os outros campos passam direto)
    estacao 2 = arvore de decisao."""
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


def treinar_modelo():
    """Treina o modelo, salva em modelo.joblib e devolve as metricas
    (o mesmo dicionario de metricas())."""
    entradas_treino, _, alvo_treino, _ = dividir_dados()

    pipeline = criar_pipeline()
    pipeline.fit(entradas_treino, alvo_treino)  # aqui a arvore "estuda"

    joblib.dump(pipeline, CAMINHO_MODELO)  # congela o modelo pronto
    return metricas()


def carregar_modelo():
    """Carrega o modelo salvo; se o arquivo nao existir, treina antes."""
    if not CAMINHO_MODELO.exists():
        treinar_modelo()
    return joblib.load(CAMINHO_MODELO)

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


def metricas():
    """Mede o modelo na 'prova' (os 2.000 perfis de teste) em dois recortes:
    1) todos os perfis do teste; 2) so os que a politica NAO recusa."""
    modelo = carregar_modelo()
    _, entradas_teste, _, alvo_teste = dividir_dados()
    previsto = modelo.predict(entradas_teste)

    # Recorte 2: reaproveita a regra da politica que ja existe no dados_sinteticos.py
    # (a tabela de entradas tem as mesmas colunas que ela usa)
    entradas_com_perfil = entradas_teste.copy()
    entradas_com_perfil["restricao"] = entradas_com_perfil["restricao"].astype(bool)
    faixa_intermediaria = ~recusado_pela_politica(entradas_com_perfil)

    return {
        "todos": _calcular_metricas(alvo_teste, previsto),
        "faixa_intermediaria": _calcular_metricas(
            alvo_teste[faixa_intermediaria], previsto[faixa_intermediaria.to_numpy()]
        ),
    }


def _fatores_do_modelo(modelo, quantos=3):
    """Textos com as entradas que mais pesam no modelo (visao geral)."""
    nomes = modelo.named_steps["preparo"].get_feature_names_out()
    pesos = modelo.named_steps["arvore"].feature_importances_
    ranking = sorted(zip(nomes, pesos), key=lambda par: par[1], reverse=True)
    textos = []
    for nome, peso in ranking[:quantos]:
        if peso > 0:
            nome_limpo = nome.split("__", 1)[-1]  # tira o prefixo "vinculo__"/"remainder__"
            textos.append(f"{nome_limpo} (peso {peso:.0%} no modelo)")
    return textos


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
        "fatores": _fatores_do_modelo(modelo),
    }
# Colunas numericas das entradas (tudo, menos "vinculo", que e texto)
COLUNAS_NUMERICAS = ["renda", "tempo_vinculo", "dividas_mensais", "restricao",
                     "entrada", "credito", "prazo", "parcela_estimada",
                     "comprometimento", "entrada_pct", "credito_renda"]


def criar_pipeline_logistica():
    """Linha de montagem da regressao logistica (so para a comparacao):
    estacao 1 = OneHotEncoder no vinculo + StandardScaler nos numeros
    estacao 2 = regressao logistica."""
    preparo = ColumnTransformer([
        ("vinculo", OneHotEncoder(handle_unknown="ignore"), ["vinculo"]),
        ("numeros", StandardScaler(), COLUNAS_NUMERICAS),
    ])
    regressao = LogisticRegression(max_iter=1000, random_state=RANDOM_STATE)
    return Pipeline([("preparo", preparo), ("regressao", regressao)])


def _avaliar_pipeline(pipeline, entradas_teste, alvo_teste):
    """Mede um pipeline ja treinado nos dois recortes (mesma regra da metricas())."""
    previsto = pipeline.predict(entradas_teste)

    com_booleano = entradas_teste.copy()
    com_booleano["restricao"] = com_booleano["restricao"].astype(bool)
    faixa = ~recusado_pela_politica(com_booleano)

    return {
        "todos": _calcular_metricas(alvo_teste, previsto),
        "faixa_intermediaria": _calcular_metricas(
            alvo_teste[faixa], previsto[faixa.to_numpy()]
        ),
    }


def comparar_com_regressao_logistica():
    """Treina arvore e regressao logistica (so na memoria, sem mexer no
    modelo.joblib) com a MESMA divisao e devolve as metricas dos dois."""
    entradas_treino, entradas_teste, alvo_treino, alvo_teste = dividir_dados()

    arvore = criar_pipeline()
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