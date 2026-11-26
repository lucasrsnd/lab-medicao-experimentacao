# Backlog Lab05 (Sprint 01): prévia local por padrão; -Apply cria issues e adiciona ao Projects em "Backlog".
# Requer GitHub CLI autenticado com escopo project:  gh auth login -s project
# Uso: powershell -ExecutionPolicy Bypass -File Lab-05/tools/create_lab05_backlog.ps1 [-Table | -Apply]
# Reexecução reutiliza issues já criadas (marcador lab05-backlog no corpo); não duplica.
param(
  [switch]$Apply,
  [switch]$Table,
  [string]$Repo = 'lucasrsnd/lab-medicao-experimentacao',
  [string]$ProjectOwner = 'lucasrsnd',
  [int]$ProjectNumber = 2,
  [string]$MemberA = 'DaviSantos23',
  [string]$MemberB = 'gustavoprehl',
  [string]$MemberC = 'lucasrsnd',
  [string]$Status = 'Backlog'
)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding $false
$OutputEncoding = [Console]::OutputEncoding

$Members   = @{ A = $MemberA; B = $MemberB; C = $MemberC }
$Reviewers = @{ A = $MemberB; B = $MemberC; C = $MemberA }
$Roles     = @{ A = 'Planejamento e Método'; B = 'Instrumentação e Operação'; C = 'Análise e Impacto' }
$Issues = New-Object System.Collections.ArrayList

function Add-Issue($Id, $Who, $Title, $Artifacts, $Consumes, $Acceptance) {
  [void]$Issues.Add([pscustomobject]@{
    Id = $Id; Who = $Who; Title = $Title; Artifacts = $Artifacts; Consumes = $Consumes
    Acceptance = $Acceptance.Trim(); Milestone = 'Lab05S01'
  })
}

# ---------------------------------------------------------------- Sprint 01
Add-Issue 'S01-01' 'A' 'Escolher o software e comprovar os três critérios (real, em operação, alto impacto)' `
  'docs/software.md' `
  'nenhum — esta issue define o objeto de estudo usado pelos demais' @'
- [ ] Shortlist de 3 candidatos, cada um com o caminho de estudo que permitiria (seção 2b do enunciado). Repositório público do GitHub **não** vale como objeto de pesquisa.
- [ ] Confirmar com o professor/turma que nenhum outro grupo escolheu o mesmo software.
- [ ] Tabela com os três critérios e evidências numéricas: site/documentação oficial (real); versão atual, data do último release e empresas/órgãos que usam (em operação); usuários, downloads (PyPI, npm, Docker Hub), DB-Engines, Stack Overflow Survey, painéis gov.br etc. (alto impacto).
- [ ] Toda evidência com link e data de acesso.
- [ ] Um parágrafo justificando a escolha: por que dá para medir algo relevante nas três sprints.
'@

Add-Issue 'S01-02' 'A' 'Definir pergunta de pesquisa, GQM, hipóteses e 1ª versão das 7 categorias' `
  'docs/proposta.md' `
  'docs/software.md; docs/plano-analise.md (métricas e escalas); docs/protocolo-coleta.md' @'
- [ ] Pergunta de pesquisa em uma frase e caminho(s) escolhido(s); combinar caminhos (ex.: dados de operação + experimento) é valorizado.
- [ ] Objetivo GQM no template de Basili (analisar… com o propósito de… com respeito a… do ponto de vista de… no contexto de…), perguntas e métricas.
- [ ] Para cada métrica: entidade (produto, processo ou recurso), atributo interno/externo, medida direta/derivada e se pode ser "jogada" (Goodhart, Campbell, McNamara).
- [ ] Hipóteses H0/H1 (quando couber), variáveis independentes e dependentes, objetos/sujeitos e design do estudo.
- [ ] Primeira versão das 7 categorias da Aula 8 (natureza, objetivos, abordagem, procedimentos, tempo, controle, nível de evidência), cada uma com justificativa.
- [ ] Lista preliminar de ameaças à validade (conclusão, interna, construto, externa) com mitigação prevista.
- [ ] Consolidar a proposta da entrega Lab05S01 linkando os documentos dos demais.
'@

