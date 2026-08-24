# Relatório de Análise: Características de Repositórios Populares no GitHub

**Link do repositório/GitHub Projects:** `https://github.com/lucasrsnd/lab-medicao-experimentacao`

## 1. Introdução
Sistemas de código aberto (open-source) tornaram-se a espinha dorsal do desenvolvimento de software moderno. O sucesso e a sustentabilidade desses projetos dependem de uma comunidade ativa, maturidade do código e boas práticas de manutenção.

Neste laboratório, investigamos as principais características dos 1.000 repositórios mais populares do GitHub (medidos pelo número de estrelas). O objetivo é extrair e analisar métricas de repositório, atividades de contribuição e gestão de *issues* para entender o que define um projeto de sucesso e como diferentes ecossistemas (linguagens de programação) se comportam nesse cenário.

### 1.1 Hipóteses Informais
Antes da coleta e análise aprofundada dos dados, estabelecemos as seguintes hipóteses baseadas no senso comum do desenvolvimento de software:

* **RQ01 (Idade):** Acreditamos que sistemas muito populares sejam maduros e antigos, tendo em média mais de 5 anos de criação, tempo necessário para construir uma grande base de usuários e estrelas.
* **RQ02 (Contribuição Externa):** Espera-se que esses projetos recebam um volume massivo de contribuições externas, com a mediana de *Pull Requests* aceitas na casa dos milhares.
* **RQ03 (Releases):** A hipótese é de que projetos populares adotem práticas de integração/entrega contínua, lançando *releases* com alta frequência (várias dezenas por ano).
* **RQ04 (Atualizações):** Espera-se que a atividade seja diária ou semanal. O tempo até a última atualização (último *push*) deve ser, em sua esmagadora maioria, inferior a 7 dias.
* **RQ05 (Linguagem Primária):** Hipotetizamos que as linguagens mais comuns nesses repositórios acompanhem os relatórios de mercado (como o GitHub Octoverse), sendo dominados por JavaScript, Python, TypeScript e Go.
* **RQ06 (Gestão de Issues):** Projetos saudáveis e populares devem possuir um alto engajamento da comunidade e dos mantenedores, refletindo em um percentual de *issues* fechadas superior a 80%.
* **RQ07 (Correlação por Linguagem):** Acreditamos que repositórios escritos nas linguagens mais populares (Top 3) receberão proporcionalmente mais PRs, mais *releases* e atualizações mais frequentes, devido ao maior tamanho de suas comunidades de desenvolvedores.

## 2. Metodologia de Coleta

A coleta foi feita inteiramente via **GraphQL API do GitHub**, com script próprio do grupo (Python + `requests` + `python-dotenv`), sem bibliotecas de terceiros que abstraem a API, conforme exigido pelo enunciado.

**Critério de amostragem:** os repositórios foram buscados com `search(query: "stars:>1 sort:stars-desc", type: REPOSITORY, ...)`, ou seja, ordenados do maior para o menor número de estrelas. Não existe uma lista fixa de repositórios: o "top N" é definido dinamicamente no momento da consulta.

**Campos coletados por RQ**, todos extraídos do mesmo objeto `Repository` numa única query combinada:

| RQ | Métrica | Campo GraphQL |
|---|---|---|
| RQ01 | Idade do repositório | `createdAt` |
| RQ02 | PRs aceitas | `pullRequests(states: MERGED) { totalCount }` |
| RQ03 | Total de releases | `releases { totalCount }` |
| RQ04 | Tempo até última atualização | `pushedAt` |
| RQ05 | Linguagem primária | `primaryLanguage { name }` |
| RQ06 | Razão de issues fechadas | `issues { totalCount }` e `issues(states: CLOSED) { totalCount }` |

Para RQ05, a fonte de referência usada para "linguagens mais populares" é o **GitHub Octoverse** (edição 2025), mantida como referência única em todo o laboratório.

**Processo em 3 etapas, ao longo das sprints:**

