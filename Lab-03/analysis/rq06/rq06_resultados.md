# RQ06 — Métricas DORA por subgrupo

Repositórios: 300. Família de Holm: 12 testes, α = 0.05.

## Fatores e tamanhos dos grupos

- **Linguagem principal:** C++ = 13, Go = 31, Java = 10, JavaScript = 31, Python = 60, Rust = 25, TypeScript = 77, Outras = 51. Agrupadas em "Outras" (< 10): Astro, Blade, C, C#, Crystal, Dart, Fluent, HTML, Jupyter Notebook, Kotlin, Lua, PHP, Ruby, Shell, Swift, Vue.
- **Quartis de estrelas:** Q1 = 75, Q2 = 75, Q3 = 75, Q4 = 75. Cortes (Q1/Q2/Q3): 28455.0 / 35030.0 / 47144.0.
- **Quartis de contribuidores:** Q1 = 76, Q2 = 74, Q3 = 75, Q4 = 75. Cortes (Q1/Q2/Q3): 106.0 / 223.5 / 399.2.

## Testes

| Fator | Métrica | Teste | n | k | estatística | p | p (Holm) | efeito | magnitude |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| Linguagem principal | Frequência (releases/semana) | kruskal-wallis | 298 | 8 | 16.32 | 0.0224 | 0.2236 | ε² = 0.055 | pequeno |
| Linguagem principal | Lead time (a) (horas) | kruskal-wallis | 287 | 8 | 28.37 | 1.88e-04 | 0.0023 * | ε² = 0.099 | médio |
| Linguagem principal | CFR (a) CI | kruskal-wallis | 298 | 8 | 12.21 | 0.0940 | 0.8154 | ε² = 0.041 | pequeno |
| Linguagem principal | Recuperação (horas) | kruskal-wallis | 267 | 8 | 7.09 | 0.4194 | 1.0000 | ε² = 0.027 | pequeno |
| Quartis de estrelas | Frequência (releases/semana) | kruskal-wallis | 300 | 4 | 2.84 | 0.4162 | 1.0000 | ε² = 0.010 | desprezível |
| Quartis de estrelas | Lead time (a) (horas) | kruskal-wallis | 289 | 4 | 0.44 | 0.9313 | 1.0000 | ε² = 0.002 | desprezível |
| Quartis de estrelas | CFR (a) CI | kruskal-wallis | 300 | 4 | 6.48 | 0.0906 | 0.8154 | ε² = 0.022 | pequeno |
| Quartis de estrelas | Recuperação (horas) | kruskal-wallis | 268 | 4 | 2.95 | 0.3997 | 1.0000 | ε² = 0.011 | pequeno |
| Quartis de contribuidores | Frequência (releases/semana) | kruskal-wallis | 300 | 4 | 2.18 | 0.5360 | 1.0000 | ε² = 0.007 | desprezível |
| Quartis de contribuidores | Lead time (a) (horas) | kruskal-wallis | 289 | 4 | 15.35 | 0.0015 | 0.0170 * | ε² = 0.053 | pequeno |
| Quartis de contribuidores | CFR (a) CI | kruskal-wallis | 300 | 4 | 0.34 | 0.9529 | 1.0000 | ε² = 0.001 | desprezível |
| Quartis de contribuidores | Recuperação (horas) | kruskal-wallis | 268 | 4 | 4.56 | 0.2071 | 1.0000 | ε² = 0.017 | pequeno |

\* significativo após Holm (α = 0,05).

## Mediana [Q1–Q3] por grupo

### Linguagem principal

| Métrica | C++ | Go | Java | JavaScript | Python | Rust | TypeScript | Outras |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Frequência (releases/semana) | 0.17 [0.11–0.21] (n=13) | 0.27 [0.21–0.63] (n=31) | 0.19 [0.12–0.35] (n=10) | 0.33 [0.14–0.45] (n=31) | 0.23 [0.13–0.64] (n=60) | 0.19 [0.11–0.46] (n=25) | 0.40 [0.15–0.82] (n=77) | 0.27 [0.12–0.50] (n=51) |
| Lead time (a) (horas) | 1069.87 [583.51–2687.31] (n=12) | 358.72 [68.10–836.40] (n=29) | 729.84 [237.30–13897.21] (n=9) | 233.68 [64.02–738.60] (n=29) | 180.63 [55.62–456.35] (n=60) | 565.11 [75.97–1016.08] (n=23) | 162.75 [36.79–433.47] (n=75) | 427.38 [145.60–891.41] (n=50) |
| CFR (a) CI | 0.04 [0.00–0.08] (n=13) | 0.06 [0.02–0.10] (n=31) | 0.03 [0.02–0.05] (n=10) | 0.02 [0.00–0.08] (n=31) | 0.04 [0.01–0.18] (n=60) | 0.06 [0.01–0.14] (n=25) | 0.06 [0.04–0.15] (n=77) | 0.06 [0.03–0.13] (n=51) |
| Recuperação (horas) | 8.32 [3.43–27.99] (n=10) | 3.14 [0.94–10.30] (n=31) | 6.11 [1.39–19.83] (n=8) | 2.08 [0.66–17.23] (n=24) | 2.73 [0.62–18.70] (n=50) | 6.92 [1.36–19.21] (n=23) | 3.57 [0.87–20.62] (n=73) | 9.70 [1.09–23.79] (n=48) |

### Quartis de estrelas

| Métrica | Q1 | Q2 | Q3 | Q4 |
|---|---:|---:|---:|---:|
| Frequência (releases/semana) | 0.25 [0.14–0.47] (n=75) | 0.33 [0.17–0.66] (n=75) | 0.25 [0.14–0.50] (n=75) | 0.27 [0.13–0.66] (n=75) |
| Lead time (a) (horas) | 288.27 [61.37–898.26] (n=75) | 253.53 [71.83–743.55] (n=75) | 248.14 [106.37–738.23] (n=70) | 219.61 [64.05–683.03] (n=69) |
| CFR (a) CI | 0.06 [0.03–0.19] (n=75) | 0.06 [0.02–0.18] (n=75) | 0.05 [0.01–0.14] (n=75) | 0.04 [0.02–0.11] (n=75) |
| Recuperação (horas) | 6.10 [0.76–23.24] (n=70) | 4.72 [0.75–23.04] (n=68) | 2.41 [0.87–10.16] (n=64) | 5.66 [0.97–29.57] (n=66) |

### Quartis de contribuidores

| Métrica | Q1 | Q2 | Q3 | Q4 |
|---|---:|---:|---:|---:|
| Frequência (releases/semana) | 0.27 [0.15–0.57] (n=76) | 0.31 [0.20–0.64] (n=74) | 0.23 [0.14–0.47] (n=75) | 0.33 [0.13–0.55] (n=75) |
| Lead time (a) (horas) | 141.84 [50.43–442.68] (n=75) | 156.86 [49.07–756.46] (n=73) | 416.38 [143.23–770.47] (n=72) | 403.44 [162.75–1238.43] (n=69) |
| CFR (a) CI | 0.06 [0.03–0.11] (n=76) | 0.05 [0.01–0.13] (n=74) | 0.05 [0.02–0.16] (n=75) | 0.05 [0.02–0.16] (n=75) |
| Recuperação (horas) | 4.45 [0.88–23.15] (n=70) | 2.81 [0.55–13.04] (n=66) | 4.53 [1.17–22.28] (n=66) | 6.71 [1.11–27.84] (n=66) |
