# Comparação de modelos: árvore x regressão logística

Gerado em 22/11/2026.

## Todos os perfis do teste (2000 perfis)

| Medida | Árvore | Regressão logística |
|---|---|---|
| acuracia | 90.8% | 90.1% |
| precisao | 89.6% | 88.5% |
| revocacao | 90.8% | 90.5% |

Matriz da árvore: [[972, 98], [86, 844]]
Matriz da logística: [[961, 109], [88, 842]]
Referência: chutar 'Aprovado' para todos acertaria 46.5%.

## Faixa intermediária (política não recusa) (1171 perfis)

| Medida | Árvore | Regressão logística |
|---|---|---|
| acuracia | 87.9% | 89.2% |
| precisao | 89.6% | 91.3% |
| revocacao | 95.0% | 94.8% |

Matriz da árvore: [[186, 98], [44, 843]]
Matriz da logística: [[204, 80], [46, 841]]
Referência: chutar 'Aprovado' para todos acertaria 75.7%.

## Experimentos do contrato v3.2 (faixa intermediária)

| Variante | Acurácia | Precisão | Revocação | Brier |
|---|---|---|---|---|
| Atual (treina com todos) | 89.2% | 91.3% | 94.8% | 0.101 |
| A) só perfis fora da política | 90.3% | 92.0% | 95.5% | 0.088 |
| B) class_weight balanced | 88.9% | 89.9% | 96.2% | 0.099 |
| A+B) os dois | 82.1% | 94.6% | 80.9% | 0.124 |

Brier: quanto menor, mais perto da realidade ficaram as chances previstas.

Matriz de Atual (treina com todos): [[204, 80], [46, 841]]
Matriz de A) só perfis fora da política: [[210, 74], [40, 847]]
Matriz de B) class_weight balanced: [[188, 96], [34, 853]]
Matriz de A+B) os dois: [[243, 41], [169, 718]]

