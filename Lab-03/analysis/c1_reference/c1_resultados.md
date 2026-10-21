# Classificação DORA de referência C1

Base: 300 repositórios. SHA-256 do CSV-base: `f0633cb8aacb95925661d9b4f4e455afe20d40ab5e5f46c390791d0585b080e1`.
O classificador de `lab03.metrics.classification` foi aplicado sem alterar os cortes; a mediana das quatro pontuações é arredondada para baixo. A categoria geral recalculada foi conferida contra `categoria_geral_c1`.

| Métrica | Elite | High | Medium | Low | Não classificável |
|---|---:|---:|---:|---:|---:|
| Frequência | 0 | 34 | 130 | 136 | 0 |
| Lead time (a) | 42 | 72 | 98 | 77 | 11 |
| CFR (a) | 230 | 40 | 17 | 13 | 0 |
| Recuperação | 77 | 135 | 40 | 16 | 32 |
| Geral | 17 | 89 | 130 | 24 | 40 |

## Regras de fronteira

A implementação reutilizada e os limites verificados por teste são: frequência ≥7/semana (Elite), ≥1 (High), ≥12/52 (Medium); lead time <24 h, <168 h, <720 h; CFR ≤15%, ≤30%, ≤45%; recuperação <1 h, <24 h, <168 h. Cada limite pertence à categoria mais alta indicada; o valor exatamente no próximo limite cai na faixa seguinte.

Valores ausentes ou com denominador zero permanecem não classificáveis. A categoria geral só é emitida quando as quatro métricas têm denominador positivo e valor observado.
