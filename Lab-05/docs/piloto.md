# Lab05 — Coleta piloto

Issue: S01-04 (#184). Responsável: @gustavoprehl. Revisor: @lucasrsnd.

> **Status:** piloto **de fumaça**, contra um servidor local, porque o software ainda não foi escolhido (#181). O objetivo dele é validar o coletor, o protocolo e o contrato com a análise sem enviar requisições a terceiros. **Os números abaixo não são resultados do estudo.** Com o software definido, o piloto real repete a seção 6 com outro arquivo de alvos.

## 1. Execução

| Item | Valor |
|---|---|
| Alvo | [`scripts/servidor_local.py`](../scripts/servidor_local.py) em `127.0.0.1:8765` |
| Tratamentos | `A_sem_cache` (gera a página a cada requisição) × `B_com_cache` (mesma página, cache em memória) |
| Unidades | 20 páginas (`p01`–`p20`), custo de geração crescente |
| Repetições | 5 por (unidade, tratamento) → 200 observações, 600 linhas no CSV |
| Aquecimento | 3 por tratamento + 1 por (unidade, tratamento) = 46 requisições descartadas |
| Intervalo / semente | 0,2 s (permitido só em host local) / 42 |
| Ambiente | Windows 11, AMD64 (AMD Family 23), Python 3.13, `requests` 2.34.2, loopback |
| Duração | 49 s, 246 requisições, 0 falhas, 0 novas tentativas |
| Arquivos | [`data/piloto/piloto_local_20261126T015135Z.*`](../data/piloto/) (`.csv`, `.log.jsonl`, `.meta.json`) |

Comando:

```powershell
python scripts/coleta.py scripts/alvos/piloto_local.json --repeticoes 5 --aquecimento 3 --aquecer-unidades --intervalo 0.2 --saida data/piloto --rede "loopback (127.0.0.1)"
```

## 2. Validação dos dados

| Checagem | Resultado |
|---|---|
| Nulos | 0 |
| Duplicatas (tratamento, unidade, repeticao, metrica) | 0 |
| Negativos / acima do timeout | 0 / 0 |
| `ttfb_ms` > `tempo_ms` | 0 |
| Completude | 200 / 200 = 100% |
| Controle `tamanho_kb` | idêntico entre tratamentos em todas as unidades (mesmo conteúdo, como esperado) |
| Contrato com a análise | `analise.descritiva.validate` aceitou o CSV sem conversão; `python -m analise.piloto ... --pareado` rodou completo |

## 3. Problemas encontrados e ajustes no protocolo

1. **Cache frio na repetição 1.** Na primeira execução (aquecimento só na primeira unidade), a mediana de `B_com_cache` foi 28,3 ms na repetição 1 e cerca de 15 ms nas repetições 2–5. Cada unidade ainda não estava no cache na primeira vez em que era medida. Isso inflaria a variância de B e misturaria "cache frio" com o tratamento.
   **Ajuste:** opção `--aquecer-unidades` (uma requisição descartada por unidade e tratamento) e protocolo atualizado (seção 3, passo 3). Na nova execução, as medianas de B ficaram entre 15,0 e 17,1 ms em todas as repetições. A primeira execução foi descartada.
2. **Métrica de controle sem variação.** `tamanho_kb` é idêntico entre os tratamentos (é a mesma página). O Wilcoxon devolve p = NaN, mas `analise.testes.holm` trata o NaN como p pequeno e o `comparacoes.csv` marca `rejeita_h0 = True` com `p_holm ≈ 1e-6`. **Para o @lucasrsnd (#185):** excluir p-valores NaN da correção de Holm (deixar `p_holm` NaN e `rejeita_h0` False). **No protocolo:** `tamanho_kb` é métrica de controle e fica fora dos testes de hipótese quando os tratamentos servem o mesmo conteúdo.
3. **Console do Windows (cp1252).** Os caracteres `×` e `≈` quebravam a saída do coletor. Corrigido com saída em UTF-8. A saída da análise aparece com acentos trocados no console, mas os CSVs estão corretos. Para ver a saída limpa: `$env:PYTHONIOENCODING = "utf-8"`.

## 4. Descritivas e viabilidade (só do pipeline)

| Métrica | Tratamento | n | Mediana (ms) | IQR (ms) | Shapiro p |
|---|---|---|---|---|---|
| `tempo_ms` | A_sem_cache | 100 | 33,1 | 17,8 | 0,13 |
| `tempo_ms` | B_com_cache | 100 | 16,2 | 5,6 | < 0,001 |
| `ttfb_ms` | A_sem_cache | 100 | 31,4 | 18,0 | 0,13 |
| `ttfb_ms` | B_com_cache | 100 | 14,6 | 5,1 | < 0,001 |

- A análise pareada (mediana das 5 repetições por unidade) detectou o efeito do cache (t pareado, d_z ≈ 1,7). A simulação de poder pediu **n = 10 unidades** para 80%. O pipeline produz a recomendação de repetições que a S02 precisa.
- B é assimétrico (Shapiro rejeita), como o plano de análise prevê para tempos. A árvore de testes cobre esse caso.
- Com um alvo remoto, a variância deve ser bem maior (rede, carga do servidor, CDN). O n da S02 deve sair do **piloto real**, não deste.

Saídas da análise (não versionadas, regeneráveis): `analysis/resultados/piloto_local/`.

## 5. Estimativa de tempo da coleta completa (S02)

Com host externo o intervalo é de 1 s. Com latência abaixo de 1 s, a duração é praticamente o número de requisições, em segundos:

requisições = 2 tratamentos × unidades × repetições + aquecimento (3 × 2 + 2 × unidades)

| Unidades | Repetições | Requisições | Duração aproximada |
|---|---|---|---|
| 20 | 10 | 446 | 7,5 min |
| 20 | 30 | 1.246 | 21 min |
| 50 | 30 | 3.106 | 52 min |

Com duas execuções em horários diferentes (protocolo, seção 4), a coleta da S02 cabe em uma tarde mesmo no cenário maior. Recalcular com `--estimar --latencia-ms <mediana do piloto real>` quando o alvo for conhecido. Se a latência passar de 1 s, ela passa a dominar a conta.

## 6. Checklist do piloto real (quando #181 e #182 fecharem)

- [ ] Criar `scripts/alvos/<estudo>.json` a partir de `modelo_externo.json`, com a versão exata do software.
- [ ] Preencher a tabela de ética do protocolo (termos de uso, robots.txt, links e datas).
- [ ] Rodar `--estimar`, depois o piloto com `--repeticoes 5 --aquecer-unidades` e `--rede` preenchido.
- [ ] Repetir as seções 2–4 deste documento com os dados reais e passar o CSV para a análise (#186).
- [ ] Atualizar a seção 5 com a latência medida.
