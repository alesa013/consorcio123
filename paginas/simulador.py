# paginas/simulador.py - página "Simulador" (Pessoa A)
# Muda crédito, prazo, entrada e dívidas e mostra o efeito na hora.
# Nada é gravado no banco; as contas e a decisão vêm das funções da Pessoa B.

import pandas as pd
import streamlit as st

import banco
import recomendador
from formatacao import moeda, percentual
import altair as alt

PRAZOS = [36, 60, 80, 120, 180]
CREDITO_MIN = 5000  # limites do contrato, seção 7
CREDITO_MAX = 600000

CHAVES_PERFIL = [
    "renda",
    "vinculo",
    "tempo_vinculo",
    "dividas_mensais",
    "restricao",
    "entrada",
    "objetivo",
    "credito",
    "prazo",
]


def carregar_perfil_base(usuario_id):
    """Perfil salvo da pessoa: primeiro da memória da sessão, depois do banco."""
    perfil = st.session_state.get("perfil")
    if perfil is not None:
        return perfil
    registro = banco.ultimo_perfil(usuario_id)
    if not registro:
        return None
    return {chave: registro[chave] for chave in CHAVES_PERFIL}


def decidir(perfil):
    """Decisão da Pessoa B, ou None se a decidir() ainda não existe."""
    if hasattr(recomendador, "decidir"):
        return recomendador.decidir(perfil)
    return None


def variacao_moeda(novo, antigo):
    """Texto da seta: +R$ 50,00 ou -R$ 50,00 (None se não mudou)."""
    dif = novo - antigo
    if abs(dif) < 0.005:
        return None
    sinal = "+" if dif > 0 else "-"
    return f"{sinal}{moeda(abs(dif))}"


def variacao_pontos(novo, antigo):
    """Diferença entre duas frações, em pontos percentuais (None se não mudou)."""
    dif = (novo - antigo) * 100
    if abs(dif) < 0.05:
        return None
    sinal = "+" if dif > 0 else "-"
    return f"{sinal}{abs(dif):.1f} p.p.".replace(".", ",")


# ----- A página começa aqui -----
st.header("Simulador")
st.caption("Mude os valores e veja o efeito na parcela e na decisão. Nada aqui é salvo.")

if "usuario_id" not in st.session_state:
    st.error("Usuário não identificado. Abra o aplicativo pelo app.py.")
    st.stop()

base = carregar_perfil_base(st.session_state["usuario_id"])
if base is None:
    st.info(
        "Você ainda não avaliou nenhum perfil. Abra a página **Meu perfil**, "
        "preencha os campos e clique em **Avaliar perfil**."
    )
    st.stop()

tem_decisao = hasattr(recomendador, "decidir")
if not tem_decisao:
    st.warning(
        "A função decidir() da Pessoa B ainda não existe: por enquanto o "
        "simulador mostra só os indicadores."
    )

# ----- Controles -----
st.subheader("Mude os valores")
st.caption("Os controles começam nos valores do seu perfil salvo (arredondados).")

col1, col2 = st.columns(2)

with col1:
    credito_ini = int(min(max(round(base["credito"], -3), CREDITO_MIN), CREDITO_MAX))
    credito = st.slider(
        "Crédito desejado (R$)",
        min_value=CREDITO_MIN,
        max_value=CREDITO_MAX,
        value=credito_ini,
        step=1000,
    )
    prazo_ini = base["prazo"] if base["prazo"] in PRAZOS else PRAZOS[0]
    prazo = st.select_slider("Prazo (meses)", options=PRAZOS, value=prazo_ini)

with col2:
    if base["credito"] > 0:
        pct_ini = round(base["entrada"] / base["credito"] * 100)
    else:
        pct_ini = 0
    pct_ini = int(min(max(pct_ini, 0), 60))
    entrada_pct = st.slider("Entrada (% do crédito)", 0, 60, pct_ini, step=1)
    dividas = st.number_input(
        "Dívidas mensais (R$)",
        min_value=0.0,
        value=float(base["dividas_mensais"]),
        step=50.0,
        format="%.2f",
    )

# Cenário = cópia do perfil salvo com os valores novos (o perfil salvo não muda)
cenario = dict(base)
cenario["credito"] = float(credito)
cenario["prazo"] = int(prazo)
cenario["entrada"] = round(credito * entrada_pct / 100, 2)
cenario["dividas_mensais"] = float(dividas)

