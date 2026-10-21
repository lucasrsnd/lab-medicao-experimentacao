# Integração da 2ª parte da coleta (183 → 300 repositórios)

> **Status (20/10/2026): integrada.** A `parte2.json` (117 repositórios,
> `slice = [183, 300]`, SHA-256 `cb8a7398…`) foi unida à 1ª parte com
> `lab03.merge` e `selecao-amostra-revisada.json`. Conferido: 300 repositórios
> únicos, ordem da seleção, mesma `window` e `criteria`, heurística v2 em todos,
> `collection_validation.status = complete`. Hashes do JSON: 183 antes
> `3e66a078…`, 300 depois `bbc65239…`. Hashes do `.gz`: antes `315e063b…`, depois
> `4e648213…` (66 MB). O dataset de 300 tem `collected_at` de 13/10, e não é o de
> 15/10 (`87656c1c…`), então a `labels/reamostragem-v2/` segue não vinculada.
> O texto abaixo é o guia original.

**Responsável:** Lucas, que tem a coleta local (o cache registrado no dataset
aponta para `C:\Users\Lucas\...\Lab-03\data\cache_estudo.sqlite3`).
**Contexto:** o dataset versionado, `data/amostra_completa.json.gz`, tem só a
1ª parte da seleção (`pilot_sample.slice = [0, 183]`). A seleção revisada,
`data/selecao-amostra-revisada.json`, tem 300 repositórios, com 17
substituições nos índices 183 a 299. A `labels/reamostragem-v2/` foi sorteada
de um dataset com 300 repositórios (SHA-256
`87656c1c9637fd1e938f1d4e2775be55e29df701a94fa2268096f71ec623fa52`,
`collected_at` em 2026-10-15T12:41:13Z). Esse arquivo não está no GitHub.

O artigo, o README e `analysis/` estão hoje coerentes com 183 repositórios e
declaram essa limitação. Só substitua isso se a integração for completa e
validada.

## Prompt para o Claude Code (copiar e colar, na raiz do repositório)

```text
Contexto: repositório lab-medicao-experimentacao, pasta Lab-03 (Python 3.12+,
pacote lab03). O dataset versionado data/amostra_completa.json.gz tem só a 1ª
parte da coleta (183 repositórios, pilot_sample.slice = [0, 183]). Preciso
integrar a 2ª parte (índices 183 a 299 de data/selecao-amostra-revisada.json,
117 repositórios) para chegar aos 300 repositórios do protocolo. Leia antes
Lab-03/docs/integracao-parte2.md, Lab-03/docs/protocolo.md (seção "Janela,
limites e unidades") e Lab-03/analysis/README.md.

Regras: não invente nem complete dados. Não altere rótulos em labels/. Não
mude janela, critérios ou heurística. Se algo não fechar, pare e me mostre o
problema em vez de contornar. O token do GitHub fica só em $env:GITHUB_TOKEN,
nunca em arquivo ou commit.

1. Atualize a branch: git checkout dev_LucasResende; git pull origin main.

2. Localize a coleta. Procure, dentro e fora do repositório, por
   amostra_completa*.json*, parte*.json* e cache_estudo.sqlite3. Para cada
   JSON encontrado, informe len(repositories), collected_at, window,
   pilot_sample e o SHA-256 dos bytes do arquivo. Considere "o dataset de
   300" um arquivo com 300 repositórios, ou com SHA-256 87656c1c…, ou com
   collected_at em 2026-10-15. Considere "a parte 2" um arquivo com
   pilot_sample.slice = [183, 300]. Me mostre a tabela antes de seguir.

3. Monte o dataset de 300, conforme o que existir:
   a) Se existir o dataset de 300: confirme que os 183 primeiros
      repositórios, na ordem da seleção, são os mesmos do .gz atual, e que
      window e criteria são iguais.
   b) Se existir só a parte 2: descompacte o .gz atual em data/parte1.json e
      rode
      python -m lab03.merge data/parte1.json data/parte2.json --selection data/selecao-amostra-revisada.json --output data/amostra_completa.json
   c) Se existir só o cache: tente regerar a parte 2 a partir dele, sem
      refazer a busca:
      python -m lab03 --config config/estudo.json --full --selection data/selecao-amostra-revisada.json --slice 183:300 --cache <caminho do cache_estudo.sqlite3> --output data/parte2.json
      Confira no JSON que cache.misses é 0 ou baixo. Se precisar de muitas
      requisições à API, pare e me avise. Depois siga o passo (b).
   d) Se nada existir: pare. Nesse caso o artigo fica com 183, como já está.

4. Valide. O merge não pode reclamar de parte parcial nem de repositório
   repetido. Confira: 300 repositórios únicos; mesma ordem de
   selecao-amostra-revisada.json; mesma window e criteria da parte 1; todos
   com report.delivery_failure_rate.heuristic_version == "v2". Rode
   python -m pytest e garanta que tudo passa, com cobertura de pelo menos 80%.

5. Compacte o novo dataset em data/amostra_completa.json.gz, substituindo o
   atual. O arquivo precisa ter menos de 100 MB por causa do limite do
   GitHub. Registre o SHA-256 antigo e o novo, tanto do .gz quanto do JSON
   descompactado.

6. Refaça todas as análises:
   python -m lab03.analysis.base
   python -m lab03.analysis.rq01_rq02
   python -m lab03.analysis.rq03_rq04
   python -m lab03.analysis.c1_reference
   python -m lab03.analysis.rq05
   python -m lab03.analysis.rq06
   python -m lab03.analysis.cfr_b_validation
   Me mostre um antes/depois dos números principais: n, medianas e IQR das
   RQ01 a RQ04, distribuição C1, ρ e p (Holm) da RQ05, ε² e p (Holm) da RQ06,
   e as releases avaliadas, a precisão, o recall e o F1 da validação.

7. Validação do CFR (b): com 300 repositórios, mais releases da 1ª rodada da
   amostra-ouro (labels/amostra_ouro_*) devem entrar no snapshot. Até agora
   eram 178 de 283. Se o SHA-256 do novo JSON for 87656c1c…, a
   labels/reamostragem-v2/ fica vinculada ao dataset. Mesmo assim ela
   continua sem rótulos: não preencha nada.

8. Atualize o texto com os novos números, sem mudar a interpretação sem me
   mostrar antes:
   - Lab-03/article/main.tex: abstract e resumo;
   - Lab-03/article/sections/metodologia.tex: subseção "Amostra analisada",
     que hoje diz 183 de 300;
   - Lab-03/article/sections/resultados.tex: todas as tabelas e todos os
     números das RQ01 a RQ06, da C1 e da validação do CFR (b), e o parágrafo
     sobre "183 repositórios";
   - Lab-03/article/sections/introducao.tex: menções a 183;
   - Lab-03/README.md, seção "Sprint 03", "Cobertura";
   - Lab-03/analysis/README.md: resultados citados das RQ05, RQ06 e da
     validação.
   Procure "183", "172", "178" e "37 repositórios" e trate cada ocorrência.

9. Faça o commit na dev_LucasResende, referenciando as issues #126 e #136,
   com o antes/depois dos hashes na mensagem. Abra um PR para a main e
   marque @gustavoprehl e @DaviSantos23 como revisores.
```

## Se não houver tempo

Nada precisa ser feito: a entrega com 183 repositórios está consistente e
declara a limitação na Metodologia (Seção 2.1 do artigo). Só não misture
números de 183 com os de 300. Ou se atualiza tudo, ou nada.