Add-Issue 'S01-03' 'B' 'Estruturar a pasta Lab-05 e o protocolo de coleta (ambiente e ética)' `
  'README.md, requirements.txt ou pyproject.toml, docs/protocolo-coleta.md, docs/dicionario-dados.md' `
  'docs/software.md; docs/proposta.md (métricas)' @'
- [ ] Estrutura `Lab-05/` com README (objetivo, como reproduzir), dependências com versão fixa e pastas `data/{piloto,raw,processed}`, `scripts/`, `analysis/`, `docs/`.
- [ ] Protocolo: o que é coletado, de onde, frequência, número de repetições/observações, versão exata do software, hardware, SO, rede, warm-up e ordem aleatória dos tratamentos (se houver).
- [ ] Regras de ética documentadas: sem teste de carga em terceiros, no máximo 1 requisição/s, termos de uso e robots.txt verificados (com link), nenhum dado pessoal; com participantes, termo de consentimento e contas fictícias.
- [ ] Dicionário de dados: coluna, tipo, unidade, escala e origem.
'@

Add-Issue 'S01-04' 'B' 'Implementar script de coleta e executar a coleta piloto' `
  'scripts/coleta*.py, data/piloto/, docs/piloto.md, tests/' `
  'docs/protocolo-coleta.md; docs/dicionario-dados.md' @'
- [ ] Script parametrizado (alvo, versão/configuração, repetições, semente) com limite de taxa e log de execução (timestamp, versão, ambiente).
- [ ] Reaproveitar o que couber do Lab01 (coleta via API, retry/backoff) e registrar o que foi reaproveitado.
- [ ] Coleta piloto pequena executada e versionada em `data/piloto/` com metadados.
- [ ] Validação dos dados: nulos, duplicatas, faixas plausíveis e unidades; problemas e ajustes no protocolo registrados em `docs/piloto.md`.
- [ ] Estimativa de tempo da coleta completa da S02.
'@

Add-Issue 'S01-05' 'C' 'Elaborar o plano de análise (escalas, testes de hipótese e tamanho do efeito)' `
  'docs/plano-analise.md' `
  'docs/proposta.md (métricas e hipóteses); variância do piloto (S01-06)' @'
- [ ] Para cada métrica: escala (nominal, ordinal, intervalar, razão) e estatísticas permitidas.
- [ ] Estatística descritiva e gráficos previstos por métrica.
- [ ] Teste de hipótese escolhido e justificado (pareado ou independente, paramétrico ou não, pressupostos e como verificá-los), α e correção para comparações múltiplas, se houver.
- [ ] Medida de tamanho do efeito (ex.: Cohen d, Cliff δ, r) e como interpretá-la.
- [ ] Número de repetições/observações justificado por poder, reaproveitando a simulação do Lab04 com a variância do piloto.
'@

Add-Issue 'S01-06' 'C' 'Analisar a coleta piloto e levantar fontes para o impacto' `
  'analysis/piloto.py ou .ipynb, analysis/figures/, docs/impacto-fontes.md' `
  'data/piloto/ (dados sintéticos até a coleta piloto); docs/plano-analise.md' @'
- [ ] Script/notebook reprodutível que lê `data/piloto/` e gera descritivas e 1–2 gráficos (título, eixos com unidade, legenda).
- [ ] Viabilidade: variância, distribuição, outliers; recomendação do número de repetições para a S02.
- [ ] Números públicos para estimar o impacto (usuários, acessos, consultas/dia, instalações) com link e data de acesso.
- [ ] Esboço da conta de impacto (seção 5 do enunciado) e do que **não** poderá ser afirmado (validade externa).
'@

