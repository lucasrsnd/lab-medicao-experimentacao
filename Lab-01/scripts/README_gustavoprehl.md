# gustavoprehl - extração e validação (RQ01 + RQ02)

Responsável: `gustavoprehl`
Issues: RQ01 (idade do repositório) e RQ02 (PRs aceitas) · `sprint:S01`
Issue: Validação individual RQ01+RQ02 em 1000 repos + hipótese informal · `sprint:S02` (#10)

## Como rodar

```
cd Lab-01
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install -e .          # instala config/src em modo editavel
copy .env.example .env    # depois editar e colar o token
python scripts\rq01_idade.py
python scripts\rq02_prs_aceitas.py
```

---

## RQ01 — idade do repositório

**Métrica:** idade do repositório = hoje - `createdAt` (campo GraphQL), em anos.

### Validação

- [x] Amostra rodada: 10 repositórios
- [x] Nenhum `createdAt` nulo na amostra
- [x] Idades calculadas fazem sentido (conferido `codecrafters-io/build-your-own-x` e `sindresorhus/awesome` manualmente na página do GitHub, batem)
- [x] Observações / inconsistências encontradas: nenhuma. `openclaw/openclaw` deu idade 0.71 anos (criado em 2025-11-24), o que é coerente, repositório recente com alto número de estrelas.

| repositório | estrelas | criado em | idade (anos) |
|---|---|---|---|
| codecrafters-io/build-your-own-x | 538254 | 2018-05-09 | 8.25 |
| sindresorhus/awesome | 494202 | 2014-07-11 | 12.08 |
| public-apis/public-apis | 455280 | 2016-03-20 | 10.39 |
| freeCodeCamp/freeCodeCamp | 453729 | 2014-12-24 | 11.62 |
| EbookFoundation/free-programming-books | 394078 | 2013-10-11 | 12.83 |
| openclaw/openclaw | 385751 | 2025-11-24 | 0.71 |
| nilbuild/developer-roadmap | 364060 | 2017-03-15 | 9.40 |
| donnemartin/system-design-primer | 362892 | 2017-02-26 | 9.45 |
| jwasham/coding-interview-university | 358308 | 2016-06-06 | 10.18 |
| vinta/awesome-python | 313188 | 2014-06-27 | 12.12 |

### Trecho de query pronto para integração

Campo relevante dentro do `search(...) { nodes { ... on Repository { } } }` (ver `src/queries`):

```graphql
createdAt
```

Cálculo de idade fica em `extract_rq01_idade_anos()`, em `src/metrics`.

---

## RQ02 - PRs aceitas

**Métrica:** total de pull requests aceitas (merged) por repositório.

### Validação

- [x] Amostra rodada: 10 repositórios
- [x] `prs_aceitas` presente e não-negativo em todos
- [x] Valores fazem sentido: projetos com equipe grande/muito ativa (`freeCodeCamp` 29.056, `openclaw` 23.604) têm ordens de grandeza a mais de PRs aceitas que listas curadas (`awesome-python` 738, `system-design-primer` 210), coerente com a natureza de cada tipo de projeto.
- [x] Observações / inconsistências encontradas: nenhuma.

| repositório | estrelas | PRs aceitas |
|---|---|---|
| codecrafters-io/build-your-own-x | 538265 | 157 |
| sindresorhus/awesome | 494209 | 700 |
| public-apis/public-apis | 455282 | 2106 |
| freeCodeCamp/freeCodeCamp | 453732 | 29056 |
| EbookFoundation/free-programming-books | 394078 | 7416 |
| openclaw/openclaw | 385757 | 23604 |
| nilbuild/developer-roadmap | 364061 | 4387 |
| donnemartin/system-design-primer | 362899 | 210 |
| jwasham/coding-interview-university | 358310 | 415 |
| vinta/awesome-python | 313203 | 738 |

### Trecho de query pronto para integração

Campo relevante dentro do `search(...) { nodes { ... on Repository { } } }` (ver `src/queries`):

```graphql
pullRequests(states: MERGED) {
  totalCount
}
```

Extração feita em `extract_rq02_prs_aceitas()`, em `src/metrics`.

---

## S02 - validação em 1000 repos + hipótese informal (#10)

Rodado com `python scripts/validacao_s02_rq01_rq02.py` sobre
`data/raw/repositorios_s02.csv` (**998/1000 repositórios** - ver nota no commit da
#21 sobre o motivo de não ser exatamente 1000: comportamento da Search API do
GitHub em coletas longas, não é falha nos dados).

### RQ01 - idade do repositório

| | |
|---|---|
| Valores ausentes | 0 / 998 (0%) |
| Média | 7.65 anos |
| Mediana | 7.72 anos |
| Desvio padrão | 4.52 anos |
| Min / Max | 0.00 / 18.34 anos |
| Outliers (IQR 1.5x) | 0 (0%) — distribuição sem cauda pesada |

Mais antigos: `rails/rails` (18.34), `git/git` (18.06), `jekyll/jekyll` (17.81),
`redis/redis` (17.39), `jquery/jquery` (17.36) — todos projetos fundacionais de
longa data, como esperado.

Mais novos: `deepseek-ai/deepseek-harness` (0.00), `DietrichGebert/ponytail` (0.17),
`odysseus-dev/odysseus` (0.20) repositórios muito recentes que já acumularam
estrelas suficientes pra entrar no top, a maioria ligada à onda de IA.

**Hipótese informal:** sistemas populares tendem a ser maduros, mas não
uniformemente, a mediana (7.7 anos) confirma a hipótese original, e a ausência de
outliers pela regra do IQR mostra que a maior parte da distribuição é razoavelmente
concentrada (a maturidade é a norma, não a exceção). Ao mesmo tempo, o mínimo em
0 anos indica que popularidade extrema *pode* ser alcançada quase instantaneamente
(hype, viralização, ligação com tendências como IA), a hipótese "populares =
antigos" vale em geral, mas tem uma minoria genuína de exceções recentes que a
mediana sozinha esconde.

### RQ02 - PRs aceitas

| | |
|---|---|
| Valores ausentes | 0 / 998 (0%) |
| Média | 4211.5 |
| Mediana | 768.0 |
| Desvio padrão | 10633.2 |
| Min / Max | 0 / 103014 |
| Outliers (IQR 1.5x) | 123 (12.32%) — cauda bem pesada |

Média **5.5x maior que a mediana** e 12.3% de outliers pela regra do IQR (bem acima
do ~1% esperado numa distribuição próxima da normal) confirmam uma distribuição
fortemente assimétrica à direita: poucos projetos com contribuição externa gigante
puxam a média pra cima, enquanto a maioria dos repositórios populares recebe uma
fração disso.

Maiores: `firstcontributions/first-contributions` (103014  repositório cujo
propósito literal é ensinar iniciantes a abrir sua primeira PR, então o número faz
sentido por natureza), `llvm/llvm-project` (96386), `elastic/elasticsearch` (95266),
`getsentry/sentry` (91020), `home-assistant/core` (89919) todos projetos de
software ativo com base de contribuidores muito grande.

Menores (0 PRs aceitas): `awesome-selfhosted/awesome-selfhosted`,
**`torvalds/linux`**, `DigitalPlatDev/FreeDomain`, `chrislgarry/Apollo-11`,
`gorhill/uBlock`.

**Ressalva importante pro relatório final:** `torvalds/linux` com 0 PRs aceitas não
significa que o kernel Linux não recebe contribuição externa, significa que o
desenvolvimento do kernel não usa o mecanismo nativo de Pull Request do GitHub
(patches são enviados por lista de e-mail). A métrica `pullRequests(states: MERGED)`
mede um canal específico de contribuição, não "contribuição externa" em geral,
projetos populares que usam workflow fora do GitHub vão aparecer artificialmente
como "sem contribuição" mesmo sendo extremamente colaborativos. Vale citar essa
limitação de métrica na discussão hipótese vs. resultado do relatório final.

**Hipótese informal:** sistemas populares recebem, em geral, mais contribuição
externa que projetos comuns (mediana de 768 PRs aceitas já é um número expressivo),
mas "populares" não é sinônimo de "alta contribuição" de forma uniforme — o tipo de
projeto importa mais que a popularidade pura: projetos com propósito colaborativo
explícito ou base de código ativa (`llvm`, `elasticsearch`, `sentry`) recebem ordens
de grandeza mais PRs que listas curadas ou projetos com workflow externo ao GitHub,
mesmo quando estes têm popularidade (estrelas) comparável ou maior.
