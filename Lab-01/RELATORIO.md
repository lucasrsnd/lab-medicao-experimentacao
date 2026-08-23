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

## 5. Configuração do Processo

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