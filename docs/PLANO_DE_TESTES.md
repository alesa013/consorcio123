# Plano de testes: 123 Consórcio

> ⚠️ Todos os dados e decisões do sistema são fictícios. Os testes verificam o funcionamento do protótipo, e não a qualidade de uma análise de crédito real.

## 1. Objetivo e escopo

Verificar que o sistema funciona de ponta a ponta (login, perfil, decisão, recomendações, simulador, catálogo, acompanhamento e exclusão de dados), que a IA se comporta como descrito e que um usuário novo consegue instalar e executar o projeto seguindo o `README.md`.

## 2. Ambiente de teste

| Item | Valor |
| --- | --- |
| Sistema | Windows, PowerShell |
| Python | 3.14.10 |
| Streamlit | 1.67.0 |
| pandas | 3.1.1 |
| scikit-learn | versão do `requirements.txt` |
| Execução | `python -m streamlit run app.py` |
| Login | Conta Microsoft pessoal (`LOGIN_ATIVO = True`) ou modo demonstração (`False`) |

## 3. Como registrar os problemas

- Cada problema vai como uma linha em `docs/PROBLEMAS.md` (perfil usado, o que esperava, o que aconteceu, página e gravidade) e, se possível, como uma **Issue no GitHub**.
- **Gravidade:** **Alta** (impede o uso ou a demonstração), **Média** (atrapalha, mas há contorno), **Baixa** (estético ou de texto).

## 4. Critérios de aceite

- Todos os casos de prioridade **Alta** passam.
- Nenhum problema de gravidade **Alta** fica aberto.
- A demonstração foi ensaiada ao menos duas vezes, com o tempo medido.
- A instalação limpa (CT-01) foi feita por quem **não escreveu** o README.

## 5. Perfis de referência

Ordem dos campos: renda / vínculo / meses de vínculo / dívidas / restrição / entrada / objetivo / crédito / prazo.

| Perfil | Valores | Resultado esperado |
| --- | --- | --- |
| **P1** (aprovado claro) | 8000 / Servidor público / 96 / 500 / Não / 40000 / Imóvel / 200000 / 180 | Aprovado, cerca de 98%, origem Modelo |
| **P2** (fronteira) | 4500 / CLT / 36 / 500 / Não / 20000 / Imóvel / 120000 / 120 | Recusado, cerca de 45%, origem Modelo |
| **P3** (restrição) | P1 com restrição **Sim** | Recusado pela política, 0% |
| **P4** (renda baixa) | 1200 / CLT / 36 / 0 / Não / 4000 / Imóvel / 20000 / 60 | Recusado pela política (renda abaixo de R$ 1.500) |
| **P5** (comprometimento alto) | 4500 / CLT / 36 / 500 / Não / 0 / Imóvel / 400000 / 36 | Recusado pela política (comprometimento de 295,1%) |
| **P6** (Veículo) | 6000 / Servidor público / 60 / 400 / Não / 20000 / Veículo / 80000 / 60 | Aprovado, cerca de 95%, origem Modelo |
| **P7** (Serviço) | 5000 / CLT / 48 / 300 / Não / 5000 / Serviço / 20000 / 36 | Aprovado, cerca de 99,5%, origem Modelo |

## 6. Casos de teste

**Prioridade:** A = Alta, M = Média. **Situação:** preencher com OK, FALHOU ou N/A (anotar a data e quem executou).

### 6.1 Instalação, execução e login

| ID | Pri. | O que testar | Passos | Resultado esperado | Situação |
| --- | --- | --- | --- | --- | --- |
| CT-01 | A | Instalação limpa | Em uma pasta nova (de preferência em outro computador), seguir o `README.md`: clonar, criar o ambiente, instalar e rodar | O sistema abre sem erro; a primeira execução cria `consorcio.db` e `modelo_v3_2.joblib` | |
| CT-02 | M | Modo sem login | Deixar `LOGIN_ATIVO = False` e rodar | Entra como "Usuário de demonstração" (`demo@local`) | |
| CT-03 | A | Login Microsoft | Clicar em **Entrar com Microsoft** | Mostra nome e e-mail na barra lateral | |
| CT-04 | A | Logout | Clicar em **Sair** | Volta à tela de entrada; sem login, o formulário não aparece | |
| CT-05 | M | Usuário gravado | Após o login, rodar `python -c "import sqlite3; print(sqlite3.connect('consorcio.db').execute('select email from usuarios').fetchall())"` | O e-mail do login está na lista | |

