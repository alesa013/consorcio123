# Contrato técnico v3.3: 123 Consórcio

Vale para as duas pessoas. **Se o chat de qualquer uma contradisser este texto, vale este texto.**
Versão consolidada: substitui a v3.1 e a v3.2. Data: 23/11/2026.

> ⚠️ Dados e decisões são fictícios. Não é análise de crédito real.

## 0. Histórico de versões

| Versão | O que mudou |
| --- | --- |
| v3 | Base inicial: login Microsoft, 9 campos de perfil, IA com árvore de decisão, 4 tabelas |
| v3.1 | 10.000 perfis sintéticos, fórmulas e distribuições calibradas, limites de validação, `origem` na decisão, regra do ranking, coluna `nome` no CSV |
| v3.2 | Regressão logística no lugar da árvore, fatores individuais, treino só com perfis fora da política, cache e arquivo versionado do modelo, `decidir()` escrita pela Pessoa A |
| **v3.3** | Consolidação dos dois textos; CRUD do catálogo no `banco.py` (escrito pela A); constante `COMPROMETIMENTO_NOTA_ZERO`; retornos das funções do banco; 6 páginas; métrica do sistema completo; documentos novos; cronograma final |

## 1. Visão geral

Protótipo que recebe o perfil de um usuário autenticado, decide **Aprovado** ou **Recusado** para o consórcio (política de regras mais modelo de IA), explica a decisão e recomenda consórcios do catálogo. Demonstração ao vivo no computador da Pessoa A.

**Prazos:** código pronto e entregue para testes em **26/11**; código congelado na noite de **25/11**; testes, documentação e GitHub até **01/12**.

## 2. Versões e ambiente

- Python 3.14.10 (versão em que o sistema foi testado)
- Streamlit 1.67.0, pandas 3.1.1, scikit-learn 1.9.1 ou superior (conforme `requirements.txt`)
- Rodar: `python -m streamlit run app.py`
- Checar a sintaxe de um arquivo: `python -m py_compile arquivo.py`
- `LOGIN_ATIVO = True` ou `False` no topo do `app.py`. Com `False`, o app usa o usuário `demo@local` ("Usuário de demonstração"). A Pessoa B desenvolve com `False` (não precisa do Azure).

## 3. Arquivos e donas

Cada arquivo tem uma dona. Ninguém edita o arquivo da outra, **salvo nas exceções abaixo**.

| Pessoa | Arquivos |
| --- | --- |
| **A** | `app.py`, `paginas/` (`perfil.py`, `resultado.py`, `simulador.py`, `catalogo.py`, `acompanhamento.py`, `conta.py`), `formatacao.py`, `teste_decidir.py`, `README.md`, `docs/ARQUITETURA.md`, `docs/PLANO_DE_TESTES.md`, `docs/PROBLEMAS.md` |
| **B** | `banco.py`, `dados_sinteticos.py`, `modelo.py`, `recomendador.py`, `consorcios.csv`, `teste_banco.py`, `teste_recomendador.py`, `teste_dados_sinteticos.py`, `docs/comparacao_modelos.md` |
| **Juntas** | `requirements.txt`, `.gitignore`, `docs/CONTRATO.md` |

**Exceções de autoria (escritas pela Pessoa A, com acordo):**

- `recomendador.py`: a função `decidir()` e a auxiliar `_maiuscula()`, no final do arquivo.
- `banco.py`: `criar_consorcio`, `editar_consorcio`, `excluir_consorcio` e as auxiliares `_validar_consorcio` e `_calcular_parcela`, antes do bloco `if __name__ == "__main__":`.
- **Quem edita esses arquivos faz `git pull` antes**, para não dar conflito.

**Fora do GitHub (`.gitignore`):** `.venv/`, `__pycache__/`, `.streamlit/secrets.toml`, `consorcio.db`, `*.joblib`, `dados_treino.csv`.
**No GitHub:** `.streamlit/secrets.toml.example` (valores falsos).

## 4. Perfil (dicionário Python; chaves sem acento)

| Chave | Tipo | Conteúdo |
| --- | --- | --- |
| `renda` | float | R$ por mês, líquida |
| `vinculo` | texto | `"CLT"`, `"Servidor público"`, `"Autônomo/MEI"`, `"Empresário"` ou `"Aposentado/Pensionista"` |
| `tempo_vinculo` | int | meses no vínculo atual |
| `dividas_mensais` | float | R$ por mês em parcelas já existentes |
| `restricao` | bool | `True` se há restrição no nome |
| `entrada` | float | R$ disponível para entrada ou lance |
| `objetivo` | texto | exatamente `"Imóvel"`, `"Veículo"` ou `"Serviço"` |
| `credito` | float | R$ de crédito desejado |
| `prazo` | int | meses: 36, 60, 80, 120 ou 180 |

