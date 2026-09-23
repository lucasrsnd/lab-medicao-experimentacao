# Resultados: RQ3 (Complexidade ciclomática e duplicação)

> Dono: Lucas, Issue [S03] #72 (RQ3: complexidade ciclomática e duplicação).
> Complementa `docs/resultados-rq1-rq2.md` (Gustavo) na seção "Resultados por
> RQ" do relatório final.
>
> Fonte dos números: `reports/analysis/rq3_estrutura.{md,json}`, gerados por
> `src/analysis/rq3_estrutura.py` a partir de `data/raw/trials_metricas.csv`
> (18 trials, 6 katas × 3 integrantes, coletados com
> `src/metrics/static_metrics.py`: Radon cc/raw/mi + jscpd, ignorando
> `test_*.py`/`conftest.py`). As métricas do CSV foram conferidas contra o
> código atual de `katas/` (Radon recalculado nos 18 trials, 0 divergências).

## RQ3: O uso de assistente de IA altera a complexidade ciclomática ou a duplicação do código produzido?

### Métricas escolhidas

| Métrica | Ferramenta | Papel |
|---|---|---|
| Complexidade ciclomática média por função | Radon `cc` | primária |
| % de linhas duplicadas | jscpd (mín. 3 linhas / 20 tokens) | primária |
| SLOC | Radon `raw` | controle (obrigatória pelo enunciado) |
| CC por 10 SLOC | derivada (`complexidade_total / sloc * 10`) | complexidade normalizada por LOC |
| Índice de Manutenibilidade | Radon `mi` | aprofundamento (opcional) |

A CC normalizada por LOC entrou porque a CC "crua" mistura dois efeitos: o
código ser mais complexo e o código ser maior. Todas as soluções têm uma única
função (`num_blocos = 1` nos 18 trials), então a "CC média por função" é, na
prática, a CC da solução.

### Pareamento

Seguindo a RQ1/RQ2, o Wilcoxon principal pareia **por integrante** (mediana dos
3 trials Com IA contra a dos 3 Sem IA da mesma pessoa, N=3). Na RQ3 foi
acrescentado um Wilcoxon complementar **por kata** (N=6): a estrutura do código
depende muito do problema (o K1, parser de log, tem CC bem acima dos demais), e
todo kata foi resolvido nos dois tratamentos por integrantes diferentes (ver
`katas/README.md`). Parear por kata controla a dificuldade do problema, e
parear por integrante controla a habilidade individual. Nenhum dos dois
controla ambos, por isso os dois são reportados.

### Resultados (todos os 18 trials)

| Métrica | Mediana Com IA (IQR) | Mediana Sem IA (IQR) | p (por integrante, N=3) | p (por kata, N=6) |
|---|---|---|---|---|
| CC média por função | 5.00 (2.00) | 4.00 (5.00) | 1.00 | 1.00 |
| Duplicação (%) | 0.00 (0.00) | 0.00 (0.00) | n/a ¹ | n/a ¹ |
| SLOC | 14.00 (5.00) | 11.00 (4.00) | 0.50 | 0.56 |
| CC por 10 SLOC | 4.29 (1.11) | 4.00 (1.25) | 1.00 | 0.84 |
| MI | 66.45 (13.66) | 75.16 (35.14) | 0.75 | 0.44 |

¹ Duplicação zero em todos os trials: todas as diferenças pareadas são zero, e
o teste não é informativo (o scipy devolve p = 1.0).

**Complexidade.** A mediana da CC foi 5 com IA e 4 sem IA, mas a diferença não
é consistente. Por kata, a CC com IA foi menor no K1 (4.5 contra 11) e no K5,
maior no K2 e no K3, e igual no K4 e no K6. Nenhum teste chega perto de
significância (p ≥ 0.84 na CC normalizada). O caso extremo, K1 Sem IA (CC 11,
29 SLOC), é uma solução manual por `split`/`if` encadeados. As duas soluções
com IA do K1 usaram uma expressão regular, que "esconde" a complexidade dentro
do padrão (CC 4 a 5). Isso é uma diferença de *estratégia* de solução, não de
qualidade, e a CC não captura a complexidade do regex.

**Duplicação.** Nenhum trial teve linha duplicada internamente (0% nos 18).
Com soluções de 6 a 29 SLOC em uma função só, não há espaço para clones com o
limiar do jscpd (3 linhas / 20 tokens). Como checagem, o jscpd rodado sobre
**todos** os katas juntos encontrou um único clone entre trials: o laço de
"3 caracteres repetidos em sequência" do K4, idêntico entre Lucas (Com IA) e
Davi (Sem IA). É convergência natural para a mesma solução idiomática, não
cópia, e não é duplicação no sentido da RQ3.

**LOC (controle).** O código Com IA foi um pouco mais longo (mediana 14 contra
11 SLOC, com 2 dos 3 integrantes escrevendo mais linhas com IA), coerente com a
ressalva do enunciado de que código de IA tende a ser mais verboso. A diferença
também não é significativa. Normalizando a CC por LOC, os tratamentos ficam
praticamente iguais (4.29 contra 4.00 CC/10 SLOC).

**Manutenibilidade.** O MI mediano foi menor com IA (66 contra 75), mas o MI do
Radon satura em 100 em arquivos muito pequenos (4 trials têm MI = 100). Com
arquivos deste tamanho a métrica é pouco discriminante, e a diferença não é
significativa (p ≥ 0.44).

**Resposta à RQ3.** Nesta amostra, **não há evidência de que o assistente de IA
altere a complexidade ciclomática ou a duplicação** do código produzido. As
medianas são próximas, as direções variam entre katas e integrantes, e nenhum
Wilcoxon se aproxima de 0.05. Isso não rejeita H0 para a RQ3. Com N=3/N=6, a
ausência de significância também não prova equivalência: o poder estatístico é
baixo demais para detectar efeitos pequenos.

### Cenário excluindo o outlier de instrumentação (Davi, K2 Sem IA)

Esse trial foi censurado por um bug de infraestrutura do pytest (ver
`docs/resultados-rq1-rq2.md`), mas o código dele é válido e as métricas
estáticas não dependem do resultado dos testes. Excluí-lo praticamente não muda
a RQ3: a mediana da CC Sem IA segue em 4.0, o SLOC em 11, a CC/10 SLOC fica em
4.22 e o MI em 78.85. Nenhum p-valor
fica abaixo de 0.43 (o menor é 0.4375). A conclusão é a mesma nos dois cenários.
