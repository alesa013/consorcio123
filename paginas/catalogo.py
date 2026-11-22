# paginas/catalogo.py - página "Catálogo" (Pessoa A)
# Lista os consórcios e, quando as funções da Pessoa B existirem,
# permite adicionar, editar e excluir.

import streamlit as st

import banco
from formatacao import moeda

CATEGORIAS = ["Imóvel", "Veículo", "Serviço"]
PRAZOS = [36, 60, 80, 120, 180]


def indice(opcoes, valor, padrao=0):
    """Posição de 'valor' na lista; se não estiver nela, usa a posição padrão."""
    return opcoes.index(valor) if valor in opcoes else padrao


def tem(nome_funcao):
    """True se a Pessoa B já entregou essa função em banco.py."""
    return hasattr(banco, nome_funcao)


def avisar_e_recarregar(texto):
    """Guarda a mensagem e reexecuta a página para atualizar a lista."""
    st.session_state["catalogo_msg"] = texto
    st.rerun()


st.header("Catálogo de consórcios")
st.caption(
    "Consórcios fictícios usados nas recomendações. "
    "Na demonstração, qualquer usuário logado pode editar o catálogo."
)

# Mensagem da ação anterior (adicionar, editar ou excluir)
mensagem = st.session_state.pop("catalogo_msg", None)
if mensagem:
    st.success(mensagem)

catalogo = banco.listar_consorcios()

# ----- Lista com filtro -----
filtro = st.selectbox("Filtrar por categoria", ["Todas"] + CATEGORIAS)
if filtro == "Todas":
    vista = catalogo
else:
    vista = catalogo[catalogo["categoria"] == filtro]

if vista.empty:
    st.info("Nenhum consórcio nesta categoria.")
else:
    exibir = vista.copy()
    exibir["credito"] = exibir["credito"].apply(moeda)
    exibir["parcela"] = exibir["parcela"].apply(moeda)
    exibir["prazo"] = exibir["prazo"].astype(int).astype(str) + " meses"
    colunas = [c for c in ["id", "nome", "categoria", "credito", "prazo", "parcela"]
               if c in exibir.columns]
    exibir = exibir[colunas].rename(
        columns={
            "id": "ID",
            "nome": "Nome",
            "categoria": "Categoria",
            "credito": "Crédito",
            "prazo": "Prazo",
            "parcela": "Parcela",
        }
    )
    st.dataframe(exibir, hide_index=True)

st.caption(f"{len(catalogo)} consórcios no catálogo (o contrato prevê de 8 a 12).")

# ----- Adicionar -----
st.subheader("Adicionar consórcio")
if not tem("criar_consorcio"):
    st.info("A função criar_consorcio() da Pessoa B ainda não existe.")
else:
    with st.form("form_novo", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            novo_nome = st.text_input("Nome do consórcio")
            nova_categoria = st.selectbox("Categoria", CATEGORIAS)
        with col2:
            novo_credito = st.number_input(
                "Crédito (R$)", min_value=0.0, value=0.0, step=1000.0, format="%.2f"
            )
            novo_prazo = st.selectbox("Prazo (meses)", PRAZOS)
        st.caption("A parcela é calculada automaticamente.")
        adicionar = st.form_submit_button("Adicionar", type="primary")

    if adicionar:
        if not novo_nome.strip():
            st.error("Informe o nome do consórcio.")
        elif novo_credito <= 0:
            st.error("O crédito deve ser maior que zero.")
        else:
            banco.criar_consorcio(
                {
                    "categoria": nova_categoria,
                    "credito": float(novo_credito),
                    "prazo": int(novo_prazo),
                    "nome": novo_nome.strip(),
                }
            )
            avisar_e_recarregar("Consórcio adicionado.")

# ----- Editar ou excluir -----
st.subheader("Editar ou excluir")
if catalogo.empty:
    st.info("Não há consórcios para editar.")
else:
    rotulos = {}
    for _, linha in catalogo.iterrows():
        nome_exibido = linha["nome"] if "nome" in catalogo.columns else "Consórcio"
        rotulos[int(linha["id"])] = f"{int(linha['id'])} - {nome_exibido} ({linha['categoria']})"

    escolhido = st.selectbox(
        "Escolha o consórcio",
        list(rotulos.keys()),
        format_func=lambda i: rotulos[i],
    )
    atual = catalogo[catalogo["id"] == escolhido].iloc[0]

    # --- Editar ---
    if not tem("editar_consorcio"):
        st.info("A função editar_consorcio() da Pessoa B ainda não existe.")
    else:
        with st.form(f"form_editar_{escolhido}"):
            col1, col2 = st.columns(2)
            with col1:
                ed_nome = st.text_input(
                    "Nome",
                    value=str(atual["nome"]) if "nome" in catalogo.columns else "",
                    key=f"ed_nome_{escolhido}",
                )
                ed_categoria = st.selectbox(
                    "Categoria",
                    CATEGORIAS,
                    index=indice(CATEGORIAS, atual["categoria"]),
                    key=f"ed_cat_{escolhido}",
                )
            with col2:
                ed_credito = st.number_input(
                    "Crédito (R$)",
                    min_value=0.0,
                    value=float(atual["credito"]),
                    step=1000.0,
                    format="%.2f",
                    key=f"ed_cred_{escolhido}",
                )
                ed_prazo = st.selectbox(
                    "Prazo (meses)",
                    PRAZOS,
                    index=indice(PRAZOS, int(atual["prazo"])),
                    key=f"ed_prazo_{escolhido}",
                )
            salvar = st.form_submit_button("Salvar alterações")

        if salvar:
            if not ed_nome.strip():
                st.error("Informe o nome do consórcio.")
            elif ed_credito <= 0:
                st.error("O crédito deve ser maior que zero.")
            else:
                banco.editar_consorcio(
                    int(escolhido),
                    {
                        "categoria": ed_categoria,
                        "credito": float(ed_credito),
                        "prazo": int(ed_prazo),
                        "nome": ed_nome.strip(),
                    },
                )
                avisar_e_recarregar("Consórcio atualizado.")

    # --- Excluir ---
    if not tem("excluir_consorcio"):
        st.info("A função excluir_consorcio() da Pessoa B ainda não existe.")
    else:
        confirmou = st.checkbox(
            "Confirmo a exclusão deste consórcio", key=f"conf_{escolhido}"
        )
        if st.button("Excluir consórcio", disabled=not confirmou):
            banco.excluir_consorcio(int(escolhido))
            avisar_e_recarregar("Consórcio excluído.")