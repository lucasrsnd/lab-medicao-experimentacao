# Dados reais — Apache Ant 1.7 (PROMISE)

| Item | Valor |
|---|---|
| Dataset | `ant-1.7` do repositório PROMISE / tera-PROMISE (Jureczko & Madeyski, métricas CK por classe Java) |
| Obtido de | <https://github.com/klainfo/DefectData> (`inst/extdata/terapromise/ck/ant-1.7.csv`), commit `e65993d` |
| Arquivo bruto | `raw/ant-1.7.csv` (745 classes; 742 com LOC > 0) |
| Licença | MIT (pacote DefectData, de Chakkrit Tantithamthavorn); os dados originais são públicos no PROMISE |
| Coletado em | 2026-11-02, por download direto |

## Por que este dataset

O enunciado sugere NASA MDP ou PROMISE. Os arquivos NASA MDP mais usados trazem só defeito booleano. O
`ant-1.7` traz `bug` como **contagem** de defeitos por classe, além de `loc`, o que permite o par
LOC × nº de defeitos do P5.

## Como a amostra foi gerada

- Colunas usadas do bruto: nome da classe (`module_id`), `loc` e `bug` (renomeado `defects`).
- Classes com `loc = 0` foram descartadas (3 de 745), porque a lognormal exige LOC > 0.
- `src/lab04/real_data.py::load_sample()` sorteia **30 classes sem reposição** com
  `numpy.random.default_rng(42)` e grava `amostra.csv` (`module_id, loc, defects`).
- Reprodução: `python -m lab04.real_data` (regera `amostra.csv` e `outputs/real_params.json`).

## Resumo da população (742 classes) × amostra (30)

| | População | Amostra |
|---|---|---|
| Pearson r (LOC × defeitos) | 0,65 | 0,62 |
| Spearman ρ | 0,49 | 0,56 |
| Proporção de classes sem defeito | 77,6% | 73,3% |

Ambas as variáveis são muito assimétricas, com cauda à direita e muitos zeros nos defeitos.
Isso motiva a lognormal para LOC e a binomial negativa para defeitos.
