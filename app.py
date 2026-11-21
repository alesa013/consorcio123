from pathlib import Path

import streamlit as st

import banco

# Interruptor do login (contrato, seção 2).
# True = exige login Microsoft | False = usuário de demonstração
LOGIN_ATIVO = True

st.set_page_config(page_title="123 Consórcio", page_icon="🏠")

PASTA_PAGINAS = Path(__file__).parent / "paginas"

# (arquivo, título no menu, ícone) - arquivos da Pessoa A, contrato seção 3
PAGINAS = [
    ("perfil.py", "Meu perfil", "📝"),
    ("resultado.py", "Resultado", "✅"),
    ("simulador.py", "Simulador", "🧮"),
    ("catalogo.py", "Catálogo", "📚"),
    ("acompanhamento.py", "Acompanhamento", "📊"),
    ("conta.py", "Minha conta", "👤"),
]


@st.cache_resource
def preparar_banco():
    """Cria o banco na primeira vez que o app abre (pode rodar sempre)."""
    banco.iniciar_banco()
    return True


def obter_usuario():
    """Devolve (email, nome), ou None se a pessoa ainda precisa entrar."""
    if not LOGIN_ATIVO:
        return "demo@local", "Usuário de demonstração"
    if not st.user.is_logged_in:
        return None
    return st.user.email, st.user.name


def mostrar_avisos():
    st.info("Dados e decisão são fictícios e não são análise de crédito real.")
    st.info("O e-mail do login fica registrado no banco de dados.")


preparar_banco()

usuario = obter_usuario()

# --- Tela de entrada ---
if usuario is None:
    st.title("123 Consórcio")
    mostrar_avisos()
    st.write("Entre com sua conta Microsoft para continuar.")
    if st.button("Entrar com Microsoft"):
        st.login("microsoft")
    st.stop()

email, nome = usuario

if not email:
    st.error("Sua conta não informou um e-mail. Saia e entre com outra conta.")
    if LOGIN_ATIVO and st.button("Sair"):
        st.logout()
    st.stop()

nome = nome or email

# --- Registra o usuário no banco uma vez por sessão ---
# As páginas leem estes valores de st.session_state.
if st.session_state.get("usuario_email") != email:
    st.session_state["usuario_id"] = banco.upsert_usuario(email, nome)
    st.session_state["usuario_email"] = email
    st.session_state["usuario_nome"] = nome

# --- Barra lateral ---
with st.sidebar:
    st.write(f"**{nome}**")
    st.caption(email)
    if LOGIN_ATIVO and st.button("Sair"):
        st.logout()

# --- Navegação: só as páginas que já existem em paginas/ ---
paginas = [
    st.Page(str(PASTA_PAGINAS / arquivo), title=titulo, icon=icone)
    for arquivo, titulo, icone in PAGINAS
    if (PASTA_PAGINAS / arquivo).exists()
]

mostrar_avisos()

if not paginas:
    st.info("Nenhuma página criada ainda na pasta paginas/.")
    st.stop()

st.navigation(paginas).run()