# Roteiro de Apresentação — Lab02 (5 min, 3 integrantes)

> Baseado em `reports/relatorio_final.md`. Tempos são cronometrados pra
> ritmo de fala normal (~130-140 palavras/min) — ensaiem pelo menos uma vez
> com cronômetro antes da apresentação real. Se sobrar tempo, é melhor deixar
> pra perguntas do que alongar uma parte.

**Total: 5:00** — Davi 1:40 · Gustavo 1:40 · Lucas 1:30 · Fechamento conjunto 0:10

---

## Davi — Introdução + Metodologia (0:00 – 1:40)

**[0:00 – 0:40] Introdução**

> "Boa tarde. Nosso experimento testa uma pergunta simples: um assistente de
> IA generativa — no nosso caso, o Claude — realmente ajuda a programar mais
> rápido, e isso custa algo em qualidade? A gente mediu três coisas:
> **tempo** até o código passar nos testes, **quantidade de defeitos**, e
> **complexidade/duplicação** do código. Cada um de nós resolveu 6 katas de
> programação, metade com IA habilitada, metade sem, sob um cronômetro de até
> 35 minutos por tarefa."

**[0:40 – 1:40] Metodologia**

> "O desenho é *crossover within-subject*: cada um de nós passou pelos dois
> tratamentos, então dá pra comparar a mesma pessoa com e sem IA, controlando
> diferença de habilidade individual. Os 6 katas — parser de log, sistema de
> reservas, cálculo de troco, validação de senha, achatamento de dicionário e
> agrupamento de anagramas — foram distribuídos numa tabela de
> contrabalanceamento, pra cada kata ser resolvido nos dois tratamentos por
> pessoas diferentes, evitando que alguém resolvesse o mesmo problema duas
> vezes. No total, **18 trials**: 6 katas × 3 integrantes. Cronometragem e
> coleta de métricas foram automatizadas — um script fica de olho nos testes
> a cada 10 segundos e para sozinho quando tudo passa, ou aos 35 minutos."

---

## Gustavo — RQ1 (Tempo) e RQ2 (Defeitos) (1:40 – 3:20)

*[Mostrar Figura 1 — dashboard — e Figura 2 — gráfico pareado por integrante]*

**[1:40 – 2:30] RQ1 — Tempo**

> "A primeira pergunta é se a IA reduz o tempo de resolução. A mediana caiu
> de **11.37 minutos sem IA para 3.17 minutos com IA** — menos de um terço do
> tempo. E não é só a mediana geral: **os três, individualmente, foram mais
> rápidos com IA** — esse gráfico aqui mostra exatamente isso, uma linha por
> pessoa, e as três sobem de Com IA pra Sem IA. O teste estatístico não deu
> significativo — com só 3 pessoas, o Wilcoxon nunca consegue passar de
> p=0.25 — mas a direção é consistente nos três, o que é um sinal forte
> mesmo sem confirmação estatística."

**[2:30 – 3:20] RQ2 — Defeitos**

> "A segunda pergunta é se esse ganho de velocidade custou qualidade
> funcional — código com IA passa menos testes? A resposta, nos nossos
> dados, é não: **100% de taxa de sucesso mediana nos dois tratamentos**.
> Praticamente todo mundo terminou com todos os testes passando, com ou sem
> IA. Também testamos, como contribuição extra, se o código gerado introduz
> **vulnerabilidades de segurança** — rodamos dois scanners diferentes,
> Bandit e Semgrep, e o resultado foi zero vulnerabilidades nos dois
> tratamentos. Não é uma resposta empolgante, mas é honesta: nossos katas são
> funções pequenas e isoladas, sem o tipo de superfície — arquivo, rede,
> banco — onde vulnerabilidade de verdade apareceria."

---

## Lucas — RQ3 (Estrutura) + Discussão + Ameaças (3:20 – 4:50)

*[Mostrar os painéis de Complexidade/MI da Figura 1]*

**[3:20 – 4:00] RQ3 — Estrutura do código**

> "A terceira pergunta é sobre a estrutura do código: complexidade
> ciclomática e duplicação. Também não achamos diferença significativa. Mas
> tem um achado interessante: no kata de parser de log, a solução manual
> usou `if`s encadeados — complexidade 11 — enquanto as duas soluções com IA
> usaram uma expressão regular — complexidade 4 a 5. Pela métrica, o código
> com IA é 'mais simples'. Na prática, a complexidade não sumiu, só migrou
> pra dentro do regex, que essa métrica não enxerga. Isso é uma mudança de
> **estratégia**, não de qualidade."

**[4:00 – 4:50] Discussão e limitações**

> "No geral: a IA claramente acelerou a resolução, sem custo mensurável de
> qualidade funcional ou estrutural nos nossos dados. Mas duas limitações
> importantes: primeiro, com só 3 pessoas o poder estatístico é baixo — não
> dá pra confirmar estatisticamente nada disso, só descrever a direção.
> Segundo, e mais honesto: percebemos depois que dois de nós fizemos todos
> os trials sem IA antes dos com IA — a ordem ficou meio confundida com o
> tratamento, o que pode ter inflado um pouco o ganho de tempo que reportamos.
> Está tudo documentado nas ameaças à validade do relatório."

---

## Fechamento (conjunto, 4:50 – 5:00)

> "O relatório completo, com os 18 trials rastreados como Issues, e o board
> do GitHub Projects, estão linkados no repositório. Obrigado."

---

## Checklist antes de apresentar

- [ ] Ensaiar com cronômetro pelo menos uma vez — cortar, não acelerar a fala, se passar de 5min
- [ ] Abrir `reports/figures/dashboard_tratamentos.png` e
      `reports/figures/rq1_pareado_por_integrante.png` prontos pra mostrar na tela
- [ ] Decidir quem segura o cronômetro/troca de slide durante a fala dos outros
- [ ] Combinar antecipadamente quem responde se a banca perguntar sobre o
      trial censurado por bug (#64, Seção 5.1) ou sobre o resultado nulo de
      segurança — são os pontos mais prováveis de pergunta
