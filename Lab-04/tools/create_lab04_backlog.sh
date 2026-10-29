#!/usr/bin/env bash
# Backlog Lab04: prévia local por padrão; --apply cria issues e adiciona ao Projects.
# Bash >=4 (Git Bash no Windows), gh autenticado e escrita no repo/projeto.
# Cria os milestones ausentes e os atribui. Veja ../docs/plano-lab04.md.
set -euo pipefail
[[ "${BASH_VERSINFO[0]}" -ge 4 ]] || { echo "Requer Bash >=4." >&2; exit 1; }

REPO="${REPO:-lucasrsnd/lab-medicao-experimentacao}"
PROJECT_OWNER="${PROJECT_OWNER:-lucasrsnd}"
PROJECT_NUMBER="${PROJECT_NUMBER:-2}"
MEMBER_A="${MEMBER_A:-DaviSantos23}"
MEMBER_B="${MEMBER_B:-gustavoprehl}"
MEMBER_C="${MEMBER_C:-lucasrsnd}"
STATUS_FIELD="Status"
BACKLOG_STATUS="${BACKLOG_STATUS:-Backlog}"
MODE=dry-run

die() { printf 'ERRO: %s\n' "$*" >&2; exit 1; }
usage() {
  cat <<'HELP'
Uso: bash Lab-04/tools/create_lab04_backlog.sh [--dry-run|--table|--apply]
  --dry-run  Prévia completa local (padrão); não requer gh ou rede.
  --table    Tabela Markdown das issues; sem rede.
  --apply    Cria milestones e issues ausentes e as adiciona ao Projects existente.
Variáveis: REPO, PROJECT_OWNER, PROJECT_NUMBER, MEMBER_A/B/C, BACKLOG_STATUS.
Reexecução reutiliza issues já criadas (marcador lab04-backlog no corpo) e
preserva conteúdo, assignees e status; só preenche milestone vazio.
HELP
}
for arg in "$@"; do
  case "$arg" in
    --dry-run) MODE=dry-run ;;
    --apply) MODE=apply ;;
    --table) MODE=table ;;
    --help|-h) usage; exit 0 ;;
    *) die "Opção desconhecida: $arg (use --help)" ;;
  esac
done
[[ "$REPO" =~ ^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$ ]] || die "REPO deve ser owner/repo."
[[ "$PROJECT_NUMBER" =~ ^[1-9][0-9]*$ ]] || die "PROJECT_NUMBER inválido."
for login in "$PROJECT_OWNER" "$MEMBER_A" "$MEMBER_B" "$MEMBER_C"; do
  [[ "$login" =~ ^[A-Za-z0-9-]+$ ]] || die "Login inválido: $login"
done

declare -a IDS=()
declare -A WHO TITLE ARTIFACT CONSUMES ACCEPTANCE MILESTONE URL ISSUE_STATE ISSUE_MILESTONE ITEM_ID ITEM_STATUS
declare -A MEMBERS=([A]="$MEMBER_A" [B]="$MEMBER_B" [C]="$MEMBER_C")
declare -A REVIEWERS=([A]="$MEMBER_B" [B]="$MEMBER_C" [C]="$MEMBER_A")
# add_issue ID PAPEL TÍTULO ARTEFATOS CONTRATOS_CONSUMIDOS <<< critérios
add_issue() {
  local id="$1"
  IDS+=("$id")
  WHO["$id"]="$2"; TITLE["$id"]="$3"; ARTIFACT["$id"]="$4"; CONSUMES["$id"]="$5"
  ACCEPTANCE["$id"]="$(cat)"
  case "$id" in
    S01-*) MILESTONE["$id"]=Lab04S01 ;;
    S02-*) MILESTONE["$id"]=Lab04S02 ;;
    FINAL-*) MILESTONE["$id"]=Lab04-EntregaFinal ;;
    *) die "ID inválido: $id" ;;
  esac
}

# ---------------------------------------------------------------- Sprint 01
add_issue 'S01-01' 'B' 'Criar pacote, contratos e configuração compartilhada' \
  'pyproject.toml, src/lab04/{config,contracts,style}.py, README.md, tests/test_contracts.py' \
  'nenhum — esta issue publica os contratos usados pelos demais' <<'ACCEPTANCE'
