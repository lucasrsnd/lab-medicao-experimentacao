"""Coleta parametrizada do Lab05: mede requisições HTTP por tratamento e grava no formato longo.

Issue: S01-04 (#184). Protocolo: ../docs/protocolo-coleta.md. Dicionário: ../docs/dicionario-dados.md.

Cada execução lê um arquivo de alvos (JSON) com os tratamentos (URL com ``{unidade}``) e as
unidades, mede cada (tratamento, unidade, repetição) em ordem aleatória e grava três arquivos:

- ``<prefixo>.csv``: observações no formato longo (tratamento, unidade, repeticao, metrica, valor),
  o contrato de ../analysis (docs/plano-analise.md, seção 1);
- ``<prefixo>.log.jsonl``: uma linha por requisição, inclusive aquecimento e falhas;
- ``<prefixo>.meta.json``: versão do software, ambiente, parâmetros, semente e validação.

Regras de ética aplicadas no código: no mínimo 1 s entre requisições a hosts externos,
robots.txt respeitado e nenhum dado pessoal gravado (só tempos, tamanhos e status).

Uso (a partir de Lab-05):
    python scripts/coleta.py scripts/alvos/piloto_local.json --repeticoes 5 --saida data/piloto
    python scripts/coleta.py scripts/alvos/piloto_local.json --estimar --repeticoes 30
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import random
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable
from urllib import robotparser
from urllib.parse import urlsplit

import pandas as pd
import requests

COLUNAS = ("tratamento", "unidade", "repeticao", "metrica", "valor")
METRICAS = ("tempo_ms", "ttfb_ms", "tamanho_kb")
HOSTS_LOCAIS = {"localhost", "127.0.0.1", "::1"}
INTERVALO_MIN_EXTERNO_S = 1.0  # ética: no máximo 1 requisição/s em sistemas de terceiros
USER_AGENT = "PUC-Minas-LabExperimentacao-Lab05/1.0 (pesquisa academica; 1 req/s)"

# Retry com backoff exponencial, adaptado de Lab-01/src/github_client (run_query).
MAX_TENTATIVAS = 4
ESPERA_BASE_S = 2.0


@dataclass
class Alvos:
    nome: str
    software: dict
    tratamentos: dict[str, str]
    unidades: list[str]
    headers: dict[str, str] = field(default_factory=dict)
    timeout_s: float = 30.0

    @classmethod
    def ler(cls, caminho: Path) -> "Alvos":
        bruto = json.loads(caminho.read_text(encoding="utf-8"))
        alvos = cls(
            nome=bruto["nome"],
            software=bruto.get("software", {}),
            tratamentos=bruto["tratamentos"],
            unidades=[str(u) for u in bruto["unidades"]],
            headers=bruto.get("headers", {}),
            timeout_s=float(bruto.get("timeout_s", 30.0)),
        )
        if len(alvos.tratamentos) < 2:
            raise ValueError("São necessários pelo menos 2 tratamentos.")
        if not alvos.unidades or len(set(alvos.unidades)) != len(alvos.unidades):
            raise ValueError("A lista de unidades deve ser não vazia e sem repetições.")
        for nome, url in alvos.tratamentos.items():
            if "{unidade}" not in url:
                raise ValueError(f"A URL do tratamento {nome!r} precisa conter '{{unidade}}'.")
        return alvos

    def url(self, tratamento: str, unidade: str) -> str:
        return self.tratamentos[tratamento].format(unidade=unidade)

    def hosts(self) -> set[str]:
        return {urlsplit(u).hostname or "" for u in self.tratamentos.values()}


def eh_local(host: str) -> bool:
    return host in HOSTS_LOCAIS


def intervalo_efetivo(alvos: Alvos, pedido_s: float) -> float:
    """Respeita o mínimo de 1 s quando algum host não é local."""
    if all(eh_local(h) for h in alvos.hosts()):
        return max(pedido_s, 0.0)
    return max(pedido_s, INTERVALO_MIN_EXTERNO_S)


def verificar_robots(alvos: Alvos, sessao: requests.Session) -> dict[str, bool]:
    """Confere robots.txt de cada host externo para todas as URLs; hosts locais são liberados."""
    permitido: dict[str, bool] = {}
    for tratamento in alvos.tratamentos:
        for unidade in alvos.unidades:
            url = alvos.url(tratamento, unidade)
            partes = urlsplit(url)
            if eh_local(partes.hostname or ""):
                permitido[url] = True
                continue
            base = f"{partes.scheme}://{partes.netloc}"
            parser = _robots_cache.get(base)
            if parser is None:
                parser = robotparser.RobotFileParser()
                try:
                    resp = sessao.get(f"{base}/robots.txt", timeout=alvos.timeout_s)
                    parser.parse(resp.text.splitlines() if resp.status_code == 200 else [])
                except requests.RequestException:
                    parser.parse([])  # sem robots.txt acessível: nenhuma restrição declarada
                _robots_cache[base] = parser
            permitido[url] = parser.can_fetch(USER_AGENT, url)
    return permitido


_robots_cache: dict[str, robotparser.RobotFileParser] = {}


def plano_execucao(alvos: Alvos, repeticoes: int, aquecimento: int, semente: int,
                   aquecer_unidades: bool = False) -> list[tuple[str, str, str, int]]:
    """Lista ordenada de (fase, tratamento, unidade, repeticao).

    Aquecimento (descartado): ``aquecimento`` requisições por tratamento na primeira unidade e,
    com ``aquecer_unidades``, mais uma por (unidade, tratamento), para que a repetição 1 não
    pague cache frio (achado do piloto, docs/piloto.md).
    Medição: para cada repetição, unidades em ordem aleatória e, dentro de cada unidade,
    tratamentos em ordem aleatória (contrabalanceia cache e deriva temporal).
    """
    rng = random.Random(semente)
    plano: list[tuple[str, str, str, int]] = []
    for i in range(aquecimento):
        for tratamento in rng.sample(list(alvos.tratamentos), k=len(alvos.tratamentos)):
            plano.append(("aquecimento", tratamento, alvos.unidades[0], i + 1))
    if aquecer_unidades:
        for unidade in rng.sample(alvos.unidades, k=len(alvos.unidades)):
            for tratamento in rng.sample(list(alvos.tratamentos), k=len(alvos.tratamentos)):
                plano.append(("aquecimento", tratamento, unidade, 0))
    for rep in range(1, repeticoes + 1):
        for unidade in rng.sample(alvos.unidades, k=len(alvos.unidades)):
            for tratamento in rng.sample(list(alvos.tratamentos), k=len(alvos.tratamentos)):
                plano.append(("medicao", tratamento, unidade, rep))
    return plano


def medir(sessao: requests.Session, url: str, headers: dict, timeout: float) -> dict:
    """Uma requisição GET com retry. Devolve métricas ou o erro da última tentativa."""
    ultimo_erro = ""
    for tentativa in range(1, MAX_TENTATIVAS + 1):
        inicio = time.perf_counter()
        try:
            resp = sessao.get(url, headers=headers, timeout=timeout, stream=True)
            corpo = resp.content  # baixa o corpo inteiro dentro do cronômetro
            fim = time.perf_counter()
            if resp.status_code >= 500 or resp.status_code == 429:
                raise requests.HTTPError(f"HTTP {resp.status_code}")
            return {
                "ok": 200 <= resp.status_code < 400,
                "status": resp.status_code,
                "tentativa": tentativa,
                "tempo_ms": (fim - inicio) * 1000,
                "ttfb_ms": resp.elapsed.total_seconds() * 1000,
                "tamanho_kb": len(corpo) / 1024,
                "erro": "" if resp.status_code < 400 else f"HTTP {resp.status_code}",
            }
        except requests.RequestException as erro:
            ultimo_erro = str(erro)
            if tentativa < MAX_TENTATIVAS:
                time.sleep(ESPERA_BASE_S * 2 ** (tentativa - 1))
    return {"ok": False, "status": None, "tentativa": MAX_TENTATIVAS, "erro": ultimo_erro}


def validar(df: pd.DataFrame, alvos: Alvos, repeticoes: int) -> dict:
    """Nulos, duplicatas, faixas plausíveis e completude do desenho."""
    if df.empty:
        return {"linhas": 0, "completude": 0.0, "nulos": 0, "duplicatas": 0, "negativos": 0}
    chave = ["tratamento", "unidade", "repeticao", "metrica"]
    esperado = len(alvos.tratamentos) * len(alvos.unidades) * repeticoes
    por_obs = df.drop_duplicates(["tratamento", "unidade", "repeticao"]).shape[0] if len(df) else 0
    tempo = df.loc[df["metrica"] == "tempo_ms", "valor"]
    ttfb = df.pivot_table(index=["tratamento", "unidade", "repeticao"], columns="metrica", values="valor")
    ttfb_maior = int((ttfb["ttfb_ms"] > ttfb["tempo_ms"] + 1e-6).sum()) if {"ttfb_ms", "tempo_ms"} <= set(ttfb) else 0
    return {
        "linhas": int(len(df)),
        "nulos": int(df["valor"].isna().sum()),
        "duplicatas": int(df.duplicated(chave).sum()),
        "negativos": int((df["valor"] < 0).sum()),
        "tempo_acima_timeout": int((tempo > alvos.timeout_s * 1000).sum()),
        "ttfb_maior_que_tempo": ttfb_maior,
        "observacoes_esperadas": esperado,
        "observacoes_obtidas": int(por_obs),
        "completude": round(por_obs / esperado, 4) if esperado else 0.0,
    }


def estimar_duracao_s(n_obs: int, intervalo_s: float, latencia_ms: float) -> float:
    """Tempo de parede aproximado: cada requisição espera o intervalo ou a própria latência."""
    return n_obs * max(intervalo_s, latencia_ms / 1000)


def _git_commit() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                              check=True, cwd=Path(__file__).parent).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def ambiente() -> dict:
    return {
        "python": platform.python_version(),
        "requests": requests.__version__,
        "so": f"{platform.system()} {platform.release()} ({platform.version()})",
        "maquina": platform.machine(),
        "processador": platform.processor(),
        "commit": _git_commit(),
    }


def coletar(
    alvos: Alvos,
    repeticoes: int,
    aquecimento: int,
    semente: int,
    intervalo_s: float,
    saida: Path,
    rede: str = "",
    aquecer_unidades: bool = False,
    sessao: requests.Session | None = None,
    relogio: Callable[[], float] = time.monotonic,
    dormir: Callable[[float], None] = time.sleep,
) -> tuple[Path, dict]:
    sessao = sessao or requests.Session()
    sessao.headers["User-Agent"] = USER_AGENT
    intervalo = intervalo_efetivo(alvos, intervalo_s)

    permitido = verificar_robots(alvos, sessao)
    bloqueadas = [u for u, ok in permitido.items() if not ok]
    if bloqueadas:
        raise PermissionError(f"robots.txt não permite {len(bloqueadas)} URL(s), ex.: {bloqueadas[0]}")

    inicio_utc = datetime.now(timezone.utc)
    prefixo = saida / f"{alvos.nome}_{inicio_utc:%Y%m%dT%H%M%SZ}"
    saida.mkdir(parents=True, exist_ok=True)
    plano = plano_execucao(alvos, repeticoes, aquecimento, semente, aquecer_unidades)

    linhas: list[tuple] = []
    falhas = 0
    ultimo = None
    with open(f"{prefixo}.log.jsonl", "w", encoding="utf-8") as log:
        for ordem, (fase, tratamento, unidade, rep) in enumerate(plano, start=1):
            if ultimo is not None:
                espera = intervalo - (relogio() - ultimo)
                if espera > 0:
                    dormir(espera)
            ultimo = relogio()
            url = alvos.url(tratamento, unidade)
            r = medir(sessao, url, alvos.headers, alvos.timeout_s)
            registro = {"ordem": ordem, "timestamp": datetime.now(timezone.utc).isoformat(), "fase": fase,
                        "tratamento": tratamento, "unidade": unidade, "repeticao": rep, "url": url, **r}
            log.write(json.dumps(registro, ensure_ascii=False) + "\n")
            if fase != "medicao":
                continue
            if not r["ok"]:
                falhas += 1
                continue
            linhas.extend((tratamento, unidade, rep, m, round(r[m], 3)) for m in METRICAS)
            if ordem % 25 == 0:
                print(f"[{ordem}/{len(plano)}] {tratamento} {unidade} rep {rep}: {r['tempo_ms']:.1f} ms")

    df = pd.DataFrame(linhas, columns=list(COLUNAS))
    df.to_csv(f"{prefixo}.csv", index=False)
    validacao = validar(df, alvos, repeticoes)
    fim_utc = datetime.now(timezone.utc)
    meta = {
        "alvos": alvos.nome,
        "software": alvos.software,
        "tratamentos": alvos.tratamentos,
        "n_unidades": len(alvos.unidades),
        "parametros": {"repeticoes": repeticoes, "aquecimento": aquecimento,
                       "aquecer_unidades": aquecer_unidades, "semente": semente,
                       "intervalo_s": intervalo, "timeout_s": alvos.timeout_s, "user_agent": USER_AGENT},
        "config_sha256": hashlib.sha256(json.dumps(alvos.__dict__, sort_keys=True).encode()).hexdigest(),
        "ambiente": {**ambiente(), "rede": rede},
        "inicio_utc": inicio_utc.isoformat(),
        "fim_utc": fim_utc.isoformat(),
        "duracao_s": round((fim_utc - inicio_utc).total_seconds(), 1),
        "requisicoes": len(plano),
        "falhas_medicao": falhas,
        "validacao": validacao,
    }
    Path(f"{prefixo}.meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return Path(f"{prefixo}.csv"), meta


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description="Coleta do Lab05 (formato longo para ../analysis).")
    p.add_argument("alvos", type=Path, help="JSON com nome, software, tratamentos, unidades.")
    p.add_argument("--repeticoes", type=int, default=5)
    p.add_argument("--aquecimento", type=int, default=3, help="Requisições descartadas por tratamento.")
    p.add_argument("--aquecer-unidades", action="store_true",
                   help="Uma requisição descartada por (unidade, tratamento) antes da medição.")
    p.add_argument("--semente", type=int, default=42)
    p.add_argument("--intervalo", type=float, default=INTERVALO_MIN_EXTERNO_S,
                   help="Segundos entre requisições (mínimo 1 s para hosts externos).")
    p.add_argument("--saida", type=Path, default=Path("data/piloto"))
    p.add_argument("--rede", default="", help="Descrição da rede (ex.: 'Wi-Fi residencial 300 Mb/s').")
    p.add_argument("--estimar", action="store_true", help="Só estima a duração, sem requisições.")
    p.add_argument("--latencia-ms", type=float, default=500.0, help="Latência média usada em --estimar.")
    args = p.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # console do Windows (cp1252)

    alvos = Alvos.ler(args.alvos)
    intervalo = intervalo_efetivo(alvos, args.intervalo)
    n = len(plano_execucao(alvos, args.repeticoes, args.aquecimento, args.semente, args.aquecer_unidades))
    if args.estimar:
        s = estimar_duracao_s(n, intervalo, args.latencia_ms)
        print(f"{n} requisições x max({intervalo:.2f} s, {args.latencia_ms:.0f} ms) ~ {s / 60:.1f} min")
        return

    csv, meta = coletar(alvos, args.repeticoes, args.aquecimento, args.semente, args.intervalo,
                        args.saida, rede=args.rede, aquecer_unidades=args.aquecer_unidades)
    print(f"\nDados: {csv}\nDuração: {meta['duracao_s']} s | falhas: {meta['falhas_medicao']}")
    print("Validação:", json.dumps(meta["validacao"], ensure_ascii=False))
    v = meta["validacao"]
    if v["nulos"] or v["duplicatas"] or v["negativos"] or v["completude"] < 1:
        sys.exit("Validação encontrou problemas; registre em docs/piloto.md antes de usar os dados.")


if __name__ == "__main__":
    main()
