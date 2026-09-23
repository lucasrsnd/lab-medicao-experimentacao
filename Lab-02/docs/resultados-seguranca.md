# Resultados — Análise extra: Vulnerabilidades de segurança (Bandit)

> Dono: Gustavo. Contribuição extra do grupo (não é uma das RQ1-RQ3 fixas do
> enunciado) — mesma linha do que o Lab-01 do grupo fez com frentes de
> contribuição própria além do pedido.
>
> Fonte: `data/raw/trials_seguranca.csv`, gerado por
> `src/security/bandit_scan.py` a partir dos 18 `solution.py` (mesmo
> critério de exclusão de `test_*.py`/`conftest.py` de
> `src/metrics/static_metrics.py`). Números em
> `reports/analysis/rq_extra_seguranca.{md,json}`.

## Pergunta

O uso de assistente de IA altera a quantidade de vulnerabilidades de
segurança introduzidas no código produzido — a IA introduz mais, menos, ou
a mesma quantidade que o desenvolvimento manual?

## Ferramenta

**Bandit** (`pip install bandit`), o scanner de segurança estático padrão
para Python — mesma categoria do Radon/jscpd já usados na RQ3 (estático,
sem depender de API externa nem de execução do código, reprodutível). Roda
por AST, procurando por padrões conhecidos: uso de `eval`/`exec`, injeção
de comando/SQL, criptografia fraca, deserialização insegura, segredos
hardcoded, etc. (lista completa de checks em
[bandit.readthedocs.io](https://bandit.readthedocs.io)).

## Resultado

**Zero vulnerabilidades encontradas, nos dois tratamentos, nos 18 trials.**
Mediana e IQR são 0 em Com IA e em Sem IA; o Wilcoxon pareado por integrante
(N=3) não tem o que detectar (todas as diferenças são zero), e retorna
p=1.0 — um resultado nulo, não uma prova estatística de equivalência.

| Tratamento | N | Mediana | IQR |
|---|---|---|---|
| Com IA | 9 | 0.00 | 0.00 |
| Sem IA | 9 | 0.00 | 0.00 |

## Por que isso é o resultado esperado (e não um scanner quebrado)

Antes de aceitar o zero como resultado, `tests/test_bandit_scan.py` inclui
um **controle positivo**: um arquivo com `eval()` deliberado, que o Bandit
detecta corretamente. Isso descarta a hipótese de o scanner estar mal
configurado ou não estar rodando de verdade.

O motivo do zero é o formato da tarefa, não a ferramenta: os 6 katas são
funções puras e pequenas (6 a 29 SLOC — ver RQ3), sem nenhuma das
superfícies que o Bandit cobre — sem I/O de arquivo, sem rede, sem
subprocess/shell, sem SQL, sem criptografia, sem desserialização, sem
segredos. `eval`/`exec` também não fazem sentido para nenhum dos 6
problemas (parsing de log, conflito de reservas, troco, validação de senha,
achatamento de dicionário, agrupamento de anagramas). Não há, estruturalmente,
onde uma vulnerabilidade do tipo que o Bandit procura poderia aparecer nesta
amostra.

## O que isso significa para a pergunta original

**Não dá para responder "a IA introduz mais ou menos vulnerabilidades" com
estes dados** — não porque a resposta seja "não introduz", mas porque a
tarefa escolhida (katas algorítmicos isolados, sem I/O) não é o tipo de
código onde esse risco se manifesta. Isso é, em si, um achado válido sobre
os limites do desenho experimental: análise de vulnerabilidade de segurança
exige tarefas com superfície de ataque real (parsing de entrada não
confiável, acesso a arquivo/rede/banco, autenticação, serialização) — nenhum
dos 6 katas tem isso por construção (foram escolhidos para serem pequenos,
autorais e de baixa indexação, não para cobrir padrões de segurança).

## Trabalhos futuros

Para uma análise de vulnerabilidade introduzida por IA ser informativa,
seria preciso katas/tarefas com superfície de ataque real — ex.: parsing de
entrada de usuário sem sanitização, construção de queries, manipulação de
arquivos com paths vindos de fora, chamadas de rede. Nenhuma dessas classes
de problema esteve nos 6 katas usados neste experimento.