1. **S01, validação individual em amostra pequena (10 repositórios):** cada integrante testou a extração da sua parte (Gustavo: RQ01/RQ02; Lucas: RQ03/RQ04; Davi: RQ05/RQ06/RQ07), conferindo manualmente se os valores batiam com a página do GitHub. Nessa etapa, pedir os 100 repositórios do Lab01S01 numa única chamada GraphQL (com todos os campos aninhados de todo mundo juntos) retornava erro **502** da API. Resolvido paginando a consulta em lotes menores por cursor (`after`/`pageInfo`), em vez de uma única chamada.
2. **S02, paginação para 1000 repositórios:** o mesmo mecanismo de paginação por cursor foi estendido para coletar a base completa, salva em `data/raw/repositorios_s02.csv`. A coleta fechou em **998 repositórios** (não exatamente 1000) por causa do comportamento da Search API do GitHub em coletas longas (resultado, não falha nos dados). Cada integrante validou individualmente a consistência da sua parte nessa base (distribuição, outliers pela regra do IQR, valores ausentes) e registrou uma hipótese informal antes de calcular o resultado real.
3. **S03, análise e visualização:** cálculo das estatísticas finais (mediana, média, outliers) e geração dos gráficos (`reports/figures/`) a partir da base de 998 repositórios, usando `pandas` para as estatísticas e `matplotlib` para as figuras.

O rastreamento de todas as tarefas foi feito via Issues no GitHub Projects, com snapshots do board exportados ao final de cada sprint (ver Seção 5).

## 3. Resultados por RQ

*(estatísticas sobre os 998 repositórios coletados; figuras completas em `reports/figures/`, legendas em `reports/figures/legendas.md`)*

**RQ01, Idade do repositório**
Mediana: **7,72 anos** (média 7,65, min 0,00, max 18,34). Sem outliers pela regra do IQR, distribuição concentrada e sem cauda pesada. Mais antigos: `rails/rails` (18,34 anos), `git/git` (18,06). Mais novos: repositórios ligados à onda de IA que já acumularam estrelas suficientes em poucos meses.

**RQ02, PRs aceitas (merged)**
Mediana: **768** (média 4.211,5, 5,5x maior que a mediana). 123 outliers pela regra do IQR (12,3%), indicando distribuição fortemente assimétrica à direita. Maior: `firstcontributions/first-contributions` (103.014, projeto cujo propósito é ensinar a abrir a primeira PR). Menor: `torvalds/linux` (0, o kernel Linux não usa PR nativo do GitHub, contribui por lista de e-mail).

**RQ03, Total de releases**
Mediana: **39,5** (média 127,4). 92 outliers pela regra do IQR (9,2%). 27,9% dos repositórios têm 0 releases. Maiores: `langchain-ai/langchain`, `vercel/next.js`, `ggml-org/llama.cpp`, `electron/electron`, `storybookjs/storybook`, todos batendo exatamente em 1000, provável teto de contagem do campo `releases.totalCount` na paginação usada e não o total real.

**RQ04, Tempo até última atualização**
Mediana: **2 dias** (média 112,6 dias, puxada por outliers). 190 outliers pela regra do IQR (19,0%). 61,3% dos repositórios foram atualizados na última semana. Maior tempo sem atualizar: `exacity/deeplearningbook-chinese` (2.445 dias, quase 7 anos).

**RQ05, Linguagem primária**
Top 3: **Python** (228), **TypeScript** (174), **JavaScript** (110). 43 linguagens distintas identificadas, nenhum valor ausente na base de 998 (repositórios sem linguagem classificável ficaram marcados como "N/A" e entraram na contagem). Top 3 do laboratório coincide com o top 3 do GitHub Octoverse 2025.

**RQ06, Razão de issues fechadas**
Mediana: **0,86** (86%). 4,3% dos repositórios com 0 issues cadastradas ou funcionalidade desativada (razão forçada a 0,0 nesses casos). 60 outliers pela regra do IQR.

**RQ07, Comparação por linguagem (RQ02+RQ03+RQ04 agrupadas por RQ05)**
TypeScript apresentou a maior mediana de PRs aceitas (1.985) entre as linguagens mais frequentes, mas **Rust** (2.491) e **Go** (1.690), bem menos frequentes no top 1.000, superaram Python (559,5) e JavaScript (630). Ou seja, volume de repositórios numa linguagem não é proporcional ao volume de contribuição externa por repositório.

## 4. Discussão: Hipótese vs. Resultado

| RQ | Hipótese | Resultado | Confirmou? |
|---|---|---|---|
| RQ01 | Maduros, média > 5 anos | Mediana 7,72 anos, sem outliers relevantes | **Sim** |
| RQ02 | Contribuição na casa dos milhares | Mediana de 768 (não milhares) | **Parcial** |
| RQ03 | Releases frequentes (dezenas por ano) | Mediana 39,5, mas 27,9% com 0 releases | **Parcial** |
| RQ04 | Atualização quase sempre < 7 dias | Mediana 2 dias, 61,3% na última semana | **Sim** |
| RQ05 | Dominado por JS/Python/TS/Go | Top 3 = Python, TS, JS (bate com Octoverse) | **Sim** |
| RQ06 | Issues fechadas > 80% | Mediana 86% | **Sim** |
| RQ07 | Top 3 linguagens concentram mais contribuição/releases/atualização | Rust e Go (menos frequentes) superaram Python/JS em PRs | **Não** |

