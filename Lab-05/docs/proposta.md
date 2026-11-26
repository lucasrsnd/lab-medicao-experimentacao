# Lab05 — Proposta de pesquisa (versão inicial)

Issue: S01-02 (#182). Responsável: @DaviSantos23. Revisor: @gustavoprehl.

> **Status:** proposta inicial baseada na escolha confirmada de WordPress em [software.md](./software.md). O solicitante confirmou em 25/11/2026 que nenhum outro grupo selecionou o software. `docs/protocolo-coleta.md` (issue #183) ainda não está disponível; ambiente, implementação do cache, carga, aquecimento e tamanho da amostra serão fixados nele após o piloto. A escala e os testes seguem o [plano de análise](./plano-analise.md).

## Pergunta de pesquisa e caminho

**Pergunta:** Em uma instalação de teste do WordPress 7.1.5 com conteúdo fixo, qual é o efeito de habilitar o cache de página completa, comparado a mantê-lo desligado, sobre a latência das respostas HTTP?

**Caminho escolhido:** experimento controlado com uma instância isolada, contextualizado por dados públicos de adoção do WordPress. O experimento não acessará sites de produção nem usará dados de usuários reais.

## Objetivo GQM

**Analisar** o efeito de habilitar cache de página completa, **com o propósito de avaliar** a mudança de desempenho observável, **com respeito à** latência HTTP, **do ponto de vista de** quem opera ou mantém um site WordPress, **no contexto de** uma instalação de teste WordPress 7.1.5 com conteúdo e ambiente controlados.

| Pergunta GQM | Métrica |
|---|---|
| Q1. Como a latência de resposta muda entre cache desligado e ligado? | M1. Latência HTTP observada pelo cliente, em milissegundos por requisição. |

## Classificação das métricas

| Métrica | Entidade | Atributo | Medida | Escala | Pode ser “jogada”? |
|---|---|---|---|---|---|
| Latência HTTP (ms) | Produto (instância WordPress e página servida) | Desempenho percebido externamente | Direta, cronometrada pelo cliente HTTP | Razão | Sim. Por exemplo, desconsiderando requisições lentas, alterando o conteúdo entre condições ou medindo somente após aquecimento desigual. Mitigação: conteúdo fixo, inclusão de todas as medições planejadas e aquecimento documentado e igual. |

Códigos HTTP serão registrados para verificar se uma execução é válida e diagnosticar falhas, mas a proporção de erros não será uma métrica de hipótese: o analisador previsto no plano atual não implementa testes para proporções binárias.

## Hipóteses, variáveis e desenho

Para a métrica primária, a comparação será bicaudal, em linha com o plano de análise:

- **M1 — latência:** H0: a diferença de latência entre as condições é nula; H1: há diferença.
- **Variável independente:** estado do cache de página completa (desligado ou ligado).
- **Variável dependente:** latência HTTP.
- **Objeto:** uma instalação isolada de WordPress 7.1.5, com uma página e conteúdo de teste fixos.
- **Sujeitos/unidades observacionais:** blocos de requisições HTTP geradas por cliente de teste para o mesmo endpoint; cada linha do CSV corresponde a uma requisição e sua repetição dentro do bloco. Não há participantes humanos.
- **Desenho:** experimento controlado, pareado por endpoint e bloco. Cada bloco será medido sob as duas condições, com os mesmos recursos e parâmetros do ambiente; a ordem será alternada ou randomizada. Aquecimento, implementação e limpeza/invalidação do cache, concorrência e critérios de validade da execução serão especificados no protocolo.
- **Amostra e análise:** definidas após o piloto, conforme o [plano de análise](./plano-analise.md). Quando o pareamento e a escala permitirem, cada unidade será comparada nas duas condições; não se tratarão repetições da mesma unidade como unidades independentes. Serão reportados tamanho do efeito e intervalo de confiança, além do p-valor.

## Primeira classificação nas sete categorias

Esta classificação é uma primeira versão; os rótulos devem ser conferidos com a nomenclatura exata da Aula 8 antes da consolidação final.

| Categoria | Classificação inicial | Justificativa |
|---|---|---|
| Natureza | Aplicada | Busca evidência prática para uma decisão de configuração de um CMS em uso. |
| Objetivos | Explicativa e comparativa | Compara duas condições e estima o efeito do estado do cache nas métricas definidas. |
| Abordagem | Quantitativa | Usa tempos de resposta medidos em milissegundos. |
| Procedimentos | Experimento controlado, com medidas repetidas pareadas | Manipula deliberadamente o estado do cache e mantém o restante do ambiente constante. |
| Tempo | Longitudinal de curta duração / medidas repetidas | A mesma unidade será observada repetidamente nas duas condições durante a campanha de coleta. |
| Controle | Ambiente de laboratório controlado, com comparação pareada | Reduz diferenças de conteúdo, rota, ambiente e unidade entre tratamentos. |
| Nível de evidência | Evidência empírica experimental local, inicial | Sustenta conclusões para a instância, versão e carga ensaiadas; não generaliza automaticamente para todas as instalações WordPress. |

## Ameaças à validade e mitigação prevista

- **Conclusão:** amostra pequena pode produzir conclusões frágeis. Mitigar calculando amostra/poder após o piloto, fixando α em 0,05 e reportando efeito e intervalo de confiança, conforme o plano.
- **Interna:** aquecimento desigual, ordem, carga concorrente, rede ou cache residual podem explicar diferenças. Mitigar isolando o ambiente, alternando/randomizando a ordem e documentando aquecimento e invalidação do cache no protocolo.
- **Construto:** latência de uma página é apenas um indicador de desempenho. Mitigar definindo a métrica antes da coleta, validando equivalência do conteúdo servido e limitando as conclusões ao desempenho percebido pelo cliente.
- **Externa:** uma versão, página, configuração e ambiente local não representam toda a variedade de sites e tráfego WordPress. Mitigar descrevendo o ambiente e tratando os dados de adoção da [fonte de impacto](./software.md) somente como contexto, sem extrapolar a medição para volume global.

## Consolidação da entrega Lab05S01

- Objeto e evidências preliminares: [software.md](./software.md) — escolha e exclusividade confirmadas pelo solicitante.
- Métricas e estatísticas: [plano-analise.md](./plano-analise.md).
- Procedimentos de coleta: `docs/protocolo-coleta.md` — dependência da issue #183, ainda pendente.
- Dados públicos para contextualizar impacto: [impacto-fontes.md](./impacto-fontes.md) — fontes e estimativa de impacto dependem da escolha; não converter prevalência de sites em requisições sem dados específicos de tráfego.