- [ ] `pyproject.toml` instalável (`pip install -e ".[dev]"`) com numpy, scipy, pandas, plotly, streamlit e pytest.
- [ ] `config.py` com SEED=42, ALPHA=0.05, N_SIMS=10_000, EFFECTS=(0, 0.1, 0.2, 0.3, 0.4, 0.5), N_REAL=30 e TESTS.
- [ ] `contracts.py` com `MarginalParams`, `Scenario` e `TestResult` exatamente como em docs/plano-lab04.md.
- [ ] `style.py` com uma cor fixa por teste (`TEST_COLORS`), rótulos (`TEST_LABELS`) e `apply_layout(fig, title, x_title, y_title)` com legenda.
- [ ] Merge na `main` nos primeiros dias da sprint para os demais ajustarem o import.
ACCEPTANCE

add_issue 'S01-02' 'B' 'Montar dashboard Streamlit (seções 1–3) e gráfico G2' \
  'src/lab04/dashboard/app.py, src/lab04/plots/g2_nula.py, tests/test_g2.py' \
  'style.py; outputs/exemplo_simulado.json; docs/dashboard/*.md; plots.g1_dados.figure' <<'ACCEPTANCE'
- [ ] `streamlit run src/lab04/dashboard/app.py` abre o dashboard; link do dashboard e do GitHub Projects no topo.
- [ ] As 7 seções na ordem do enunciado; textos lidos de `docs/dashboard/NN-*.md` (cada autor edita só o seu texto); seções sem dados mostram aviso, sem quebrar.
- [ ] `g2_nula.figure(test, n, observed_statistic)`: distribuição t com n-2 g.l. sob H0, região de rejeição bicaudal sombreada e p-valor do exemplo marcado como área; para o Spearman, distribuição nula por permutação (semente fixa) sobreposta.
- [ ] Título, eixos com nome/unidade, legenda e cores de `style.TEST_COLORS`.
- [ ] Teste que valida a área sombreada contra o p-valor de `scipy.stats` (fixture sintética, sem depender de outputs/).
- [ ] Merge de fim de sprint: dashboard exibindo G1 e G2.
ACCEPTANCE

add_issue 'S01-03' 'A' 'Implementar gerador de dados simulados (cópula gaussiana)' \
  'src/lab04/simulation/{generator,scenarios}.py, tests/test_generator.py' \
  'contracts.MarginalParams/Scenario; outputs/real_params.json (opcional: usa padrão de config se ausente)' <<'ACCEPTANCE'
- [ ] `generate(params, n, rho, rng)` devolve DataFrame `loc, defects`: Z ~ normal bivariada com correlação ρ; LOC = lognormal(mu, sigma) e defeitos = binomial negativa via quantil de Φ(Z).
- [ ] `generate_batch(scenario, rho, n_sims, rng)` vetorizado, devolve X e Y com forma (n_sims, n) e aplica `scenario.postprocess` se houver.
- [ ] `scenarios.py` com registro (`register`, `get`, `all_scenarios`) e o cenário base `realista` (parâmetros de `real_params.json` ou padrão documentado).
- [ ] Testes: semente fixa reproduz os dados; ρ=0 gera variáveis independentes; mediana de LOC e média de defeitos batem com os parâmetros (tolerância documentada); ρ de Spearman amostral cresce com ρ.
- [ ] Docstring explica que o "tamanho do efeito" é a correlação latente ρ.
ACCEPTANCE

add_issue 'S01-04' 'A' 'Implementar os dois testes e aplicá-los a um conjunto simulado' \
  'src/lab04/stats_tests.py, scripts/exemplo_simulado.py, outputs/exemplo_simulado.json, docs/dashboard/03-testes.md, tests/test_stats_tests.py' \
  'contracts.TestResult; simulation.generator.generate (fixture até o merge)' <<'ACCEPTANCE'
- [ ] `pearson(x, y)` e `spearman(x, y)` devolvem `TestResult` (estatística t, p-valor bicaudal, r/ρ, IC 95% por Fisher z, n).
- [ ] `pvalues(test, X, Y)` vetorizado por linha (postos com empates pela média), para 10.000 repetições sem laço Python.
- [ ] Testes comparam com `scipy.stats.pearsonr`/`spearmanr` (tolerância 1e-8), inclusive com empates e muitos zeros em defeitos.
- [ ] `scripts/exemplo_simulado.py` gera um conjunto (n=30, ρ documentado, SEED) e salva `outputs/exemplo_simulado.json`.
- [ ] Texto da seção 3 (2–4 frases): o que cada teste compara (valores × postos) e a interpretação do resultado do exemplo.
ACCEPTANCE

