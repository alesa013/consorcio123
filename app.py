import streamlit as st

# Interruptor do login (contrato, seção 2).
# True = exige login Microsoft | False = usuário de demonstração
LOGIN_ATIVO = True

st.set_page_config(page_title="123 Consórcio", page_icon="🔐")


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


usuario = obter_usuario()

st.title("123 Consórcio - teste de login")
mostrar_avisos()

if usuario is None:
    st.write("Entre com sua conta Microsoft para continuar.")
    if st.button("Entrar com Microsoft"):
        st.login("microsoft")
    st.stop()

email, nome = usuario
st.success("Login funcionou ✅")
st.write(f"Nome: {nome}")
st.write(f"E-mail: {email}")

if LOGIN_ATIVO and st.button("Sair"):
    st.logout()