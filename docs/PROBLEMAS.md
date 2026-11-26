# Registro de problemas e melhorias

Gravidade: Alta (impede o uso ou a demonstração), Média (atrapalha), Baixa (estético).

## Problemas

| # | Data | Quem achou | Página | Perfil usado | O que esperava | O que aconteceu | Gravidade | Situação |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 22/11 | A | (exemplo) Simulador | Perfil 2 | Gráfico de 0 a 100% | Eixo mostrava valores negativos | Baixa | Resolvido |
| 2 | 24/11 | Alessandra | recomendador.py e dados_sinteticos.py | (não se aplica) | Regra da política escrita em um só lugar | A mesma regra existe em decidir() e em recusado_pela_politica(). Hoje as duas batem, mas se uma mudar e a outra não, o sistema e a métrica passam a divergir | Baixa | Mitigado (coberto por teste_consistencia_politica.py) |

## Melhorias sugeridas

| # | Data | Sugestão | Quem propôs | Situação |
| --- | --- | --- | --- | --- |
| 1 | 22/11 | Ordenar as barras do Acompanhamento na mesma ordem da tabela | A | Aberta |
| 2 | 24/11 | Fazer decidir() e a métrica usarem uma única função para a regra da política | Alessandra | Aberta |
| 3 | 26/11 | Rodar o CT-24 na máquina da A (Python 3.14.10) e comparar as métricas com as da B (Python 3.13) | B | Aberta |

---

## Rodada 1 de testes 


Verificado em 24/11 pelo teste_consistencia_politica.py: as duas versões da regra da política (decidir() e recusado_pela_politica()) concordaram em 2000 perfis novos e em 6 casos de fronteira, com 0 divergências. Refatorar para uma só versão fica como melhoria futura (gravidade Baixa).

| Quem | O que foi executado | Resultado |
| --- | --- | --- |
| A | Casos de prioridade Alta da parte da A (login, perfil e validação, decisão, resultado, simulador, catálogo e minha conta) | Todos passaram. Nenhum problema novo. |
| A | `python teste_revisao.py` (código da B contra o contrato v3.3) | [58] de [58] verificações OK, nenhuma divergência |
| A | `python teste_consistencia_politica.py` (as duas versões da regra da política) | 0 divergências em [2000] perfis novos e nos 6 casos de fronteira |
| B | Parte da B (6.7, 6.9, CT-23 a CT-25 e CT-01) | A executar em 25/11 |

Problemas abertos de gravidade Alta ou Média: **0**.

### Comportamentos conhecidos (não são defeitos)

- Os 4 perfis de demonstração criados pelo `banco.py` entram nos números da página **Acompanhamento** (por isso o CT-46, "banco vazio", ficou N/A).
- Se todos os consórcios forem apagados pela página **Catálogo**, o `iniciar_banco()` recarrega o `consorcios.csv` na próxima abertura.
- Perfis na fronteira de aprovação (como o P2, cerca de 45%) mudam de resultado com pequenas variações. É uma limitação do modelo, descrita no README.
- Os fatores mostram até 3 pontos que mais pesaram naquela decisão; não são uma justificativa jurídica.
- Não há papéis de administrador: qualquer usuário logado edita o catálogo.

### Melhorias futuras (gravidade Baixa)

- Unificar a regra da política em uma só função. Hoje ela existe em `decidir()` e em `recusado_pela_politica()`; as duas foram verificadas como equivalentes em 24/11 (ver problema 2 e melhoria 2).
- No gráfico do **Acompanhamento**, as barras aparecem em ordem alfabética (Imóvel, Serviço, Veículo), diferente da tabela logo abaixo.
- Controle de papéis (administrador) para a edição do catálogo.