add_issue 'S01-05' 'C' 'Coletar amostra real e estimar parâmetros da simulação' \
  'src/lab04/real_data.py, data/real/ (bruto, amostra.csv, README), outputs/real_params.json, tests/test_real_data.py' \
  'contracts.MarginalParams' <<'ACCEPTANCE'
- [ ] Escolher dataset NASA MDP/PROMISE com **contagem** de defeitos por módulo (não só booleano) e LOC; registrar fonte, versão e licença em `data/real/README.md`.
- [ ] `load_sample()` sorteia ~30 módulos com SEED e grava `data/real/amostra.csv` (`module_id, loc, defects`).
- [ ] `fit_params(df)` estima lognormal para LOC e binomial negativa para defeitos; salva `real_params.json` com assimetria, proporção de zeros, r de Pearson e ρ de Spearman observados.
- [ ] Testes do ajuste com dados sintéticos de parâmetros conhecidos.
ACCEPTANCE

add_issue 'S01-06' 'C' 'Redigir o cenário (item c) e gerar o gráfico G1' \
  'docs/cenario.md, docs/dashboard/{01-cenario,02-dados}.md, src/lab04/plots/g1_dados.py, tests/test_g1.py' \
  'style.py; data/real/amostra.csv; DataFrame simulado (fixture até o merge)' <<'ACCEPTANCE'
- [ ] `cenario.md`: pergunta em uma frase; H0: ρ = 0 e H1 (decidir e justificar uni ou bicaudal); distribuições e parâmetros escolhidos a partir dos dados reais.
- [ ] Expectativa registrada **antes** das simulações: qual teste deve se sair melhor e por quê (commit datado na S01).
- [ ] `g1_dados.figure(real, simulated)`: histograma de LOC e de defeitos, real ao lado do simulado, com título, eixos com unidade e legenda.
- [ ] Textos das seções 1 e 2 do dashboard (2–4 frases cada).
- [ ] Teste do gráfico com fixtures (número de traços, títulos e eixos).
ACCEPTANCE

# ---------------------------------------------------------------- Sprint 02
add_issue 'S02-01' 'A' 'Implementar motor Monte Carlo (Q1 erro tipo I, Q2 poder)' \
  'src/lab04/simulation/montecarlo.py, scripts/simular.py, outputs/simulacoes.csv, tests/test_montecarlo.py' \
  'simulation.generator; simulation.scenarios; stats_tests.pvalues' <<'ACCEPTANCE'
- [ ] `rejection_rates(scenarios, effects, n_sims, alpha, seed)` devolve DataFrame no formato de `simulacoes.csv` (taxa e IC 95% de Monte Carlo).
- [ ] Q1: 10.000 conjuntos com H0 verdadeira por cenário; Q2: mesma rotina para todos os EFFECTS (≥5, começando em 0).
- [ ] Roda todos os cenários registrados (inclusive os de violação, sem conhecê-los); execução completa em poucos minutos.
- [ ] Testes: com marginais normais, erro tipo I dentro de 5% ± margem; poder cresce com o efeito; mesma semente, mesmo CSV.
ACCEPTANCE

add_issue 'S02-02' 'A' 'Calcular poder em função do tamanho da amostra' \
  'src/lab04/simulation/sample_size.py, outputs/poder_por_n.csv, tests/test_sample_size.py' \
  'simulation.montecarlo.rejection_rates' <<'ACCEPTANCE'
- [ ] `power_by_n(scenario, effect, ns)` estima o poder dos dois testes para vários n.
- [ ] Poder no n real com o efeito observado em `real_params.json` e n necessário para 80% em cada teste (seção 6 do enunciado, "para discutir").
- [ ] Testes: poder cresce com n; reprodutível com semente.
ACCEPTANCE

add_issue 'S02-03' 'C' 'Criar cenários que violam pressupostos (Q3)' \
  'src/lab04/simulation/violations.py, docs/dashboard/q3-violacoes.md, tests/test_violations.py' \
  'contracts.Scenario; simulation.scenarios.register' <<'ACCEPTANCE'