**Não coletar nem usar na decisão:** idade, gênero, estado civil, cidade, nome.

## 5. Indicadores (calculados, nunca digitados)

| Indicador | Fórmula |
| --- | --- |
| `parcela_estimada` | (credito − entrada) × (1 + TAXA_ADMIN) ÷ prazo |
| `comprometimento` | (dividas_mensais + parcela_estimada) ÷ renda |
| `entrada_pct` | entrada ÷ credito |
| `credito_renda` | credito ÷ (renda × 12) |

## 6. Constantes

Ficam no topo de `recomendador.py`:

| Constante | Valor | Uso |
| --- | --- | --- |
| `RENDA_MINIMA` | 1500 | política de recusa |
| `LIMITE_COMPROMETIMENTO` | 0.40 | política de recusa e ranking |
| `COMPROMETIMENTO_IDEAL` | 0.20 | pontuação dos rótulos |
| `NOTA_MINIMA` | 60 | rótulo de aprovado nos dados de treino |
| `ENTRADA_REF` | 0.20 | pontuação dos rótulos |
| `LIMITE_CREDITO_RENDA` | 6 | pontuação dos rótulos |
| `TAXA_ADMIN` | 0.15 (fictícia) | parcela |
| `COMPROMETIMENTO_NOTA_ZERO` | 0.80 (= 2 × limite) | ranking: a nota da parcela chega a 0 neste ponto |

Em `dados_sinteticos.py`: `N_PERFIS = 10000`, `RUIDO_ROTULOS = 0.05`, `SEMENTE = 42`.

## 7. Validação (`validar_perfil` devolve lista de textos de erro; vazia = ok)

| Campo | Regra |
| --- | --- |
| `renda` | entre 0,01 e 200.000 |
| `dividas_mensais` | entre 0 e 100.000 |
| `tempo_vinculo` | entre 0 e 600 |
| `credito` | entre 5.000 e 600.000 |
| `entrada` | maior ou igual a 0 e **menor** que o crédito |
| `vinculo`, `objetivo`, `prazo` | dentro das listas aceitas |
| `restricao` | booleano |

**Erro de preenchimento NÃO é recusa:** mostra a mensagem e **não grava** no banco.

## 8. Decisão em duas camadas

`decidir(perfil)` devolve sempre este dicionário:

```
{"status": "Aprovado" | "Recusado",
 "probabilidade": 0 a 1 (chance de aprovação),
 "origem": "Política" | "Modelo",
 "motivo": texto curto,
 "fatores": lista com até 3 textos}
```

**Atenção:** `origem` é **exatamente** `"Política"` (com acento) ou `"Modelo"`, em todo o sistema, inclusive no banco. As páginas comparam o texto exato.

**Camada 1: política** (origem `"Política"`, probabilidade 0,0). Recusa se `restricao = True`, ou `renda < RENDA_MINIMA`, ou `comprometimento > LIMITE_COMPROMETIMENTO`.

- `motivo`: `"Recusado pela política: <motivos separados por '; '>."`
- `fatores`: os próprios motivos, com a primeira letra maiúscula (até 3).

**Camada 2: modelo** (origem `"Modelo"`). Nos demais casos decide o modelo; Aprovado se `probabilidade >= 0.5`.

- `motivo`: `"O modelo estimou chance de aprovação de NN% para este perfil."`
- `fatores`: até 3 fatores **individuais** daquele perfil, em português simples, no formato `"<descrição com o valor>: ajuda na aprovação"` ou `"<descrição com o valor>: pesa contra a aprovação"`. Exemplos: `"Comprometimento da renda de 19,0%: ajuda na aprovação"`, `"Entrada de 0,0% do crédito: pesa contra a aprovação"`.

## 9. Dados sintéticos e modelo de IA

**Pontuação (só para rotular os dados de treino), de 0 a 100:**

```
n_comprometimento = 40 * clip((LIMITE_COMPROMETIMENTO - comprometimento)
                    / (LIMITE_COMPROMETIMENTO - COMPROMETIMENTO_IDEAL), 0, 1)
n_estabilidade    = 25 * (0,6 * base_vinculo + 0,4 * min(tempo_vinculo / 24, 1))
    base_vinculo: Servidor público 1,0 | Aposentado/Pensionista 1,0 | CLT 0,8 |
                  Empresário 0,6 | Autônomo/MEI 0,5
n_entrada         = 20 * min(entrada_pct / ENTRADA_REF, 1)
n_credito_renda   = 15 * clip(1 - credito_renda / LIMITE_CREDITO_RENDA, 0, 1)
nota = soma dos quatro
```

