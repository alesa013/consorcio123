# paginas/conta.py - página "Minha conta" (Pessoa A)
# Mostra os dados da conta e permite excluir tudo (privacidade).

import streamlit as st

import banco

# Chaves que o app guarda na memória da sessão
CHAVES_SESSAO = [
    "usuario_id",
    "usuario_email",
    "usuario_nome",
    "perfil",
    "decisao",
    "perfil_id",
]

st.header("Minha conta")

if "usuario_id" not in st.session_state:
    st.error("Usuário não identificado. Abra o aplicativo pelo app.py.")
    st.stop()

usuario_id = st.session_state["usuario_id"]

st.write(f"**Nome:** {st.session_state['usuario_nome']}")
st.write(f"**E-mail:** {st.session_state['usuario_email']}")

# ----- Transparência: o que está guardado -----
st.subheader("Dados guardados sobre você")
st.write(
    "O sistema guarda o seu nome e e-mail (vindos do login), os perfis que você "
    "avaliou, as decisões e as recomendações geradas."
)
ultimo = banco.ultimo_perfil(usuario_id)
if ultimo:
    with st.expander("Ver meu último perfil salvo"):
        st.json(ultimo)
else:
    st.caption("Você ainda não salvou nenhum perfil.")

# ----- Exclusão -----
st.subheader("Excluir meus dados")
st.warning(
    "Isto apaga o seu usuário, todos os seus perfis e as recomendações. "
    "A ação não pode ser desfeita e a sua sessão será encerrada."
)

confirmou = st.checkbox("Entendo que a exclusão é definitiva")
excluir = st.button("Excluir meus dados", type="primary", disabled=not confirmou)

if excluir:
    if not hasattr(banco, "excluir_dados_usuario"):
        st.error("A função excluir_dados_usuario() da Pessoa B ainda não existe.")
        st.stop()

    banco.excluir_dados_usuario(usuario_id)

    # Limpa a memória da sessão, inclusive as marcas de recomendações salvas
    for chave in CHAVES_SESSAO:
        st.session_state.pop(chave, None)
    for chave in [k for k in st.session_state if k.startswith("recomendacoes_salvas_")]:
        del st.session_state[chave]

    if getattr(st.user, "is_logged_in", False):
        st.logout()  # encerra a sessão; ao entrar de novo, a conta é recriada vazia
    else:
        st.success("Dados excluídos. Atualize a página para recomeçar.")
        st.stop()