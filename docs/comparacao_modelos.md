# Comparação de modelos: árvore x regressão logística

Gerado em 21/11/2026.

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

