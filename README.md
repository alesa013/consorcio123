# 123 Consórcio

Protótipo de plataforma de recomendação de consórcios com apoio de inteligência artificial. O usuário entra com a conta Microsoft, informa o próprio perfil financeiro, e o sistema decide **Aprovado** ou **Recusado**, explica a decisão, recomenda consórcios do catálogo e permite simular cenários.

> ⚠️ **Todos os dados e todas as decisões são fictícios.** Isto é uma demonstração acadêmica e **não é análise de crédito real**. Os consórcios do catálogo não são ofertas reais e nada aqui garante contemplação.

## O que o sistema faz

| Funcionalidade | Onde |
| --- | --- |
| Login com conta Microsoft pessoal | `app.py` |
| Cadastro do perfil financeiro (9 campos) com validação | página **Meu perfil** |
| Decisão Aprovado/Recusado com probabilidade, motivo e fatores individuais | página **Resultado** |
| Recomendação de consórcios do catálogo, com justificativa | página **Resultado** |
| Simulação de cenários (crédito, prazo, entrada, dívidas) | página **Simulador** |
| Cadastro de produtos (listar, adicionar, editar, excluir) | página **Catálogo** |
| Indicadores gerais do sistema (sem dados individuais) | página **Acompanhamento** |
| Consulta e exclusão dos próprios dados | página **Minha conta** |

## Como a decisão é tomada

A decisão acontece em **duas camadas** (função `decidir()` em `recomendador.py`).

**Camada 1: política.** Recusa direto, sem consultar o modelo, quando:

- há restrição no nome; ou
- a renda é menor que R$ 1.500; ou
- o comprometimento da renda passa de 40%.

**Camada 2: modelo de IA.** Nos demais casos, decide uma **regressão logística** (scikit-learn), que devolve a probabilidade de aprovação (Aprovado a partir de 50%) e até 3 fatores individuais que mais pesaram naquele perfil.

Indicadores calculados a partir do perfil:

| Indicador | Fórmula |
| --- | --- |
| Parcela estimada | (crédito − entrada) × (1 + taxa administrativa) ÷ prazo |
| Comprometimento | (dívidas mensais + parcela estimada) ÷ renda |
| Entrada | entrada ÷ crédito |
| Crédito sobre renda anual | crédito ÷ (renda × 12) |

A taxa administrativa usada é fictícia (15%).

### Dados de treino e métricas

O modelo é treinado com **10.000 perfis fictícios** gerados por `dados_sinteticos.py` (semente 42, 80% para treino e 20% para teste). Cada perfil recebe um rótulo por uma fórmula de pontuação (comprometimento, estabilidade do vínculo, entrada e crédito sobre renda anual), e 5% dos rótulos são invertidos de propósito, para imitar exceções da vida real. O modelo usa apenas os perfis que a política não recusa.

Resultado no teste, só na **faixa intermediária** (1.171 perfis que a política não recusa e que o modelo decide):

| Medida | Valor |
| --- | --- |
| Acurácia | 90,3% |
| Precisão | 92,0% |
| Revocação | 95,5% |
| Referência (aprovar todos) | 75,7% |

Matriz de confusão (linhas: situação real; colunas: decisão do modelo):

|  | Recusou | Aprovou |
| --- | --- | --- |
| **Era recusado** | 210 | 74 |
| **Era aprovado** | 40 | 847 |

### Limitações

- O modelo aprende **a fórmula usada para rotular os dados fictícios**, e não a realidade do crédito. A acurácia mostra que ele reproduz bem essa regra, e não que avalia crédito de verdade.
- Perfis **perto da fronteira** de aprovação são os mais difíceis: o resultado pode mudar com pequenas variações. A página **Simulador** foi feita para explorar isso.
- Os fatores explicam a decisão do modelo para aquele perfil, mas não são uma justificativa jurídica.
- O catálogo pode ser editado por qualquer usuário logado (não há papéis de administrador).
- O e-mail da conta Microsoft fica registrado no banco de dados. Use dados fictícios no perfil. A página **Minha conta** permite excluir tudo.

