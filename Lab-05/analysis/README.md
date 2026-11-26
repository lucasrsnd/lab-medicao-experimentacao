# Lab05 — Análise

Implementa o [plano de análise](../docs/plano-analise.md): validação dos dados, estatística descritiva, escolha do teste de hipótese, tamanho do efeito, correção de Holm e poder × tamanho da amostra por Monte Carlo (reaproveitado do Lab04).

| Módulo | Função |
|---|---|
| `analise/descritiva.py` | `validate(df)`, `summarize(df)` |
| `analise/testes.py` | `compare(df, metrica, pareado, metodo)`, `compare_all(df, pareado)`, medidas de efeito, `holm` |
| `analise/poder.py` | `fit`, `params_from_pilot`, `power_by_n`, `required_n` |
| `analise/piloto.py` | CLI que gera tabelas e gráficos da coleta piloto |
| `analise/sintetico.py` | dados sintéticos no formato longo até a coleta real |

## Uso

Rodar a partir de `Lab-05/analysis`:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

pytest                                                      # testes
python -m analise.sintetico fixtures/piloto_sintetico.csv   # dados de exemplo
python -m analise.piloto fixtures/piloto_sintetico.csv --saida resultados/piloto --pareado
```

Com os dados reais da coleta piloto (#184), troque o CSV por `../data/piloto/<arquivo>.csv`. Use `--pareado` quando a mesma unidade for medida em todos os tratamentos.

Saídas em `--saida`: `descritivas.csv`, `comparacoes.csv`, `poder.csv`, `n_necessario.csv` e `figuras/*.png`.