function Get-Body($i) {
  $r = $i.Who
  @"
<!-- lab05-backlog:$($i.Id) -->

## Objetivo

$($i.Title)

- Papel: $($Roles[$r])
- Responsável: @$($Members[$r])
- Revisor: @$($Reviewers[$r])
- Milestone: **$($i.Milestone)**
- Artefatos (relativos a Lab-05): $($i.Artifacts)
- Depende de: $($i.Consumes)

Enquanto o insumo de outro integrante não chega, trabalhe com rascunho ou dados sintéticos e ajuste no merge.

## Critérios de aceite

$($i.Acceptance)

## Definition of Done

- [ ] Artefatos versionados; commits com referência ao número desta issue (#N).
- [ ] Revisão por outro integrante e cartão atualizado no Projects.

Fonte: enunciado do Lab05, seções 2–7.
"@
}

if ($Table) {
  '| ID | Issue | Responsável | Milestone |'
  '|---|---|---|---|'
  foreach ($i in $Issues) { "| $($i.Id) | $($i.Title) | @$($Members[$i.Who]) | $($i.Milestone) |" }
  return
}

"Repo: $Repo | Projects: $ProjectOwner/$ProjectNumber | Issues: $($Issues.Count) | Modo: $(if ($Apply) {'apply'} else {'dry-run'})"
if (-not $Apply) {
  foreach ($i in $Issues) { "`n---`n# [Lab05 $($i.Id)] $($i.Title)`n"; Get-Body $i }
  "`nPrévia concluída. Nenhuma chamada ao GitHub. Use -Apply para criar."
  return
}

function Invoke-Gh {
  $out = & gh @args
  if ($LASTEXITCODE -ne 0) { throw "gh $($args -join ' ') falhou (código $LASTEXITCODE)." }
  $out -join "`n"
}
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) { throw 'Instale o GitHub CLI (winget install GitHub.cli) e execute gh auth login -s project.' }

$project = Invoke-Gh project view $ProjectNumber --owner $ProjectOwner --format json | ConvertFrom-Json
$field = (Invoke-Gh project field-list $ProjectNumber --owner $ProjectOwner --limit 100 --format json | ConvertFrom-Json).fields |
  Where-Object { $_.name -eq 'Status' }
$norm = { param($s) ($s -replace '[\s_-]', '').ToLower() }
$option = $field.options | Where-Object { (& $norm $_.name) -eq (& $norm $Status) }
if (-not $option) { throw "Opção '$Status' não encontrada no campo Status. Disponíveis: $(($field.options.name) -join ', '). Use -Status." }

$milestones = (Invoke-Gh api --paginate "repos/$Repo/milestones?state=all&per_page=100" --jq '.[].title') -split "`n"
if ($milestones -notcontains 'Lab05S01') { Invoke-Gh api "repos/$Repo/milestones" -f title=Lab05S01 | Out-Null; 'Milestone criado: Lab05S01' }

$existing = @{}
foreach ($e in (Invoke-Gh issue list --repo $Repo --state all --limit 1000 --json 'url,body' | ConvertFrom-Json)) {
  if ($e.body -match '<!-- lab05-backlog:([A-Z0-9-]+) -->') { $existing[$Matches[1]] = $e.url }
}
$items = @{}
foreach ($it in (Invoke-Gh project item-list $ProjectNumber --owner $ProjectOwner --limit 1000 --format json | ConvertFrom-Json).items) {
  if ($it.content.url) { $items[$it.content.url] = $it.id }
}

$bodyFile = [IO.Path]::GetTempFileName()
try {
  foreach ($i in $Issues) {
    if ($existing.ContainsKey($i.Id)) {
      $url = $existing[$i.Id]; "Reutilizada $($i.Id): $url"
    } else {
      [IO.File]::WriteAllText($bodyFile, (Get-Body $i), (New-Object System.Text.UTF8Encoding $false))
      $url = (Invoke-Gh issue create --repo $Repo --title "[Lab05 $($i.Id)] $($i.Title)" --body-file $bodyFile `
        --assignee $Members[$i.Who] --milestone $i.Milestone).Trim()
      "Criada $($i.Id): $url"
    }
    if (-not $items.ContainsKey($url)) {
      $itemId = Invoke-Gh project item-add $ProjectNumber --owner $ProjectOwner --url $url --format json --jq '.id'
      Invoke-Gh project item-edit --id $itemId.Trim() --project-id $project.id --field-id $field.id `
        --single-select-option-id $option.id | Out-Null
      "  adicionada ao Projects em '$($option.name)'"
    }
  }
} finally { Remove-Item $bodyFile -ErrorAction SilentlyContinue }
"`nConcluído."