## Requisitos

- Windows (testado), com **PowerShell**
- **Python 3.14** (testado na versão 3.14.10)
- **Git**
- Conta Microsoft pessoal, apenas se for usar o login (veja o modo sem login abaixo)

## Instalação

```powershell
git clone https://github.com/alesa013/consorcio123.git
cd consorcio123
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

O repositório é privado: é preciso ter acesso concedido pela dona do projeto.

Se o PowerShell bloquear a ativação do ambiente ("a execução de scripts foi desabilitada"), rode uma vez:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Quando o ambiente estiver ativo, o início da linha do terminal mostra `(.venv)`.

## Como executar

```powershell
python -m streamlit run app.py
```

O navegador abre em `http://localhost:8501`. Para encerrar, aperte **Ctrl + C** no terminal.

Na **primeira execução**, o sistema cria sozinho o banco `consorcio.db`, carrega o catálogo de `consorcios.csv` e treina o modelo (alguns segundos, gerando `modelo_v3_2.joblib`). Esses arquivos ficam só no computador de quem roda e não vão para o GitHub. Para recomeçar do zero, feche o sistema e apague o `consorcio.db`.

### Modo sem login (demonstração)

Para testar sem configurar a Microsoft, abra o `app.py` e deixe no topo:

```python
LOGIN_ATIVO = False
```

O sistema abre direto com o usuário de demonstração `demo@local`. Para voltar ao login, use `LOGIN_ATIVO = True`.

## Configuração do login Microsoft

Só é necessária com `LOGIN_ATIVO = True`.

1. No portal **portal.azure.com**, abra **Microsoft Entra ID**, depois **App registrations** e **New registration**.
2. Escolha o tipo de conta **Personal Microsoft accounts only**.
3. Em **Redirect URI**, escolha a plataforma **Web** e informe `http://localhost:8501/oauth2callback`.
4. Anote o **Application (client) ID** e o **OpenID Connect metadata document** (em **Endpoints**).
5. Em **Certificates & secrets**, crie um **New client secret** e copie o campo **Value** (ele só aparece uma vez).
6. Copie `.streamlit/secrets.toml.example` para `.streamlit/secrets.toml` e preencha:

```toml
[auth]
redirect_uri = "http://localhost:8501/oauth2callback"
cookie_secret = "COLE_AQUI_UM_TEXTO_ALEATORIO_LONGO"

[auth.microsoft]
client_id = "COLE_AQUI_O_APPLICATION_CLIENT_ID"
client_secret = "COLE_AQUI_O_VALUE_DO_SECRET"
server_metadata_url = "https://login.microsoftonline.com/consumers/v2.0/.well-known/openid-configuration"
```

Para gerar o `cookie_secret`:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

> 🔒 **O `secrets.toml` nunca vai para o GitHub** (o `.gitignore` o protege). Não envie o arquivo por e-mail ou mensagem. Se o segredo vazar, apague-o no Azure e crie outro.

## Roteiro de demonstração (perfis de teste)

Preencha na página **Meu perfil** e clique em **Avaliar perfil**:

| # | Renda | Vínculo | Meses | Dívidas | Restrição | Entrada | Objetivo | Crédito | Prazo | Resultado esperado |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 8.000 | Servidor público | 96 | 500 | Não | 40.000 | Imóvel | 200.000 | 180 | **Aprovado**, cerca de 98%, com recomendações |
| 2 | 4.500 | CLT | 36 | 500 | Não | 20.000 | Imóvel | 120.000 | 120 | **Recusado**, cerca de 45% (perfil de fronteira) |
| 3 | igual ao perfil 1 | | | | **Sim** | | | | | **Recusado pela política** (restrição no nome) |
| 4 | 1.200 | CLT | 36 | 0 | Não | 4.000 | Imóvel | 20.000 | 60 | **Recusado pela política** (renda abaixo do mínimo) |
| 5 | 4.500 | CLT | 36 | 500 | Não | 0 | Imóvel | 400.000 | 36 | **Recusado pela política** (comprometimento de 295,1%) |
| 6 | 6.000 | Servidor público | 60 | 400 | Não | 20.000 | Veículo | 80.000 | 60 | **Aprovado**, cerca de 95%, com recomendações de Veículo |
| 7 | 5.000 | CLT | 48 | 300 | Não | 5.000 | Serviço | 20.000 | 36 | **Aprovado**, cerca de 99,5%, com recomendações de Serviço |

