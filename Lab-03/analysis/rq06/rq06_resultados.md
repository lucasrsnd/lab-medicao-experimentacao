# RQ06 — Métricas DORA por subgrupo

Repositórios: 183. Família de Holm: 12 testes, α = 0.05.

## Fatores e tamanhos dos grupos

- **Linguagem principal:** Go = 21, JavaScript = 19, Python = 41, Rust = 19, TypeScript = 43, Outras = 40. Agrupadas em "Outras" (< 10): Astro, Blade, C, C#, C++, Fluent, HTML, Java, Kotlin, PHP, Ruby, Shell, Swift.
- **Quartis de estrelas:** Q1 = 46, Q2 = 46, Q3 = 45, Q4 = 46. Cortes (Q1/Q2/Q3): 36884.5 / 44108.0 / 64203.0.
- **Quartis de contribuidores:** Q1 = 46, Q2 = 46, Q3 = 45, Q4 = 46. Cortes (Q1/Q2/Q3): 126.5 / 244.0 / 465.5.

## Testes

| Fator | Métrica | Teste | n | k | estatística | p | p (Holm) | efeito | magnitude |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| Linguagem principal | Frequência (releases/semana) | kruskal-wallis | 183 | 6 | 6.82 | 0.2346 | 1.0000 | ε² = 0.037 | pequeno |
| Linguagem principal | Lead time (a) (horas) | kruskal-wallis | 172 | 6 | 10.45 | 0.0634 | 0.6972 | ε² = 0.061 | pequeno |
| Linguagem principal | CFR (a) CI | kruskal-wallis | 183 | 6 | 5.46 | 0.3619 | 1.0000 | ε² = 0.030 | pequeno |
| Linguagem principal | Recuperação (horas) | kruskal-wallis | 158 | 6 | 5.87 | 0.3188 | 1.0000 | ε² = 0.037 | pequeno |
| Quartis de estrelas | Frequência (releases/semana) | kruskal-wallis | 183 | 4 | 1.03 | 0.7940 | 1.0000 | ε² = 0.006 | desprezível |
| Quartis de estrelas | Lead time (a) (horas) | kruskal-wallis | 172 | 4 | 2.23 | 0.5265 | 1.0000 | ε² = 0.013 | pequeno |
| Quartis de estrelas | CFR (a) CI | kruskal-wallis | 183 | 4 | 0.12 | 0.9887 | 1.0000 | ε² = 0.001 | desprezível |
| Quartis de estrelas | Recuperação (horas) | kruskal-wallis | 158 | 4 | 6.33 | 0.0966 | 0.9663 | ε² = 0.040 | pequeno |
| Quartis de contribuidores | Frequência (releases/semana) | kruskal-wallis | 183 | 4 | 2.75 | 0.4312 | 1.0000 | ε² = 0.015 | pequeno |
| Quartis de contribuidores | Lead time (a) (horas) | kruskal-wallis | 172 | 4 | 13.03 | 0.0046 | 0.0548 | ε² = 0.076 | pequeno |
| Quartis de contribuidores | CFR (a) CI | kruskal-wallis | 183 | 4 | 2.61 | 0.4552 | 1.0000 | ε² = 0.014 | pequeno |
| Quartis de contribuidores | Recuperação (horas) | kruskal-wallis | 158 | 4 | 3.87 | 0.2755 | 1.0000 | ε² = 0.025 | pequeno |

\* significativo após Holm (α = 0,05).

## Mediana [Q1–Q3] por grupo

### Linguagem principal

| Métrica | Go | JavaScript | Python | Rust | TypeScript | Outras |
|---|---:|---:|---:|---:|---:|---:|
| Frequência (releases/semana) | 0.25 [0.21–0.84] (n=21) | 0.27 [0.11–0.39] (n=19) | 0.21 [0.13–0.63] (n=41) | 0.19 [0.11–0.40] (n=19) | 0.34 [0.15–0.76] (n=43) | 0.19 [0.11–0.43] (n=40) |
| Lead time (a) (horas) | 441.33 [59.24–745.11] (n=19) | 374.07 [171.58–1001.88] (n=17) | 196.08 [76.06–458.40] (n=41) | 591.64 [174.29–933.57] (n=17) | 218.94 [57.52–403.44] (n=41) | 314.12 [155.58–1675.87] (n=37) |
| CFR (a) CI | 0.07 [0.01–0.10] (n=21) | 0.02 [0.00–0.06] (n=19) | 0.04 [0.02–0.16] (n=41) | 0.07 [0.01–0.12] (n=19) | 0.05 [0.02–0.13] (n=43) | 0.04 [0.01–0.13] (n=40) |
| Recuperação (horas) | 1.44 [0.72–7.10] (n=21) | 2.60 [1.43–30.66] (n=13) | 2.73 [0.76–18.70] (n=34) | 8.20 [2.58–17.82] (n=17) | 2.25 [0.72–9.47] (n=39) | 6.95 [1.09–17.90] (n=34) |

### Quartis de estrelas

| Métrica | Q1 | Q2 | Q3 | Q4 |
|---|---:|---:|---:|---:|
| Frequência (releases/semana) | 0.21 [0.13–0.38] (n=46) | 0.28 [0.15–0.50] (n=46) | 0.29 [0.11–0.63] (n=45) | 0.27 [0.15–0.66] (n=46) |
| Lead time (a) (horas) | 470.17 [144.08–830.06] (n=46) | 233.45 [68.10–591.64] (n=41) | 245.67 [108.55–624.07] (n=43) | 182.59 [66.54–814.32] (n=42) |
| CFR (a) CI | 0.05 [0.01–0.13] (n=46) | 0.05 [0.01–0.13] (n=46) | 0.05 [0.01–0.13] (n=45) | 0.04 [0.02–0.10] (n=46) |
| Recuperação (horas) | 2.91 [0.73–20.03] (n=40) | 1.98 [0.89–8.26] (n=40) | 3.09 [0.69–9.51] (n=38) | 7.92 [1.72–35.14] (n=40) |

### Quartis de contribuidores

| Métrica | Q1 | Q2 | Q3 | Q4 |
|---|---:|---:|---:|---:|
| Frequência (releases/semana) | 0.33 [0.15–0.62] (n=46) | 0.25 [0.19–0.58] (n=46) | 0.21 [0.13–0.50] (n=45) | 0.24 [0.12–0.54] (n=46) |
| Lead time (a) (horas) | 130.97 [41.22–339.91] (n=45) | 314.12 [70.32–741.03] (n=45) | 442.82 [167.63–1033.02] (n=42) | 288.70 [167.09–1108.67] (n=40) |
| CFR (a) CI | 0.05 [0.02–0.11] (n=46) | 0.06 [0.01–0.11] (n=46) | 0.03 [0.01–0.14] (n=45) | 0.05 [0.02–0.14] (n=46) |
| Recuperação (horas) | 3.01 [0.83–22.46] (n=41) | 2.38 [0.65–10.13] (n=40) | 3.73 [1.08–21.11] (n=36) | 5.99 [1.11–22.74] (n=41) |
