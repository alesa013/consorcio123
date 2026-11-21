# paginas/resultado.py - página "Resultado" (Pessoa A)
# Mostra a decisão, o motivo, os indicadores e as recomendações.

import streamlit as st

import banco
import recomendador
from formatacao import moeda, percentual, razao

# Campos do perfil (contrato, seção 4)
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


def carregar_do_banco(usuario_id):
    """Busca o último perfil salvo. Devolve (perfil, decisao, perfil_id)
    ou (None, None, None) se a pessoa ainda não tem nenhum."""
    registro = banco.ultimo_perfil(usuario_id)
    if not registro:
        return None, None, None

    perfil = {chave: registro[chave] for chave in CHAVES_PERFIL}
    decisao = {
        "status": registro["status"],
        "probabilidade": registro["probabilidade"],
        "origem": registro["origem"],
        "motivo": registro["motivo"],
        "fatores": [],
    }
    # O banco não guarda os fatores; se a decidir() existir, recalcula só eles.
    if hasattr(recomendador, "decidir"):
        decisao["fatores"] = recomendador.decidir(perfil).get("fatores", [])
    return perfil, decisao, registro["id"]


def obter_ranking(perfil):
    """Usa a ranquear() da Pessoa B se já existir; senão, mostra os consórcios
    do objetivo como exemplo. Devolve (tabela, eh_teste)."""
    if hasattr(recomendador, "ranquear"):
        return recomendador.ranquear(perfil), False

    catalogo = banco.listar_consorcios()
    exemplo = catalogo[catalogo["categoria"] == perfil["objetivo"]].copy()
    exemplo["score"] = 0.0
    exemplo["justificativa"] = (
        "Exemplo: a justificativa real virá da função ranquear() da Pessoa B."
    )
    return exemplo, True


def mostrar_consorcio(posicao, linha, eh_teste):
    """Desenha um consórcio como um cartão."""
    if "nome" in linha.index:
        nome = linha["nome"]
    else:
        nome = f"Consórcio {linha['id']}"

    with st.container(border=True):
        esquerda, direita = st.columns([3, 2])
        with esquerda:
            st.markdown(f"**{posicao}. {nome}**")
            st.caption(linha["categoria"])
            st.write(linha["justificativa"])
        with direita:
            st.write(f"Crédito: **{moeda(linha['credito'])}**")
            st.write(f"Prazo: **{int(linha['prazo'])} meses**")
            st.write(f"Parcela: **{moeda(linha['parcela'])}**")
            if not eh_teste:
                score = float(linha["score"])
                st.progress(
                    min(max(score / 100, 0.0), 1.0),
                    text=f"Aderência: {score:.0f}/100",
                )


# ----- A página começa aqui -----
st.header("Resultado")

if "usuario_id" not in st.session_state:
    st.error("Usuário não identificado. Abra o aplicativo pelo app.py.")
    st.stop()

usuario_id = st.session_state["usuario_id"]

# Primeiro tenta a memória da sessão; se não houver, busca no banco
perfil = st.session_state.get("perfil")
decisao = st.session_state.get("decisao")
perfil_id = st.session_state.get("perfil_id")

if perfil is None or decisao is None:
    perfil, decisao, perfil_id = carregar_do_banco(usuario_id)

if perfil is None:
    st.info(
        "Você ainda não avaliou nenhum perfil. Abra a página **Meu perfil**, "
        "preencha os campos e clique em **Avaliar perfil**."
    )
    st.stop()

# ----- Decisão -----
if decisao.get("motivo") == "teste":
    st.warning("Decisão de TESTE: a função decidir() da Pessoa B ainda não existe.")

aprovado = decisao["status"] == "Aprovado"
if aprovado:
    st.success("✅ Perfil aprovado")
else:
    st.error("❌ Perfil recusado")

col1, col2 = st.columns(2)
col1.metric("Probabilidade de aprovação", percentual(decisao["probabilidade"]))
col2.metric("Decisão feita por", decisao["origem"])
st.progress(min(max(float(decisao["probabilidade"]), 0.0), 1.0))

st.write(f"**Motivo:** {decisao['motivo']}")

if decisao.get("fatores"):
    if decisao["origem"] == "Política":
        st.write("**Motivos da recusa:**")
    else:
        st.write("**Fatores que mais pesam no modelo (valem para qualquer perfil):**")
    for fator in decisao["fatores"]:
        st.markdown(f"- {fator}")

# ----- Indicadores -----
st.subheader("Seus indicadores")
ind = recomendador.calcular_indicadores(perfil)
i1, i2, i3, i4 = st.columns(4)
i1.metric("Parcela estimada", moeda(ind["parcela_estimada"]))
i2.metric("Comprometimento", percentual(ind["comprometimento"]))
i3.metric("Entrada / crédito", percentual(ind["entrada_pct"]))
i4.metric("Crédito / renda anual", razao(ind["credito_renda"]))

# ----- Recusado: sugestões de ajuste -----
if not aprovado:
    st.subheader("Como melhorar este perfil")
    if hasattr(recomendador, "sugerir_ajustes"):
        for sugestao in recomendador.sugerir_ajustes(perfil):
            st.markdown(f"- {sugestao}")
    else:
        st.info(
            "As sugestões aparecerão quando a função sugerir_ajustes() "
            "da Pessoa B ficar pronta."
        )
    st.caption("Na página Simulador você poderá testar essas mudanças.")
    st.stop()

# ----- Aprovado: recomendações -----
st.subheader("Consórcios recomendados")
ranking, eh_teste = obter_ranking(perfil)

if eh_teste:
    st.warning("Recomendações de EXEMPLO: a função ranquear() da Pessoa B ainda não existe.")

if ranking.empty:
    st.info("Nenhum consórcio do catálogo corresponde ao objetivo escolhido.")
else:
    for posicao, (_, linha) in enumerate(ranking.head(5).iterrows(), start=1):
        mostrar_consorcio(posicao, linha, eh_teste)

    # Grava as recomendações uma vez por perfil (só com a função real da B)
    chave = f"recomendacoes_salvas_{perfil_id}"
    if not eh_teste and hasattr(banco, "salvar_recomendacoes"):
        if not st.session_state.get(chave):
            banco.salvar_recomendacoes(perfil_id, ranking)
            st.session_state[chave] = True
        