# Desenho do Experimento — Lab02

> Dono: Davi — Issues "Desenho do experimento" (hipóteses/variáveis/tratamentos)
> e "Escolha e validação dos katas" (katas + ameaças à validade) da Milestone
> `Lab02S01`. Template abaixo segue a Etapa 1 do enunciado (`Laboratório 02.pdf`).

## A. Hipóteses

- H0: O uso de assistente de IA generativa não altera significativamente o tempo de resolução, a quantidade de testes passando ou a qualidade estrutural do código (complexidade e duplicação).
- H1 (por RQ, se necessário):
  - **H1_1 (RQ1):** O tempo mediano de resolução (*time-to-green*) é menor nos trials com assistente de IA.
  - **H1_2 (RQ2):** A proporção mediana de testes de aceitação passando ao final do time-box é maior nos trials com assistente de IA.
  - **H1_3 (RQ3):** Há diferença estatística na complexidade ciclomática média e/ou no percentual de duplicação de código (normalizado por LOC) entre os tratamentos.

## B. Variáveis dependentes

- Tempo (time-to-green / censura em time-box fixo de 35 minutos)
- Nº de testes de aceitação passando ao final do trial (Taxa de Sucesso)
- Métricas estáticas: complexidade ciclomática (Radon cc), duplicação (jscpd), LOC

## C. Variável independente

- Uso (ou não) do assistente de IA generativa

## D. Tratamentos

- Com IA: O participante resolve o kata utilizando a IDE padrão com o assistente de IA do grupo (Claude) ativado, livre para fornecer autocompletes e receber prompts durante os 35 minutos.
- Sem IA: O participante resolve o kata utilizando apenas a IDE padrão, raciocínio lógico e documentação oficial (browser), com a extensão do assistente de IA explicitamente desabilitada.

## E. Objetos experimentais

- 6 katas de dificuldade equivalente (ver `katas/`) focados em regras de negócio e processamento de dados.

## F. Tipo de projeto experimental

- Crossover / within-subject, contrabalanceado (ver tabela de tratamento por integrante/kata em `../katas/README.md`)

## G. Quantidade de medições

- 6 trials/integrante × 3 integrantes = 18 trials totais

## H. Ameaças à validade

- Efeito de aprendizado entre katas: Será mitigado pelo design estritamente contrabalanceado (os integrantes alternarão a ordem de execução dos katas e intercalarão os tratamentos com e sem IA).
- Familiaridade prévia com a ferramenta de IA: Controlada pela padronização. Todos os membros usarão exatamente a mesma ferramenta (Claude) na mesma IDE — ver `docs/ambiente-execucao.md` para o registro dessa decisão e a pendência de fixar o modelo específico.
- Vazamento de solução já vista: O experimento será realizado com as sessões isoladas e controladas por um *time-box* inflexível, impedindo o compartilhamento de código ou consultas aos colegas durante a resolução.
- Memorização (katas muito conhecidas): Para impedir que a IA forneça soluções de repositórios de treinamento (HackerRank/LeetCode), foram elaborados 6 katas autorais focados em regras de negócio específicas, que possuem baixíssima ou nenhuma indexação pública.