**RQ01:** a hipótese de maturidade se confirma como norma (mediana bem acima de 5 anos, distribuição concentrada), mas o mínimo em 0 anos mostra que popularidade extrema também pode ser alcançada quase instantaneamente. A maturidade é regra, não unanimidade.

**RQ02:** a hipótese superestimou a escala (esperávamos "milhares", saiu "centenas"), mas a direção geral está certa: populares recebem mais contribuição do que projetos comuns. O achado mais importante aqui é metodológico: `torvalds/linux` aparece com 0 PRs aceitas não por falta de contribuição, mas porque o kernel usa lista de e-mail em vez do mecanismo nativo de PR do GitHub. A métrica mede um canal específico, não "contribuição externa" em geral, e projetos com workflow fora do GitHub aparecem artificialmente como pouco colaborativos.

**RQ03:** esse foi o achado que mais contrariou a expectativa inicial da nossa dupla (RQ03/RQ04). A amostra pequena do S01 (10 repositórios) sugeria fortemente que a maioria não lançava releases, mas isso era coincidência de amostra: caiu em várias listas/coleções do tipo `awesome-*`, que não são representativas do conjunto todo. Na base de 998, a maioria lança releases sim, e alguns projetos de software ativo lançam com bastante frequência (a ponto de bater no teto de contagem do campo).

**RQ04:** confirmada com folga. Mediana de 2 dias mostra que a maioria dos repositórios populares tem manutenção realmente ativa. A cauda longa também apareceu como esperado (19% de outliers), puxada por projetos de referência/didáticos que são conteúdo mais estático do que software em manutenção contínua.

**RQ05:** confirmada, e de forma direta. O top 3 do laboratório bate exatamente com o top 3 do Octoverse 2025, reforçando que o ecossistema open-source mais popular do GitHub acompanha as tendências gerais de mercado.

**RQ06:** confirmada com margem (86% vs. 80% hipotetizado), reforçando que repositórios populares mantêm boa saúde de gestão de issues. Vale notar que alguns projetos massivos (`torvalds/linux` entre eles) aparecem com razão 0,0 porque desativaram issues no GitHub. Mesma limitação de métrica observada na RQ02, projetos que não usam certos recursos nativos do GitHub aparecem distorcidos nas métricas baseadas nesses recursos.

**RQ07:** foi a hipótese refutada com mais clareza. Não é o volume de repositórios numa linguagem que determina o volume de contribuição por repositório. Linguagens de nicho mais especializado (Rust, Go) tiveram medianas de PRs mais altas que linguagens dominantes em quantidade (Python, JavaScript). Isso sugere que projetos em linguagens menos populares, mas que ainda assim atingem o top 1.000 por estrelas, tendem a ser projetos de infraestrutura/sistemas com comunidades muito engajadas proporcionalmente ao seu tamanho.



O gerenciamento e o rastreamento das tarefas deste laboratório foram realizados utilizando o GitHub Projects (v2). Adotamos uma abordagem visual baseada no sistema Kanban para refletir o progresso real e contínuo do grupo.

### Estrutura do Quadro
O fluxo de trabalho foi mapeado através das seguintes colunas (Status):
* **Backlog:** Tarefas planejadas e identificadas, aguardando priorização para as próximas sprints.
* **To Do:** Issues selecionadas para a sprint atual, prontas para serem assumidas.
* **Doing:** Tarefas em desenvolvimento ativo pelo seu responsável.
* **Review:** Atividades implementadas aguardando revisão de código (Pull Requests) ou validação do grupo.
* **Done:** Tarefas aprovadas, merjadas na branch principal e totalmente concluídas.

### Política de WIP (Work in Progress)
Definimos um limite de WIP igual a **3** para a coluna **Doing**. 
**Justificativa:** Como a equipe é formada por 3 integrantes, esse limite garante que cada membro trabalhe em no máximo uma tarefa de forma simultânea. Essa restrição evita a perda de foco (*context switching*), previne o gargalo de tarefas incompletas e incentiva a colaboração mútua e o auxílio nas revisões antes de puxar um novo cartão.

*(Insira abaixo o print do board)*
![Board Kanban Final](./caminho/para/sua/imagem.png)