# Valida antes de qualquer conta
erros = recomendador.validar_perfil(cenario)
if erros:
    for erro in erros:
        st.error(erro)
    st.stop()

ind_base = recomendador.calcular_indicadores(base)
ind_cen = recomendador.calcular_indicadores(cenario)
dec_base = decidir(base)
dec_cen = decidir(cenario)

# ----- Resultado do cenário -----
st.subheader("Resultado do cenário")
m1, m2, m3 = st.columns(3)
m1.metric(
    "Parcela estimada",
    moeda(ind_cen["parcela_estimada"]),
    delta=variacao_moeda(ind_cen["parcela_estimada"], ind_base["parcela_estimada"]),
    delta_color="inverse",
)
m2.metric(
    "Comprometimento",
    percentual(ind_cen["comprometimento"]),
    delta=variacao_pontos(ind_cen["comprometimento"], ind_base["comprometimento"]),
    delta_color="inverse",
)
if dec_cen:
    m3.metric(
        "Probabilidade de aprovação",
        percentual(dec_cen["probabilidade"]),
        delta=variacao_pontos(dec_cen["probabilidade"], dec_base["probabilidade"]),
    )
else:
    m3.metric("Probabilidade de aprovação", "—")
st.caption("As setas comparam o cenário com o seu perfil salvo.")

if dec_cen:
    if dec_cen["status"] == "Aprovado":
        st.success("✅ Neste cenário o perfil seria aprovado")
    else:
        st.error("❌ Neste cenário o perfil seria recusado")
    st.write(f"**Motivo:** {dec_cen['motivo']}")
    if dec_cen.get("fatores"):
               if dec_cen["origem"] == "Política":
            st.write("**Motivos da recusa:**")
        else:
            st.write("**Fatores que mais pesam no modelo (valem para qualquer perfil):**")
        for fator in dec_cen["fatores"]:
            st.markdown(f"- {fator}")
    if dec_cen["status"] == "Recusado" and hasattr(recomendador, "sugerir_ajustes"):
        st.write("**O que tentar para reverter:**")
        for sugestao in recomendador.sugerir_ajustes(cenario):
            st.markdown(f"- {sugestao}")

# ----- Comparação entre os prazos -----
st.subheader("E se o prazo fosse outro?")
linhas = []
for p in PRAZOS:
    alt = dict(cenario)
    alt["prazo"] = p
    if recomendador.validar_perfil(alt):
        continue
    ind = recomendador.calcular_indicadores(alt)
    linha = {
        "Prazo (meses)": p,
        "Parcela": moeda(ind["parcela_estimada"]),
        "Comprometimento": percentual(ind["comprometimento"]),
    }
    if tem_decisao:
        d = recomendador.decidir(alt)
        linha["Probabilidade"] = percentual(d["probabilidade"])
        linha["Decisão"] = d["status"]
    linhas.append(linha)
st.dataframe(pd.DataFrame(linhas), hide_index=True)

# ----- Gráfico: probabilidade x crédito -----
if tem_decisao:
    st.subheader("Probabilidade de aprovação conforme o crédito")
    st.caption("Mantém prazo, entrada (%) e dívidas do cenário e varia só o crédito.")
    pontos = []
    for passo in range(16):
        fator = 0.5 + 0.1 * passo  # de 50% a 200% do crédito simulado
        c = int(min(max(round(credito * fator, -3), CREDITO_MIN), CREDITO_MAX))
        alt_perfil = dict(cenario)
        alt_perfil["credito"] = float(c)
        alt_perfil["entrada"] = round(c * entrada_pct / 100, 2)
        if recomendador.validar_perfil(alt_perfil):
            continue
        pontos.append(
            {
                "credito_mil": c / 1000,
                "probabilidade": recomendador.decidir(alt_perfil)["probabilidade"] * 100,
            }
        )
    if len(pontos) >= 2:
        dados = pd.DataFrame(pontos).drop_duplicates("credito_mil")
        grafico = (
            alt.Chart(dados)
            .mark_line(point=True)
            .encode(
                x=alt.X("credito_mil:Q", title="Crédito (R$ mil)"),
                y=alt.Y(
                    "probabilidade:Q",
                    title="Probabilidade de aprovação (%)",
                    scale=alt.Scale(domain=[0, 100]),
                ),
            )
            .properties(height=300)
        )
        st.altair_chart(grafico)
    else:
        st.info("Não há pontos suficientes para desenhar o gráfico.")