# paginas/acompanhamento.py - página "Acompanhamento" (Pessoa A)
# Números gerais do sistema, sem dados individuais (contrato, resumo_dashboard).

import pandas as pd
import streamlit as st

import banco
from formatacao import percentual

OBJETIVOS = ["Imóvel", "Veículo", "Serviço"]

# Dados de exemplo, usados só enquanto a função da Pessoa B não existir
RESUMO_EXEMPLO = {
    "total_perfis": 120,
    "total_usuarios": 35,
    "taxa_aprovacao": 0.46,
    "probabilidade_media": 0.52,
    "por_objetivo": {
        "Imóvel": {"total": 60, "aprovados": 24},
        "Veículo": {"total": 40, "aprovados": 21},
        "Serviço": {"total": 20, "aprovados": 10},
    },
}


def obter_resumo():
    """Usa o resumo_dashboard() da Pessoa B se já existir.
    Devolve (resumo, eh_exemplo)."""
    if hasattr(banco, "resumo_dashboard"):
        return banco.resumo_dashboard(), False
    return RESUMO_EXEMPLO, True


st.header("Acompanhamento")
st.caption(
    "Visão geral de todas as avaliações feitas no sistema. "
    "São dados agregados, sem informações individuais."
)

resumo, eh_exemplo = obter_resumo()

if eh_exemplo:
    st.warning(
        "Dados de EXEMPLO: a função resumo_dashboard() da Pessoa B ainda não existe."
    )

if resumo.get("total_perfis", 0) == 0:
    st.info("Ainda não há avaliações registradas. Avalie um perfil na página **Meu perfil**.")
    st.stop()

# ----- Números gerais -----
c1, c2, c3, c4 = st.columns(4)
c1.metric("Perfis avaliados", resumo["total_perfis"])
c2.metric("Usuários", resumo["total_usuarios"])
c3.metric("Taxa de aprovação", percentual(resumo["taxa_aprovacao"]))
c4.metric("Probabilidade média", percentual(resumo["probabilidade_media"]))

# ----- Por objetivo -----
st.subheader("Aprovados e recusados por objetivo")

linhas = []
for objetivo in OBJETIVOS:
    dados = resumo.get("por_objetivo", {}).get(objetivo, {"total": 0, "aprovados": 0})
    linhas.append(
        {
            "Objetivo": objetivo,
            "Aprovados": dados["aprovados"],
            "Recusados": dados["total"] - dados["aprovados"],
        }
    )
tabela = pd.DataFrame(linhas).set_index("Objetivo")

st.bar_chart(tabela, color=["#2e9e5b", "#d9534f"])

detalhe = tabela.copy()
detalhe["Total"] = detalhe["Aprovados"] + detalhe["Recusados"]
detalhe["Taxa de aprovação"] = [
    percentual(a / t) if t else "—"
    for a, t in zip(detalhe["Aprovados"], detalhe["Total"])
]
st.dataframe(detalhe)

st.button("Atualizar números")  # qualquer clique reexecuta a página