### 6.2 Meu perfil e validação

| ID | Pri. | O que testar | Passos | Resultado esperado | Situação |
| --- | --- | --- | --- | --- | --- |
| CT-06 | A | Perfil válido | Preencher P1 e clicar em **Avaliar perfil** | "Perfil salvo com sucesso" e quatro indicadores na tela | |
| CT-07 | A | Renda zero | Renda 0 e enviar | Mensagem de erro; nada é gravado | |
| CT-08 | A | Crédito fora dos limites | Crédito 4.000 e depois 700.000 | Erro nos dois casos (limites de 5.000 a 600.000) | |
| CT-09 | A | Entrada maior que o crédito | Crédito 100.000 e entrada 120.000 | Erro; nada é gravado | |
| CT-10 | M | Números negativos | Tentar digitar valor negativo | Os campos não aceitam | |
| CT-11 | M | Memória do formulário | Salvar um perfil e apertar F5 | Os campos voltam preenchidos com o último perfil | |
| CT-12 | A | Erro não altera o salvo | Com um perfil salvo, enviar um inválido e recarregar | O último perfil válido continua o mesmo | |

### 6.3 Decisão e IA

| ID | Pri. | O que testar | Passos | Resultado esperado | Situação |
| --- | --- | --- | --- | --- | --- |
| CT-13 | A | P1 | Avaliar P1 | Aprovado, cerca de 98%, origem Modelo | |
| CT-14 | A | P2 | Avaliar P2 | Recusado, cerca de 45%, origem Modelo | |
| CT-15 | A | P3 | Avaliar P3 | Recusado pela política, 0%, motivo "restrição no nome" | |
| CT-16 | A | P4 | Avaliar P4 | Recusado pela política (renda abaixo do mínimo) | |
| CT-17 | A | P5 | Avaliar P5 | Recusado pela política, comprometimento de 295,1% | |
| CT-18 | M | P6 (Veículo) | Avaliar P6 | Aprovado, com consórcios de Veículo | |
| CT-19 | M | P7 (Serviço) | Avaliar P7 | Aprovado, com consórcios de Serviço | |
| CT-20 | A | Fatores individuais | Avaliar P1; depois mudar só a entrada para 0 | As listas de fatores são **diferentes**, em português simples | |
| CT-21 | A | A política vem antes do modelo | Avaliar qualquer perfil com restrição Sim | A origem é sempre **Política**, nunca Modelo | |
| CT-22 | M | Probabilidade válida | Avaliar P1 a P7 | Probabilidade sempre entre 0% e 100% | |
| CT-23 | A | Métricas do modelo | Rodar `python modelo.py` | Roda sem erro; faixa intermediária com acurácia de 90,3% | |
| CT-24 | M | Reprodutibilidade | A e B rodam `python modelo.py` | As duas obtêm as mesmas métricas | |
| CT-25 | M | Scripts de teste | Rodar `teste_banco.py`, `teste_recomendador.py`, `teste_dados_sinteticos.py` e `teste_decidir.py` | Todos terminam sem erro | |

### 6.4 Resultado