**Rótulo:** Aprovado se a política não recusa e `nota >= NOTA_MINIMA`. Depois, 5% dos rótulos (sorteados) são invertidos (ruído).

**Distribuições de referência (calibradas por simulação):**

| Variável | Distribuição |
| --- | --- |
| `renda` | lognormal, mediana 3.800, sigma 0,6, limitada entre 900 e 40.000 |
| `vinculo` | CLT 45%, Servidor 12%, Autônomo/MEI 20%, Empresário 8%, Aposentado/Pensionista 15% |
| `tempo_vinculo` | exponencial; médias em meses: CLT 36, Servidor 90, Autônomo 30, Empresário 60, Aposentado 120; entre 1 e 480 |
| `dividas_mensais` | renda × Beta(1,5; 7) |
| `restricao` | 10% verdadeiro |
| `objetivo` | Imóvel 40%, Veículo 40%, Serviço 20% |
| `credito` | renda × 12 × uniforme(0,25 a 2,2), limitado à faixa do objetivo (Imóvel 60.000-600.000; Veículo 20.000-180.000; Serviço 5.000-40.000), arredondado ao milhar |
| `prazo` | Imóvel 120 ou 180; Veículo 60, 80 ou 120; Serviço 36 ou 60 |
| `entrada` | crédito × uniforme(0 a 0,40) |

**O crédito precisa acompanhar a renda.** Sem isso, a política recusa mais de 70% dos perfis e o modelo não aprende nada útil.

**Conferências obrigatórias após gerar os dados:** recusados pela política entre 30% e 45%; aprovados no total entre 40% e 60%; perfis de fronteira (nota 52 a 68, fora da política) pelo menos 10%. Resultado atual: 40,7%, 46,5% e 15,1%.

**Modelo oficial (v3.2):**

- `LogisticRegression(max_iter=1000)` dentro de um `Pipeline` com `ColumnTransformer`: `OneHotEncoder` em `vinculo` e `StandardScaler` nos campos numéricos e nos 4 indicadores.
- Entradas: todos os campos do perfil **exceto `objetivo`**, mais os 4 indicadores.
- **Treino apenas com os perfis que a política NÃO recusa** (variante A). Divisão 80/20 estratificada, `random_state=42` (2.000 perfis de teste, dos quais 1.171 na faixa intermediária).
- Modelo salvo em `modelo_v3_2.joblib` (gerado em cada máquina; se não existir, `carregar_modelo()` treina sozinho) e mantido em **cache de memória** (o Simulador chama `decidir()` até ~20 vezes a cada movimento).

**Resultado dos experimentos** (faixa intermediária; fonte: `docs/comparacao_modelos.md`):

| Variante | Acurácia | Brier |
| --- | --- | --- |
| Treino com todos os perfis | 89,2% | 0,101 |
| **A) só perfis fora da política (adotada)** | **90,3%** | **0,088** |
| B) `class_weight="balanced"` | 88,9% | 0,099 |
| A+B | 82,1% | 0,124 |

**Métricas do modelo adotado (faixa intermediária):** acurácia 90,3%, precisão 92,0%, revocação 95,5%; matriz `[[210, 74], [40, 847]]`; referência "aprovar todos": 75,7%.

**Métricas a registrar em `metricas()`:** (1) faixa intermediária; (2) **sistema completo** (política + modelo) sobre os 2.000 perfis de teste. A métrica de "todos os perfis" apenas do modelo deixa de valer, porque a política decide antes dele. Estimativa pelas matrizes: cerca de 92% (1.843 de 2.000), **a confirmar no código**.

**Limitação a constar na documentação:** o modelo aprende a fórmula usada para rotular os dados fictícios, e não a realidade do crédito.

## 10. Ranking do catálogo e sugestões

**`ranquear(perfil)`:** só consórcios com `categoria` igual ao `objetivo`. Score de 0 a 100:

```
crédito (50): 50 * max(0, 1 - |credito_catalogo - credito| / credito)
prazo (25):   25 se igual; senão 25 * max(0, 1 - |prazo_catalogo - prazo| / prazo)
parcela (25): seja c = (dividas_mensais + parcela_catalogo) / renda
              25 se c <= LIMITE_COMPROMETIMENTO;
              senão diminui linearmente até 0 quando c = COMPROMETIMENTO_NOTA_ZERO
```