- [ ] `register_violations()` registra ao menos 2 cenários: outliers (contaminação em fração documentada), assimetria extrema e/ou amostra pequena (ex.: n=10).
- [ ] Outliers injetados de forma independente em X e Y para manter H0 verdadeira quando ρ=0.
- [ ] Sem alterar `generator.py`: usa apenas `Scenario.postprocess` e parâmetros.
- [ ] Texto curto: por que cada violação afeta mais o Pearson do que o Spearman (ou não).
- [ ] Testes: fração de outliers correta; independência preservada com ρ=0.
ACCEPTANCE

add_issue 'S02-04' 'C' 'Gerar o gráfico G3 (erro tipo I por situação)' \
  'src/lab04/plots/g3_erro_tipo1.py, docs/dashboard/04-erro-tipo1.md, tests/test_g3.py' \
  'style.py; formato de outputs/simulacoes.csv (fixture até o merge)' <<'ACCEPTANCE'
- [ ] `g3_erro_tipo1.figure(results)`: taxa de rejeição com efeito 0 por cenário e teste, barras de IC e linha em 5%.
- [ ] Título, eixos com unidade (%), legenda e cores de `style.TEST_COLORS`.
- [ ] Texto da seção 4: qual teste ficou perto de 5% em cada situação e qual se desviou (liberal/conservador).
- [ ] Teste com CSV sintético.
ACCEPTANCE

add_issue 'S02-05' 'B' 'Gerar G4 (curvas de poder) e integrar seções 4–5 ao dashboard' \
  'src/lab04/plots/g4_poder.py, src/lab04/dashboard/app.py, docs/dashboard/05-poder.md, tests/test_g4.py' \
  'style.py; outputs/simulacoes.csv; plots.g3_erro_tipo1.figure' <<'ACCEPTANCE'
- [ ] `g4_poder.figure(results)`: proporção de rejeições × tamanho do efeito, os dois testes no mesmo gráfico, um painel por cenário (inclui Q3).
- [ ] Título, eixos com unidade, legenda e mesmas cores dos demais gráficos.
- [ ] Seções 4 e 5 do dashboard leem `outputs/simulacoes.csv` (sem rodar 10.000 simulações ao abrir).
- [ ] Texto da seção 5: qual teste tem mais poder e onde a vantagem muda de lado.
- [ ] Merge de fim de sprint: dashboard exibindo G3 e G4.
ACCEPTANCE

add_issue 'S02-06' 'B' 'Bônus: simulador interativo de poder' \
  'src/lab04/dashboard/interativo.py, tests/test_interativo.py' \
  'simulation.montecarlo.rejection_rates; simulation.scenarios' <<'ACCEPTANCE'
- [ ] Sliders de tamanho da amostra e tamanho do efeito (e seleção de cenário) mostram o poder dos dois testes.
- [ ] Usa `rejection_rates` com menos repetições e cache (`st.cache_data`) para responder em poucos segundos; informa o número de repetições.
- [ ] Mesmas cores dos demais gráficos.
ACCEPTANCE

# ---------------------------------------------------------------- Entrega final
add_issue 'FINAL-01' 'B' 'Integrar módulos e criar comando único de reprodução' \
  'src/lab04/{cli,__main__}.py, README.md' \
  'todos os módulos' <<'ACCEPTANCE'
- [ ] Merge das branches resolvido; `pytest` passando na `main`.
- [ ] `python -m lab04 tudo` regenera amostra, parâmetros, exemplo e simulações; `streamlit run` abre o dashboard.
- [ ] README com instalação e os dois comandos; execução testada em ambiente limpo.
ACCEPTANCE

add_issue 'FINAL-02' 'B' 'Completar seções 6–7 e publicar o dashboard' \
  'src/lab04/dashboard/app.py, docs/dashboard/{06-dados-reais,07-conclusao}.md' \
  'real_data.load_sample; stats_tests; outputs/*' <<'ACCEPTANCE'
- [ ] Seção 6: tabela com estatística, p-valor, tamanho do efeito (com IC) e conclusão de cada teste nos dados reais.
- [ ] Seção 7: expectativa × resultado e recomendação (qual teste usar e quando a escolha mudaria).
- [ ] Todo gráfico com texto de 2–4 frases; links do dashboard e do Projects no topo.
- [ ] Publicado (Streamlit Community Cloud) e link no README.
ACCEPTANCE

add_issue 'FINAL-03' 'B' 'Preparar roteiro das 15 perguntas da apresentação' \
  'docs/roteiro-apresentacao.md' \
  'dashboard final' <<'ACCEPTANCE'