**Sugestão de roteiro:**

1. Avalie o perfil 1 e mostre a decisão, os fatores e as recomendações.
2. Avalie o perfil 2 (recusado, na fronteira) e abra o **Simulador**: aumente a entrada ou o prazo e observe a probabilidade mudar.
3. Mostre **Acompanhamento**, **Catálogo** e **Minha conta**.

## Estrutura do projeto

```
consorcio123/
├── app.py                  login Microsoft e navegação entre páginas
├── formatacao.py           formatação de moeda e porcentagem na tela
├── banco.py                banco SQLite (usuários, perfis, catálogo, recomendações)
├── recomendador.py         validação, indicadores, decisão e ranking
├── modelo.py               modelo de IA (treino, métricas e uso)
├── dados_sinteticos.py     geração dos 10.000 perfis fictícios de treino
├── consorcios.csv          catálogo inicial de consórcios fictícios
├── requirements.txt        bibliotecas necessárias
├── paginas/
│   ├── perfil.py           Meu perfil
│   ├── resultado.py        Resultado
│   ├── simulador.py        Simulador
│   ├── catalogo.py         Catálogo
│   ├── acompanhamento.py   Acompanhamento
│   └── conta.py            Minha conta
├── docs/                   documentação técnica
├── teste_*.py              scripts de teste
└── .streamlit/
    └── secrets.toml.example   modelo do arquivo de segredos
```

Gerados localmente e **fora do GitHub**: `consorcio.db`, `modelo_v3_2.joblib`, `dados_treino.csv` e `.streamlit/secrets.toml`.

### Banco de dados (SQLite)

| Tabela | Conteúdo |
| --- | --- |
| `usuarios` | e-mail e nome vindos do login |
| `perfis` | perfil informado, decisão, probabilidade, origem (Política ou Modelo) e motivo |
| `consorcios` | catálogo de produtos |
| `recomendacoes` | consórcios recomendados a cada perfil, com pontuação e justificativa |

## Testes

Cada arquivo `teste_*.py` é um script que imprime os resultados no terminal:

```powershell
python teste_banco.py
python teste_recomendador.py
python teste_dados_sinteticos.py
python teste_decidir.py
```

Para conferir se um arquivo Python está escrito corretamente (não imprime nada se estiver certo):

```powershell
python -m py_compile paginas/simulador.py
```

## Problemas comuns

| Sintoma | O que fazer |
| --- | --- |
| `No module named streamlit` | O ambiente não está ativo: rode `.venv\Scripts\Activate.ps1` |
| `File does not exist: app.py` | Entre na pasta do projeto antes de rodar (`cd consorcio123`) |
| `Port 8501 is already in use` | Feche o outro Streamlit ou use `--server.port 8502` |
| O navegador não abre | Abra `http://localhost:8501` manualmente |
| Erro de login Microsoft | Confira o `.streamlit/secrets.toml` e se o endereço de retorno no Azure é `http://localhost:8501/oauth2callback` |
| A primeira execução demora | É o treino do modelo (alguns segundos); as seguintes são rápidas |
| Quero recomeçar do zero | Feche o sistema e apague o `consorcio.db` |

## Documentação

Veja a pasta `docs/` para o contrato técnico entre as partes do projeto, a comparação entre os modelos de IA e os demais documentos técnicos (arquitetura, modelo de dados, plano de testes e backlog).

## Equipe

- **Esther:** interface (páginas Streamlit), login Microsoft e integração com o banco e o modelo.
- **Alessandra:** dados, banco SQLite, geração dos perfis sintéticos, modelo de IA e regras de recomendação.