Ordem decrescente de score (empates mantêm a ordem do catálogo). Devolve DataFrame com as colunas `id, categoria, credito, prazo, parcela, nome, score, justificativa`; **vazio** se nada combinar. Há um segundo parâmetro opcional (`catalogo`) que a interface ignora.

**`sugerir_ajustes(perfil)`:** usa a própria `decidir()` para testar mudanças (crédito menor, entrada maior, prazo maior, dívidas menores) e só sugere o que realmente aprova, com valores concretos. **Cada sugestão vale sozinha**, salvo quando o texto diz o contrário. Devolve lista vazia para perfil aprovado. Casos especiais: restrição no nome (a primeira sugestão é regularizar), renda abaixo do mínimo (o texto explica) e, se nenhum ajuste isolado resolver, sugere combinar ajustes.

## 11. Funções

**`recomendador.py`**

| Função | Entrada | Saída |
| --- | --- | --- |
| `validar_perfil(perfil)` | perfil | lista de textos de erro |
| `calcular_indicadores(perfil)` | perfil | dicionário com os 4 indicadores |
| `decidir(perfil)` | perfil validado | decisão (seção 8). Escrita pela Pessoa A |
| `ranquear(perfil)` | perfil | DataFrame (seção 10) |
| `sugerir_ajustes(perfil)` | perfil | lista de textos |

**`modelo.py`**

| Função | Saída |
| --- | --- |
| `treinar_modelo()` | treina, salva `modelo_v3_2.joblib` e devolve as métricas |
| `carregar_modelo()` | carrega (com cache); treina antes se o arquivo não existir |
| `avaliar_com_modelo(perfil)` | decisão do modelo (formato da seção 8) |
| `metricas()` | dicionário com as métricas (seção 9) |

**`dados_sinteticos.py`:** `gerar_perfis(n, semente)` devolve um DataFrame com os 9 campos e a coluna `aprovado`.

**`banco.py`** (cada função abre e fecha a própria conexão)

| Função | Saída |
| --- | --- |
| `iniciar_banco()` | cria as tabelas; se estiverem vazias, carrega o catálogo do CSV e 4 perfis de demonstração; pode rodar sempre |
| `upsert_usuario(email, nome)` | id do usuário |
| `salvar_perfil(usuario_id, perfil, decisao)` | id do perfil |
| `ultimo_perfil(usuario_id)` | dicionário com `id`, `usuario_id`, `criado_em`, `status`, `probabilidade`, `origem`, `motivo` e os 9 campos (`restricao` como `True`/`False`), ou `None` |
| `listar_consorcios()` | DataFrame com `id, categoria, credito, prazo, parcela, nome` |
| `salvar_recomendacoes(perfil_id, df)` | quantidade de linhas gravadas; **substitui** o ranking anterior do perfil (não duplica); `df` vazio devolve 0 sem mexer |
| `excluir_dados_usuario(usuario_id)` | `{"recomendacoes": n, "perfis": n, "usuarios": n}`; apaga nessa ordem; tudo ou nada |
| `resumo_dashboard()` | dicionário (abaixo); conta **todos** os perfis, inclusive os de demonstração |
| `criar_consorcio(dados)` | id novo. `dados` = `categoria`, `credito`, `prazo`, `nome`; a parcela é calculada na função; levanta `ValueError` se inválido |
| `editar_consorcio(id, dados)` | 1 se achou o consórcio, 0 se o id não existe; recalcula a parcela |
| `excluir_consorcio(id)` | `{"recomendacoes": n, "consorcios": n}`; apaga antes as recomendações que apontam para ele |

**Formato do `resumo_dashboard()`:**

```
{"total_perfis": int, "total_usuarios": int,
 "taxa_aprovacao": 0 a 1, "probabilidade_media": 0 a 1,
 "por_objetivo": {"Imóvel": {"total": n, "aprovados": m},
                  "Veículo": {...}, "Serviço": {...}}}
```

Sem dados individuais. Os três objetivos sempre aparecem.

## 12. Banco de dados (SQLite, `consorcio.db` na raiz)

```
usuarios(id, email UNIQUE, nome, criado_em)
perfis(id, usuario_id, criado_em, renda, vinculo, tempo_vinculo, dividas_mensais,
       restricao, entrada, objetivo, credito, prazo, status, probabilidade, origem, motivo)
consorcios(id, categoria, credito, prazo, parcela, nome)
recomendacoes(id, perfil_id, consorcio_id, score, justificativa, criado_em)
```

