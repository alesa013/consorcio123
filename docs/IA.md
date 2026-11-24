# IA do 123 Consórcio

Documento da Alessandra. Todos os dados são fictícios; este protótipo não é análise de crédito real.

> Rascunho de 24/11. As seções marcadas "a completar" serão escritas até 28/11.

## 1. Como a decisão é tomada

A decisão tem duas camadas:

1. **Política** (origem "Política", probabilidade 0): recusa direto se houver restrição, renda abaixo de R$ 1.500 ou comprometimento da renda acima de 40%.
2. **Modelo** (origem "Modelo"): nos demais casos, uma regressão logística calcula a probabilidade. Aprovado se a probabilidade for maior ou igual a 0,5.

## 2. Variáveis de entrada

A completar.

## 3. Critérios

A completar.

## 4. Dados

- 10.000 perfis sintéticos, gerados com semente fixa (mesmos perfis em qualquer máquina).
- Separação: 80% treino e 20% teste (2.000 perfis de teste).

## 5. Métricas

Modelo oficial v3.2: regressão logística treinada só com perfis que a política não recusa.

| Recorte | Perfis | Acurácia | Precisão | Revocação |
| --- | --- | --- | --- | --- |
| Faixa intermediária (só o modelo) | 1.171 | 90,3% | 92,0% | 95,5% |
| Sistema completo (política + modelo) | 2.000 | 92,2% | 92,0% | 91,1% |

Matriz do sistema completo: [[996, 74], [83, 847]].

## 6. Limitações

- No sistema completo, 43 perfis rotulados como aprovados nos dados sintéticos são recusados pela política. Por isso a revocação do sistema (91,1%) é menor que a do modelo na faixa intermediária (95,5%). A política é regra de negócio e prevalece sobre o rótulo.
- Os dados são sintéticos; os números não representam clientes reais.

## 7. Decisões do modelo

- `class_weight="balanced"` foi testado e não foi adotado.
- Modelo treinado só com perfis que a política não recusa (variante A).