| ID | Pri. | O que testar | Passos | Resultado esperado | Situação |
| --- | --- | --- | --- | --- | --- |
| CT-26 | A | Cartões (aprovado) | Avaliar P1 e abrir **Resultado** | Cartões de Imóvel, em ordem decrescente de aderência, sem aviso de "EXEMPLO" | |
| CT-27 | A | Recusado | Avaliar P2 e abrir **Resultado** | Sem cartões; sugestões de ajuste com valores concretos | |
| CT-28 | A | Recomendações gravadas | Após o CT-26, rodar `python -c "import sqlite3; print(sqlite3.connect('consorcio.db').execute('select count(*) from recomendacoes').fetchone())"`; abrir **Resultado** de novo e repetir | O número é maior que zero e **não aumenta** ao reabrir | |
| CT-29 | M | F5 no Resultado | Apertar F5 na página | O resultado continua (vem do banco) | |
| CT-30 | M | Usuário sem perfil | Entrar com conta sem perfis | Mensagem orientando a preencher o perfil | |

### 6.5 Simulador

| ID | Pri. | O que testar | Passos | Resultado esperado | Situação |
| --- | --- | --- | --- | --- | --- |
| CT-31 | M | Valores iniciais | Salvar P2 e abrir o **Simulador** | Controles começam nos valores do perfil (arredondados) | |
| CT-32 | A | Conta da parcela | Com P2, deixar a entrada em 20% (crédito 120.000, prazo 120) | Parcela de **R$ 920,00** e comprometimento de **31,6%** | |
| CT-33 | A | Recusa por política | Crédito 600.000 e prazo 36 | Recusado pela política, probabilidade 0% | |
| CT-34 | M | Tabela de prazos | Observar a tabela "E se o prazo fosse outro?" | 5 linhas; a parcela diminui quando o prazo aumenta | |
| CT-35 | M | Gráfico | Observar o gráfico de probabilidade por crédito | Eixo vertical de 0 a 100%; curva coerente | |
| CT-36 | A | Não grava | Mexer nos controles e abrir **Meu perfil** e **Resultado** | O perfil salvo continua o original | |
| CT-37 | M | Sugestões e velocidade | Com um cenário recusado, mexer nos controles | A seção "O que tentar para reverter" aparece; a resposta leva até uns 2 segundos | |

### 6.6 Catálogo

| ID | Pri. | O que testar | Passos | Resultado esperado | Situação |
| --- | --- | --- | --- | --- | --- |
| CT-38 | A | Lista e filtro | Abrir **Catálogo** e filtrar por Imóvel | Pelo menos 8 consórcios no total; o filtro mostra só a categoria escolhida | |
| CT-39 | A | Adicionar | Nome "Teste", Imóvel, crédito 100.000, prazo 120 | Mensagem de sucesso; parcela de **R$ 958,33** | |
| CT-40 | A | Validação | Tentar adicionar sem nome, e depois com crédito 0 | Erro nos dois casos; nada é gravado | |
| CT-41 | A | Editar | Mudar o prazo do consórcio de teste para 180 | Parcela de **R$ 638,89** | |
| CT-42 | A | Excluir | Excluir o consórcio de teste | O botão só fica ativo depois de marcar a confirmação; o consórcio some da lista | |
| CT-43 | M | Entra no ranking | Adicionar um consórcio de Imóvel e avaliar P1 | O novo consórcio pode aparecer nas recomendações | |

### 6.7 Acompanhamento

| ID | Pri. | O que testar | Passos | Resultado esperado | Situação |
| --- | --- | --- | --- | --- | --- |
| CT-44 | A | Números corretos | Rodar `python -c "import banco; print(banco.resumo_dashboard())"` e comparar com a página | Os valores são iguais | |
| CT-45 | M | Atualização | Avaliar um novo perfil e clicar em **Atualizar números** | O total de perfis sobe | |
| CT-46 | M | Banco vazio | Com o banco sem perfis | Mensagem informando que não há avaliações | |
| CT-47 | A | Privacidade | Olhar a página inteira | Nenhum e-mail nem dado individual aparece | |

### 6.8 Minha conta