- As chaves estrangeiras ficam ligadas (`PRAGMA foreign_keys = ON`): apagar na ordem **recomendações, perfis, usuário** (e **recomendações, consórcio**).
- `restricao` é guardada como 1 ou 0 e volta como `True`/`False`.
- `origem` guarda `"Política"` (com acento) ou `"Modelo"`.
- Comportamento conhecido: se todos os consórcios forem apagados, o `iniciar_banco()` recarrega o CSV na próxima abertura.

## 13. Catálogo `consorcios.csv`

- Colunas, nesta ordem: `id,categoria,credito,prazo,parcela,nome`.
- Vírgula como separador, ponto decimal, UTF-8, sem "R$".
- 8 a 12 consórcios (hoje, 10); categoria igual a um dos objetivos; prazos só entre os aceitos.
- `parcela = credito × (1 + TAXA_ADMIN) ÷ prazo`, com 2 casas decimais.

## 14. Aplicação (Pessoa A)

- `app.py` usa `st.navigation` com **6 páginas**: Meu perfil, Resultado, Simulador, Catálogo, Acompanhamento e Minha conta.
- Login: `st.login("microsoft")`, `st.user.email`, `st.user.name`, `st.logout()`.
- Memória da sessão (`st.session_state`): `usuario_id`, `usuario_email`, `usuario_nome`, `perfil`, `decisao`, `perfil_id`, `recomendacoes_salvas_<id>` e `catalogo_msg`.
- A interface só chama as funções da seção 11; **nenhuma regra de negócio** nas páginas. As páginas checam se a função existe (`hasattr`) e avisam, em vez de quebrar.
- Sem papéis: qualquer usuário logado vê todas as páginas, inclusive a edição do catálogo (demonstração local).
- Avisos fixos na tela: (1) dados e decisão são fictícios e não são análise de crédito real; (2) o e-mail do login fica registrado no banco.
- `formatacao.py` formata moeda, porcentagem e razão na tela.

## 15. Git e GitHub

- Repositório **privado**, branch única `main`. Rotina: `git pull` ao começar; `git add`, `git commit` e `git push` ao terminar cada bloco.
- Mensagens de commit começam com `"A:"` ou `"B:"`.
- Tags: `v0.9-testes` (25/11 à noite, código congelado) e `v1.0` (30/11).
- `secrets.toml` e `consorcio.db` **nunca** são enviados. Se um segredo vazar, gerar outro no Azure na hora (apagar o arquivo não limpa o histórico).

## 16. Testes e documentação

- Scripts de teste: `teste_banco.py`, `teste_recomendador.py`, `teste_dados_sinteticos.py`, `teste_decidir.py`.
- `docs/PLANO_DE_TESTES.md` (casos, divisão da execução, roteiro da demonstração e plano B) e `docs/PROBLEMAS.md` (registro de problemas).
- Documentos técnicos: `README.md`, `docs/ARQUITETURA.md`, `docs/CONTRATO.md`, `docs/comparacao_modelos.md`, e a fazer: `docs/IA.md`, `docs/MODELO_DE_DADOS.md`, `docs/BACKLOG.md` (Pessoa B) e `docs/MANUAL_DAS_TELAS.md` (Pessoa A).

## 17. Cronograma final

| Data | Foco |
| --- | --- |
| Ter 24/11 | Revisão cruzada do código; revisão do contrato e da arquitetura; repositório privado |
| Qua 25/11 | Testes ponta a ponta (divisão do plano de testes); correções; **congelamento à noite** (`v0.9-testes`), só depois de as duas dizerem "ok para congelar" |
| Qui 26/11 | Conferência final de manhã e **entrega para testes** |
| Sex 27/11 | Segunda rodada de testes; **somente correções** |
| Sáb 28/11 | Documentação (A: manual das telas e README final; B: IA e modelo de dados) |
| Dom 29/11 | Backlog; plano de testes com resultados; revisão cruzada dos documentos; ensaio nº 1 da demonstração |
| Seg 30/11 | Repositório final, tag `v1.0`; ensaio nº 2 (cronometrado, também sem login) |
| Ter 01/12 | Entrega (reserva de 1 hora; conferir login e internet antes) |

**Depois do congelamento (25/11):** nenhuma funcionalidade nova. Só correção de erro, com commit começando por `"A: fix"` ou `"B: fix"`.

## 18. Convivência

Ninguém muda este contrato sozinha: avisa a outra, sobe a versão (v3.4...) e as duas atualizam os chats.
