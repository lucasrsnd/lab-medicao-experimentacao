# Classificação DORA de referência C1

Base: 183 repositórios. SHA-256 do CSV-base: `cbfde52fa148c45acdbbd5425a1aa8fd7f7eaf22d7964c28b3c6bded8d41ee55`.
O classificador de `lab03.metrics.classification` foi aplicado sem alterar os cortes; a mediana das quatro pontuações é arredondada para baixo. A categoria geral recalculada foi conferida contra `categoria_geral_c1`.

| Métrica | Elite | High | Medium | Low | Não classificável |
|---|---:|---:|---:|---:|---:|
| Frequência | 0 | 19 | 73 | 91 | 0 |
| Lead time (a) | 20 | 44 | 61 | 47 | 11 |
| CFR (a) | 148 | 23 | 6 | 6 | 0 |
| Recuperação | 47 | 80 | 25 | 6 | 25 |
| Geral | 12 | 54 | 68 | 16 | 33 |

## Regras de fronteira

A implementação reutilizada e os limites verificados por teste são: frequência ≥7/semana (Elite), ≥1 (High), ≥12/52 (Medium); lead time <24 h, <168 h, <720 h; CFR ≤15%, ≤30%, ≤45%; recuperação <1 h, <24 h, <168 h. Cada limite pertence à categoria mais alta indicada; o valor exatamente no próximo limite cai na faixa seguinte.

Valores ausentes ou com denominador zero permanecem não classificáveis. A categoria geral só é emitida quando as quatro métricas têm denominador positivo e valor observado.