- [ ] 15 perguntas divididas entre os três, no mínimo 4 por integrante, cada resposta apontando a seção/gráfico do dashboard.
- [ ] Respostas de ~30 s; ensaio completo em até 7 minutos com os três.
ACCEPTANCE

declare -A SEEN=()
for id in "${IDS[@]}"; do
  [[ -z "${SEEN[$id]:-}" ]] || die "ID repetido: $id"
  SEEN["$id"]=1
done

body_for() {
  local id="$1" role="${WHO[$1]}"
  printf '<!-- lab04-backlog:%s -->\n\n' "$id"
  printf '## Objetivo\n\n%s\n\n' "${TITLE[$id]}"
  printf -- '- Responsável: @%s\n- Revisor: @%s\n' "${MEMBERS[$role]}" "${REVIEWERS[$role]}"
  printf -- '- Milestone: **%s**\n' "${MILESTONE[$id]}"
  printf -- '- Artefatos (relativos a Lab-04): %s\n' "${ARTIFACT[$id]}"
  printf -- '- Contratos consumidos: %s\n' "${CONSUMES[$id]}"
  printf '\nDesenvolvimento independente: use fixtures para o que outro integrante ainda não entregou. '
  printf 'Não edite arquivos de outras issues; a integração ocorre no merge.\n'
  printf '\n## Critérios de aceite\n\n%s\n' "${ACCEPTANCE[$id]}"
  cat <<'DOD'

## Definition of Done

- [ ] Código versionado; commits com referência ao número desta issue (#N).
- [ ] Testes do módulo passando (`pytest`), semente fixa quando houver aleatoriedade.
- [ ] Revisão por outro integrante e cartão atualizado no Projects.

Fonte: Lab-04/Enunciado.md. Arquitetura e contratos: Lab-04/docs/plano-lab04.md.
DOD
}

if [[ "$MODE" == table ]]; then
  printf '| ID | Issue | Responsável | Milestone |\n|---|---|---|---|\n'
  for id in "${IDS[@]}"; do
    printf '| %s | %s | @%s | %s |\n' "$id" "${TITLE[$id]}" \
      "${MEMBERS[${WHO[$id]}]}" "${MILESTONE[$id]}"
  done
  exit 0
fi

printf 'Repo: %s | Projects: %s/%s | Issues: %s | Modo: %s\n' \
  "$REPO" "$PROJECT_OWNER" "$PROJECT_NUMBER" "${#IDS[@]}" "$MODE"
if [[ "$MODE" == dry-run ]]; then
  for id in "${IDS[@]}"; do
    printf '\n---\n# [Lab04 %s] %s\n\n' "$id" "${TITLE[$id]}"
    body_for "$id"
  done
  printf '\nPrévia concluída. Nenhuma chamada ao GitHub. Use --apply para criar.\n'
  exit 0
fi

command -v gh >/dev/null || die "Instale GitHub CLI e execute gh auth login."
gh auth status >/dev/null 2>&1 || die "Autentique com gh auth login; Projects exige escopo project."
gh repo view "$REPO" --json nameWithOwner >/dev/null
for role in A B C; do
  gh api "repos/$REPO/assignees/${MEMBERS[$role]}" >/dev/null ||
    die "Sem acesso ou assignee indisponível: ${MEMBERS[$role]}"
done
project_id=$(gh project view "$PROJECT_NUMBER" --owner "$PROJECT_OWNER" --format json --jq '.id')
[[ -n "$project_id" ]] || die "Projeto não encontrado."
export LAB04_STATUS_FIELD="$STATUS_FIELD" LAB04_BACKLOG_STATUS="$BACKLOG_STATUS"
field_data=$(gh project field-list "$PROJECT_NUMBER" --owner "$PROJECT_OWNER" --limit 100 \
  --format json --jq '.fields[] | select(.name == env.LAB04_STATUS_FIELD) |
    .id as $field | .options[]? | select(.name == env.LAB04_BACKLOG_STATUS) |
    [$field, .id] | @tsv')
[[ -n "$field_data" && "$field_data" != *$'\n'* ]] ||
  die "Campo/opção não encontrado ou ambíguo: $STATUS_FIELD/$BACKLOG_STATUS."
IFS=$'\t' read -r status_field_id backlog_option_id <<< "$field_data"

# Cria os milestones que ainda não existem (abertos ou fechados).
existing_milestones=$(gh api --paginate "repos/$REPO/milestones?state=all&per_page=100" --jq '.[].title')
while read -r milestone; do
  if grep -Fxq -- "$milestone" <<< "$existing_milestones"; then
    printf 'Milestone existente: %s\n' "$milestone"
  else
    gh api "repos/$REPO/milestones" -f title="$milestone" >/dev/null
    printf 'Milestone criado: %s\n' "$milestone"
  fi
done < <(printf '%s\n' "${MILESTONE[@]}" | sort -u)

# Reencontra issues já criadas (abertas ou fechadas) pelo marcador no corpo.
existing=$(gh api --paginate "repos/$REPO/issues?state=all&per_page=100" --jq '
  .[] | select(has("pull_request") | not) |
  . as $issue | ((.body // "") | capture("<!-- lab04-backlog:(?<key>[A-Z0-9-]+) -->")?) |
  [.key, $issue.html_url, $issue.state, ($issue.milestone.title // "-")] | @tsv')
while IFS=$'\t' read -r key issue_url state milestone; do
  [[ -n "$key" ]] || continue
  [[ -z "${URL[$key]:-}" ]] || die "Marcador duplicado no GitHub: $key."
  URL["$key"]="$issue_url"
  ISSUE_STATE["$key"]="$state"
  ISSUE_MILESTONE["$key"]="$milestone"
done <<< "$existing"

project_items=$(gh project item-list "$PROJECT_NUMBER" --owner "$PROJECT_OWNER" \
  --limit 10000 --format json --jq '
    if .totalCount > (.items | length) then error("Lista do projeto truncada") else
    .items[] | select(.content.type == "Issue") |
    [.content.url, .id, (.status // "-")] | @tsv end')
while IFS=$'\t' read -r issue_url item_id status; do
  [[ -n "$issue_url" ]] || continue
  ITEM_ID["$issue_url"]="$item_id"
  ITEM_STATUS["$issue_url"]="$status"
done <<< "$project_items"

body_file=$(mktemp)
trap 'rm -f -- "$body_file"' EXIT
created=0
reused=0
for id in "${IDS[@]}"; do
  if [[ -n "${URL[$id]:-}" ]]; then
    issue_url="${URL[$id]}"
    reused=$((reused + 1))
    printf 'Reutilizada %s: %s\n' "$id" "$issue_url"
    if [[ "${ISSUE_MILESTONE[$id]}" == "-" ]]; then
      gh issue edit "$issue_url" --repo "$REPO" --milestone "${MILESTONE[$id]}" >/dev/null
      printf '  milestone atribuído: %s\n' "${MILESTONE[$id]}"
    fi
  else
    body_for "$id" > "$body_file"
    issue_url=$(gh issue create --repo "$REPO" --title "[Lab04 $id] ${TITLE[$id]}" \
      --body-file "$body_file" --assignee "${MEMBERS[${WHO[$id]}]}" \
      --milestone "${MILESTONE[$id]}")
    [[ "$issue_url" == "https://github.com/$REPO/issues/"* ]] ||
      die "Resposta inesperada ao criar $id. Confira o GitHub antes de repetir."
    URL["$id"]="$issue_url"
    ISSUE_STATE["$id"]=open
    created=$((created + 1))
    printf 'Criada %s: %s\n' "$id" "$issue_url"
  fi
  if [[ -z "${ITEM_ID[$issue_url]:-}" ]]; then
    item_id=$(gh project item-add "$PROJECT_NUMBER" --owner "$PROJECT_OWNER" \
      --url "$issue_url" --format json --jq '.id')
    [[ -n "$item_id" ]] || die "Não foi possível adicionar $issue_url ao projeto."
    ITEM_ID["$issue_url"]="$item_id"
    ITEM_STATUS["$issue_url"]="-"
  fi
  if [[ "${ISSUE_STATE[$id]}" == open && "${ITEM_STATUS[$issue_url]}" == "-" ]]; then
    gh project item-edit --id "${ITEM_ID[$issue_url]}" --project-id "$project_id" \
      --field-id "$status_field_id" --single-select-option-id "$backlog_option_id" >/dev/null
    ITEM_STATUS["$issue_url"]="$BACKLOG_STATUS"
  fi
done
printf '\nConcluído: %s criadas; %s reutilizadas; %s issues no projeto.\n' \
  "$created" "$reused" "${#IDS[@]}"
