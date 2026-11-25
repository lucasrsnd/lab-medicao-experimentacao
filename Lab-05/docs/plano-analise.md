# Lab05 — Plano de análise

Issue: S01-05 (#185). Responsável: @lucasrsnd. Revisor: @DaviSantos23.

> **Status:** esqueleto independente do software. As partes marcadas com **[pendente]** dependem da escolha do software (#181), das métricas e hipóteses (#182) e do piloto (#184/#186).

O código que implementa este plano está em [`../analysis/`](../analysis/README.md). Quem coleta (#184) entrega os dados no formato da seção 1; a análise roda sem alterar nada.

## 1. Formato dos dados (contrato com a coleta)

CSV em formato longo, uma linha por observação:

| Coluna | Tipo | Significado |
|---|---|---|
| `tratamento` | texto | Condição comparada (ex.: versão, configuração, app × site). |
| `unidade` | texto | O que é medido (consulta, página, tarefa, participante). Igual entre tratamentos quando o desenho é **pareado**. |
| `repeticao` | inteiro | Número da repetição da mesma unidade no mesmo tratamento. |
| `metrica` | texto | Nome da métrica, com unidade no nome (ex.: `tempo_ms`, `tamanho_kb`). |
| `valor` | número | Valor medido. |

Metadados (versão do software, hardware, data, rede) ficam no log da coleta, não neste CSV. A validação (`descritiva.validate`) rejeita colunas ausentes, valores não numéricos e linhas duplicadas.

## 2. Métricas, escalas e estatísticas permitidas

Cada métrica do GQM (#182) entra nesta tabela **[pendente]**:

| Métrica | Entidade / atributo | Direta ou derivada | Escala | Estatísticas permitidas |
|---|---|---|---|---|
| ex.: tempo de resposta (ms) | produto / eficiência (externo) | direta | razão | todas |
| ex.: nota de satisfação (1–5) | recurso / percepção | direta | ordinal | mediana, IQR, testes de postos |
| ex.: houve erro? (sim/não) | produto / confiabilidade | direta | nominal | proporção, qui-quadrado/Fisher |

Regras por escala (Stevens):

| Escala | Tendência central | Dispersão | Testes |
|---|---|---|---|
| Nominal | moda, proporção | — | qui-quadrado, exato de Fisher, McNemar (pareado) |
| Ordinal | mediana | IQR, percentis | Mann-Whitney, Wilcoxon, Kruskal-Wallis, Friedman |
| Intervalar | média, mediana | desvio-padrão, IQR | t, ANOVA (se normal) ou testes de postos |
| Razão | média, mediana, média geométrica | DP, IQR, CV | idem intervalar; razões entre tratamentos fazem sentido |

Métricas de tempo e tamanho costumam ser assimétricas à direita. Por isso a **mediana e o IQR** são reportados sempre, ao lado de média, DP e IC 95%.

## 3. Estatística descritiva

Por métrica e tratamento (`descritiva.summarize`): n, média com IC 95% (t), DP, mediana, Q1, Q3, IQR, mínimo, máximo, CV, outliers pela regra de 1,5·IQR e p-valor de Shapiro-Wilk.

Gráficos: boxplot com os pontos por tratamento; histograma ou densidade quando a forma da distribuição importar; curva de poder × n (seção 6). Todos com título, eixos com unidade e legenda.

Outliers **não são removidos** automaticamente: são investigados (erro de coleta ou comportamento real?) e a decisão é registrada.

## 4. Escolha do teste de hipótese

α = 0,05, bicaudal, salvo justificativa em contrário na hipótese (#182). A escolha segue a árvore abaixo (`testes.compare`, `metodo="auto"`):

| Grupos | Desenho | Normal (Shapiro, p > 0,05) | Não normal |
|---|---|---|---|
| 2 | independente | t de Welch | Mann-Whitney U |
| 2 | pareado | t pareado (sobre as diferenças) | Wilcoxon |
| k > 2 | independente | ANOVA | Kruskal-Wallis |
| k > 2 | pareado | Friedman | Friedman |

- **Pareado ou independente:** pareado quando a mesma unidade é medida em todos os tratamentos (mesma consulta nas duas versões, mesmo participante nas duas condições). Isso remove a variação entre unidades e aumenta o poder.
- **Repetições:** no pareado, as repetições de cada (unidade, tratamento) viram uma mediana antes do teste, para que cada unidade conte uma vez e não haja pseudorreplicação.
- **Welch em vez de t de Student:** não supõe variâncias iguais e perde pouco quando elas são iguais.
- **Normalidade:** com n grande o Shapiro rejeita desvios irrelevantes, e com n pequeno não detecta nada. A decisão é conferida no boxplot/QQ-plot e pode ser forçada (`metodo="parametrico"` ou `"nao_parametrico"`) com justificativa escrita aqui. **[pendente: decisão por métrica após o piloto]**
- **Comparações múltiplas:** com várias métricas (ou pares de tratamentos), os p-valores são corrigidos por Holm-Bonferroni (`p_holm`).
- **Post-hoc (k > 2):** se o teste global rejeitar H0, comparações par a par com o teste de 2 grupos correspondente e correção de Holm.

## 5. Tamanho do efeito

Sempre reportado, com sinal (positivo = primeiro tratamento maior), mesmo quando H0 não é rejeitada:

| Teste | Medida | Desprezível / pequeno / médio / grande |
|---|---|---|
| t de Welch | Hedges g | < 0,2 / < 0,5 / < 0,8 / ≥ 0,8 |
| t pareado | Cohen d_z | idem |
| Mann-Whitney | Cliff δ | < 0,147 / < 0,33 / < 0,474 / ≥ 0,474 (Romano et al., 2006) |
| Wilcoxon | correlação rank-biserial | < 0,1 / < 0,3 / < 0,5 / ≥ 0,5 |
| ANOVA | η² | < 0,01 / < 0,06 / < 0,14 / ≥ 0,14 |
| Kruskal-Wallis | ε² | idem |
| Friedman | Kendall W | < 0,1 / < 0,3 / < 0,5 / ≥ 0,5 |

Para o impacto (seção 5 do enunciado), o efeito também é dado na unidade original, por exemplo diferença de medianas em ms e razão entre medianas ("18% mais rápido"). Um efeito "pequeno" em d pode ser grande em impacto quando multiplicado por milhões de usos, e vice-versa.

## 6. Tamanho da amostra e poder

Reaproveita a simulação de Monte Carlo do Lab04 (`poder.power_by_n`):

1. Ajustar ao piloto uma lognormal (ou normal) por tratamento.
2. No desenho pareado, estimar a correlação entre tratamentos pela mesma unidade (Spearman convertido para a cópula gaussiana).
3. Simular 2.000 conjuntos para cada n e contar as rejeições de cada teste.
4. Escolher o menor n com poder ≥ 80% (`poder.required_n`), com folga para perdas.

Resultado: **[pendente: piloto]** n necessário por métrica = … ; n adotado na S02 = … .

Se o efeito do piloto for muito pequeno, o n necessário pode ser inviável. Nesse caso, a decisão (aumentar repetições, parear o desenho ou reformular a pergunta) é registrada aqui.

## 7. Riscos para a validade de conclusão

- Baixo poder → resultado "não significativo" sem dizer nada (mitigação: seção 6).
- Pescaria de p-valores entre muitas métricas → Holm e hipóteses declaradas antes da coleta (#182).
- Violação de pressupostos → árvore da seção 4 e testes de postos.
- Pseudorreplicação (tratar repetições como unidades independentes) → mediana por unidade no pareado.
- Confiabilidade das medidas (variação do ambiente, rede, cache) → repetições, aquecimento e ordem aleatória no protocolo (#183).
