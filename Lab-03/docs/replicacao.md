# Replicação cruzada (entrega final)

Estado: **a replicação não foi realizada**, porque o sorteio do grupo a
replicar não aconteceu. Este documento descreve a ferramenta de comparação que
ficou pronta. Não existe resultado de replicação, e nada aqui deve ser lido
como tal.

## Comparação original × replicado (FINAL-02, #130)

```powershell
copy config\replicacao-mapeamento.exemplo.json replication\mapeamento.json   # ajustar colunas do grupo autor
python -m lab03.replication.compare `
  --original replication/original.csv `
  --replicated replication/replicado.csv `
  --mapping replication/mapeamento.json `
  --output-dir replication/comparacao --sample-size 30
```

O mapeamento traduz as colunas do CSV do grupo autor e do CSV produzido na
replicação para nomes lógicos comuns. Assim, a ferramenta não presume o
esquema do outro grupo. Comparar sempre a **mesma variante** (por exemplo, o
lead time por release com o lead time por release). Se o grupo autor não
publicar uma variante, ela fica fora do mapeamento e isso é registrado no
relato.

| Situação | Tratamento | Onde aparece |
|---|---|---|
| Repositório só em um lado | Não comparado | `coverage.only_original` / `only_replicated` |
| Menos de 30 em comum | Execução parcial, com n comparável por métrica | `coverage.partial`, `n_comparable` |
| Original = 0 e replicado ≠ 0 | Δ relativo indefinido, usa Δ absoluto | status `original_zero` |
| Ambos = 0 | Δ = 0 (concordância) | status `ambos_zero` |
| Valor ausente (vazio, NA, NaN, null) | Excluído, nunca vira zero | `ausente_original` / `ausente_replicado` |
| Categoria DORA | % igual entre os que têm as duas, mais a matriz de mudanças | `categories` |

Δ relativo = (replicado − original) / |original|. A tolerância padrão de
concordância é |Δ relativo| ≤ 5% (`--tolerance`).

### Leitura das divergências

Antes de abrir uma issue de divergência (FINAL-04, #132), separe o que é
esperado do que indica defeito:

- **Data de coleta:** se a janela é relativa à data de execução, releases e
  runs novos mudam frequência e CFR. Compare primeiro a janela registrada nos
  dois lados.
- **Dados mutáveis na API:** releases apagadas ou editadas, runs expirados
  (retenção do Actions), contribuidores e estrelas variam com o tempo.
- **Configuração:** token ausente ou limite de requisições pode truncar
  paginação, e tetos de runs/releases mudam denominadores. Os logs da
  execução (FINAL-01) devem registrar isso.
- **Definição:** uma diferença sistemática em toda a amostra, sempre no mesmo
  sentido, sugere fórmula ou variante diferente da documentada. Esse é o caso
  que justifica uma issue no repositório autor, com valores, repositórios
  afetados e comando reproduzível.

## Não realizado

Sem sorteio, não foram feitas: a execução de um pipeline externo em 30
repositórios (FINAL-01, #129), as issues de execução e de divergência no
repositório autor (FINAL-03, #131, e FINAL-04, #132) nem a comparação com dados
reais. O artigo registra isso na seção "Replicação cruzada".