| ID | Pri. | O que testar | Passos | Resultado esperado | Situação |
| --- | --- | --- | --- | --- | --- |
| CT-48 | M | Dados da conta | Abrir **Minha conta** | Mostra nome, e-mail e o último perfil | |
| CT-49 | A | Confirmação | Sem marcar a caixa | O botão **Excluir meus dados** fica desabilitado | |
| CT-50 | A | Exclusão | Marcar a caixa e excluir | A sessão é encerrada; ao entrar de novo, a conta está vazia (**Resultado** e **Minha conta** sem perfil) | |

### 6.9 Persistência, segurança e privacidade

| ID | Pri. | O que testar | Passos | Resultado esperado | Situação |
| --- | --- | --- | --- | --- | --- |
| CT-51 | M | Persistência | Salvar um perfil, parar o sistema e rodar de novo | O perfil continua salvo | |
| CT-52 | M | Banco recriado | Parar o sistema, apagar `consorcio.db` e rodar de novo | O banco é recriado com o catálogo | |
| CT-53 | A | Segredos fora do GitHub | Rodar `git ls-files .streamlit` | Lista **somente** `.streamlit/secrets.toml.example` | |
| CT-54 | A | Repositório privado | Abrir o endereço do repositório em uma janela anônima do navegador | A página não carrega (erro 404) | |
| CT-55 | A | Avisos na tela | Observar o topo de todas as páginas | Aparecem o aviso de dados fictícios e o de e-mail registrado | |

## 7. Divisão da execução

| Pessoa | Executa |
| --- | --- |
| **A** | Seções 6.2, 6.3 (CT-13 a CT-22), 6.4, 6.5, 6.6, 6.8 e CT-02 a CT-05 |
| **B** | Seções 6.7, 6.9, CT-01 (instalação limpa, em outra máquina), CT-23 a CT-25 e a revisão do código da outra pessoa |

Rodada 1: de 26 a 27/11 (registrar problemas e corrigir os de gravidade Alta). Rodada 2: de 27 a 28/11 (repetir os casos que falharam e os de prioridade Alta).

## 8. Roteiro da demonstração ao vivo (cerca de 10 minutos)

| Tempo | O que mostrar |
| --- | --- |
| 0:30 | Abertura: o que é o projeto e o aviso de que tudo é fictício |
| 1:00 | Login com a conta Microsoft; mostrar nome e e-mail |
| 2:00 | Perfil aprovado (P1): decisão, probabilidade, fatores individuais e cartões de recomendação |
| 3:00 | Perfil de fronteira (P2): recusado com cerca de 45%; sugestões de ajuste; no **Simulador**, aumentar a entrada ou o prazo até a decisão virar Aprovado, mostrando a parcela e o gráfico |
| 1:00 | Perfil recusado pela política (P3): motivo claro, sem consultar o modelo |
| 1:00 | **Catálogo** (adicionar ou editar um consórcio) e **Acompanhamento** |
| 0:30 | **Minha conta**: transparência e exclusão de dados |
| 1:00 | Encerramento: limitações (o modelo aprende a fórmula usada nos dados fictícios) e próximos passos |

## 9. Plano B e checklist do dia da demonstração

- [ ] Ensaiar o roteiro completo pelo menos duas vezes, cronometrando.
- [ ] Rodar o sistema uma vez antes de começar (o modelo é treinado na primeira execução).
- [ ] Verificar a internet e o login Microsoft **uma hora antes**.
- [ ] Se o login falhar, mudar para `LOGIN_ATIVO = False` e seguir pelo usuário de demonstração.
- [ ] Ter uma cópia da pasta do projeto em um pendrive.
- [ ] Ter capturas de tela (ou um vídeo curto) de cada etapa do roteiro.
- [ ] Fechar os outros programas e desligar as notificações do computador.
- [ ] Deixar os perfis P1 e P2 anotados à mão.

## 10. Registro de execução

| Rodada | Período | Executado por | Casos OK | Casos que falharam | Problemas abertos |
| --- | --- | --- | --- | --- | --- |
| 1 | 26 a 27/11 | | | | |
| 2 | 27 a 28/11 | | | | |
