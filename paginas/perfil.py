# paginas/perfil.py - página "Meu perfil" (Pessoa A)
# Formulário com os 9 campos do contrato, validação e salvamento no banco.

import streamlit as st

import banco
import recomendador

# Opções aceitas (contrato, seção 4; não mudar a grafia)
VINCULOS = [
    "CLT",
    "Servidor público",
    "Autônomo/MEI",
    "Empresário",
    "Aposentado/Pensionista",
]
OBJETIVOS = ["Imóvel", "Veículo", "Serviço"]
PRAZOS = [36, 60, 80, 120, 180]

# Decisão de teste (contrato, seção 8), usada enquanto a decidir() da Pessoa B
# não existe.
DECISAO_TESTE = {
    "status": "Aprovado",
    "probabilidade": 0.8,
    "origem": "Modelo",
    "motivo": "teste",
    "fatores": [],
}


def moeda(valor):
    """Formata como moeda brasileira: 1234.5 -> R$ 1.234,50"""
    texto = f"{valor:,.2f}"
    texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


def percentual(valor):
    """0.324 -> 32,4%"""
    return f"{valor * 100:.1f}%".replace(".", ",")


def indice(opcoes, valor, padrao=0):
    """Posição de 'valor' na lista; se não estiver nela, usa a posição padrão."""
    return opcoes.index(valor) if valor in opcoes else padrao


def obter_decisao(perfil):
    """Usa a decidir() da Pessoa B se já existir; senão, a decisão de teste.
    Devolve (decisao, eh_teste)."""
    if hasattr(recomendador, "decidir"):
        return recomendador.decidir(perfil), False
    return DECISAO_TESTE, True


st.header("Meu perfil")
st.caption("Preencha os dados abaixo. Use valores fictícios.")

# Esta página depende do usuário registrado pelo app.py
if "usuario_id" not in st.session_state:
    st.error("Usuário não identificado. Abra o aplicativo pelo app.py.")
    st.stop()

usuario_id = st.session_state["usuario_id"]

# Último perfil salvo (dicionário vazio se a pessoa ainda não tem nenhum)
anterior = banco.ultimo_perfil(usuario_id) or {}
if anterior:
    st.caption("Os campos vêm preenchidos com o seu último perfil salvo.")

with st.form("form_perfil"):
    col1, col2 = st.columns(2)

    with col1:
        renda = st.number_input(
            "Renda mensal líquida (R$)",
            min_value=0.0,
            value=float(anterior.get("renda", 0.0)),
            step=100.0,
            format="%.2f",
            help="Quanto você recebe por mês, já descontados os impostos (valor fictício).",
        )
        vinculo = st.selectbox(
            "Tipo de vínculo",
            VINCULOS,
            index=indice(VINCULOS, anterior.get("vinculo")),
        )
        tempo_vinculo = st.number_input(
            "Tempo no vínculo atual (meses)",
            min_value=0,
            value=int(anterior.get("tempo_vinculo", 0)),
            step=1,
        )
        dividas = st.number_input(
            "Parcelas e dívidas mensais atuais (R$)",
            min_value=0.0,
            value=float(anterior.get("dividas_mensais", 0.0)),
            step=50.0,
            format="%.2f",
            help="Soma do que você já paga por mês em financiamentos, cartões etc.",
        )
        restricao_txt = st.radio(
            "Possui restrição no nome?",
            ["Não", "Sim"],
            index=1 if anterior.get("restricao") else 0,
            horizontal=True,
        )

    with col2:
        objetivo = st.selectbox(
            "Objetivo do consórcio",
            OBJETIVOS,
            index=indice(OBJETIVOS, anterior.get("objetivo")),
        )
        credito = st.number_input(
            "Valor de crédito desejado (R$)",
            min_value=0.0,
            value=float(anterior.get("credito", 0.0)),
            step=1000.0,
            format="%.2f",
        )
        entrada = st.number_input(
            "Valor disponível para entrada/lance (R$)",
            min_value=0.0,
            value=float(anterior.get("entrada", 0.0)),
            step=500.0,
            format="%.2f",
            help="Quanto você consegue pagar de entrada. Pode ser zero.",
        )
        prazo = st.selectbox(
            "Prazo preferido (meses)",
            PRAZOS,
            index=indice(PRAZOS, anterior.get("prazo")),
        )

    enviado = st.form_submit_button("Avaliar perfil", type="primary")

if enviado:
    # Perfil no formato do contrato (seção 4): chaves e tipos exatos
    perfil = {
        "renda": float(renda),
        "vinculo": vinculo,
        "tempo_vinculo": int(tempo_vinculo),
        "dividas_mensais": float(dividas),
        "restricao": restricao_txt == "Sim",
        "entrada": float(entrada),
        "objetivo": objetivo,
        "credito": float(credito),
        "prazo": int(prazo),
    }

    erros = recomendador.validar_perfil(perfil)

    if erros:
        # Erro de preenchimento: mostra e NÃO grava
        for erro in erros:
            st.error(erro)
        st.caption("O perfil não foi salvo. Corrija os pontos acima e envie de novo.")
    else:
        decisao, eh_teste = obter_decisao(perfil)
        perfil_id = banco.salvar_perfil(usuario_id, perfil, decisao)

        # Guarda na memória da sessão para a página Resultado
        st.session_state["perfil"] = perfil
        st.session_state["decisao"] = decisao
        st.session_state["perfil_id"] = perfil_id

        st.success("Perfil salvo com sucesso!")
        if eh_teste:
            st.warning(
                "Decisão de TESTE: a função decidir() da Pessoa B ainda não existe."
            )

        st.subheader("Seus indicadores")
        ind = recomendador.calcular_indicadores(perfil)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Parcela estimada", moeda(ind["parcela_estimada"]))
        c2.metric("Comprometimento", percentual(ind["comprometimento"]))
        c3.metric("Entrada / crédito", percentual(ind["entrada_pct"]))
        c4.metric("Crédito / renda anual", f"{ind['credito_renda']:.2f}".replace(".", ",") + "x")

        st.info("A decisão e as recomendações aparecerão na página Resultado.")