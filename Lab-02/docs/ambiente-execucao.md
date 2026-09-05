# Preparação do Ambiente de Execução

> Dono: Gustavo — Issue #47. Este documento fixa o
> ambiente usado em **todos** os 18 trials da Milestone `Lab02S02` — precisa
> estar fechado (e confirmado pelo trio) antes de a S02 começar.

## Linguagem

Python 3.10+ (compatível com Radon/jscpd).

## IDE

VS Code, mesma configuração-base para os três integrantes (evita que
diferença de setup vire variável de confusão entre trials):

- Extensões de IA **instaladas mas desabilitáveis por trial** (ver seção
  "Como desabilitar" abaixo) — nenhuma outra extensão de autocomplete/IA além
  da escolhida no experimento deve ficar ativa durante os trials.
- Tema, fonte e atalhos: livre por integrante (não afeta as métricas).
- Auto-save ligado (para o script de cronometragem detectar o código salvo).

## Assistente de IA

**Fechado: Claude** (ferramenta genérica) — modelo específico **não fixado
por enquanto**, decisão do trio. Precisa ser o mesmo assistente em 100% dos
trials "Com IA" do grupo, por exigência do enunciado.

```
AI_ASSISTANT_NAME=Claude
AI_ASSISTANT_VERSION=
```

⚠️ Pendência antes da S02: o relatório final exige "assistente de IA **e
versão**" na metodologia, para reprodutibilidade (enunciado, Passo 5). Como o
modelo por trás do Claude pode mudar entre os trials, o trio precisa, antes de
começar a execução: (a) fixar qual modelo será usado em todos os 18 trials, ou
(b) se for realmente deixado em aberto, registrar o modelo efetivo **por
trial** no template de log (`data/raw/log_trials.csv`, seção abaixo) em vez de
só uma vez no `.env` — senão RQ3/discussão não conseguem descartar variação de
modelo como fator de confusão.

## Como desabilitar o assistente nos trials "Sem IA"

Ponto de maior risco de contaminação entre tratamentos — checklist antes de
cada trial "Sem IA":

1. Fechar/desabilitar a extensão do assistente de IA no VS Code (ou sair da
   sessão) antes de abrir o kata.
2. Não consultar chatbots (ChatGPT/Claude/Gemini) em aba separada durante o trial.
3. Conferir a checklist acima **antes** de iniciar o cronômetro (`src/timing/trial_timer.py`).

## Cronômetro / registro de tempo

Ver `src/timing/` (Issue #46). Time-box fixo em `TRIAL_TIMEBOX_MIN` (`.env`,
default 35 — só pode reduzir e justificar no relatório, nunca aumentar).

## Template de log manual do trial

Complementar ao CSV automático do timer (`data/raw/trials_tempo.csv`).
Preencher **um por trial**, salvo em `data/raw/log_trials.csv` (mesmo cabeçalho
para os três integrantes):

| kata | integrante | tratamento | modelo_ia | n_prompts_ia | observacoes |
|---|---|---|---|---|---|
| k1 | gustavoprehl | com_ia | | | |

- `modelo_ia`: só se aplica a trials "Com IA" — registrar o modelo efetivo por
  trás do Claude usado naquele trial (ex.: "Sonnet 5"), já que o modelo não foi
  fixado previamente (ver pendência acima).

- `n_prompts_ia`: nº de prompts/interações com o assistente (opcional/exploratória, RQ1) — só se aplica a trials "Com IA".
- `observacoes`: qualquer intercorrência (trial interrompido, dúvida sobre o kata, etc.), livre-texto, para discussão qualitativa no relatório.
