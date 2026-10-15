"""Executa a coleta de um repositório a partir de uma configuração validada."""

import argparse
import json
import hashlib
import os
import sqlite3
import sys
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from lab03 import __version__
from lab03.cache import SQLiteCacheTransport
from lab03.configuration import load_config
from lab03.domain import timestamp
from lab03.github import (
    ApiError, DataError, GitHubClient, HttpTransport, SnapshotTransport,
)
from lab03.pipeline import run
from lab03.collectors.candidates import select_candidates
from lab03.collectors.releases import repo_path
from lab03.collectors.workflow_runs import collect_workflow_runs
from lab03.pilot import run_pilot
from lab03.resilience import ResilientTransport


def json_default(value):
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(f"Tipo não serializável: {type(value).__name__}")


class StreamingJson:
    """Grava `{...cabeçalho, "repositories": [...], ...rodapé}` um repositório por vez,
    em arquivo temporário, trocado pelo definitivo só no fim."""

    def __init__(self, path: Path):
        self.path = path
        self.temporary = path.with_suffix(path.suffix + ".tmp")
        path.parent.mkdir(parents=True, exist_ok=True)
        self.handle = self.temporary.open("w", encoding="utf-8")
        self.count = 0
        self.counts = {"releases": 0, "commits": 0, "workflow_runs": 0}

    def _dumps(self, value) -> str:
        return json.dumps(value, default=json_default, ensure_ascii=False, separators=(",", ":"))

    def start(self, header: dict) -> None:
        self.handle.write(self._dumps(header)[:-1] + ',"repositories":[')

    def add(self, item: dict) -> None:
        self.handle.write(("," if self.count else "") + self._dumps(item))
        self.handle.flush()
        self.count += 1
        report = item["report"]
        self.counts["releases"] += len(report["catalog"]["releases"])
        self.counts["commits"] += sum(len(change["commits"]) for change in report["changes"])
        self.counts["workflow_runs"] += item["workflow_run_count"]

    def finish(self, footer: dict) -> None:
        self.handle.write("]," + self._dumps(footer)[1:] + "\n")
        self.handle.close()
        self.temporary.replace(self.path)

    def abort(self) -> None:
        if not self.handle.closed:
            self.handle.close()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True, help="Configuração JSON do estudo ou da amostra")
    parser.add_argument("--repo", help="owner/repo; obrigatório para coleta real")
    parser.add_argument("--include-repo", action="append", default=[],
                        help="Repositório obrigatório do piloto; também deve passar pelos filtros")
    parser.add_argument(
        "--select-candidates", action="store_true",
        help="selecionar a amostra inicial e gerar o funil do estudo",
    )
    parser.add_argument(
        "--pilot", action="store_true",
        help="coletar o piloto integrado com 100 repositórios elegíveis",
    )
    parser.add_argument(
        "--full", action="store_true",
        help="coletar a amostra completa (final_sample_minimum elegíveis, S02)",
    )
    parser.add_argument(
        "--workers", type=int, default=None,
        help="threads para avaliar/coletar repositórios em paralelo (padrão: 6 em --full, 1 nos demais)",
    )
    parser.add_argument(
        "--selection", type=Path,
        help="usar a lista de elegíveis de uma seleção anterior (ex.: config/selecao-amostra.json), sem refazer a busca",
    )
    parser.add_argument(
        "--slice", dest="slice_range",
        help="com --selection: coletar só INÍCIO:FIM da lista (ex.: 200:300)",
    )
    parser.add_argument(
        "--cache", type=Path, default=Path("data/cache.sqlite3"),
        help="cache SQLite persistente para retomada (padrão: data/cache.sqlite3)",
    )
    parser.add_argument("--output", type=Path, help="Arquivo JSON de saída")
    parser.add_argument("--validate-config", action="store_true", help="Validar configuração sem coletar")
    parser.add_argument("--refresh-cache", action="store_true", help="Invalidar respostas desta configuração antes da coleta")
    args = parser.parse_args(argv)
    if args.include_repo and not args.pilot:
        parser.error("--include-repo exige --pilot.")
    cache = None
    try:
        config = load_config(args.config)
        config_snapshot = json.loads(args.config.read_text(encoding="utf-8"))
        config_hash = hashlib.sha256(
            json.dumps(config_snapshot, sort_keys=True).encode("utf-8")
        ).hexdigest()
        if args.validate_config:
            if config.mode == "study" and not config.collection_allowed:
                print("Configuração válida; coleta bloqueada até a janela oficial ser confirmada.")
            else:
                print(f"Configuração válida para modo {config.mode}.")
            return 0
        if args.output is None:
            parser.error("Defina --output para executar o pipeline.")
        if sum([args.pilot, args.full, args.select_candidates]) > 1:
            parser.error("Use apenas um entre --pilot, --full e --select-candidates.")

        if config.mode == "sample":
            if args.select_candidates or args.pilot or args.full:
                parser.error("--select-candidates, --pilot e --full só podem ser usados no modo study.")
            if args.repo and args.repo != config.repository:
                parser.error("No modo sample, o repositório é fixado pelo arquivo de configuração.")
            if config.repository is None or config.window is None or config.snapshot is None:
                raise ValueError("Configuração da amostra incompleta.")
            repository = config.repository
            window = config.window
            transport = SnapshotTransport(
                json.loads(config.snapshot.read_text(encoding="utf-8"))["responses"]
            )
            cache = resilient = None
            source = "snapshot"
        else:
            if not config.collection_allowed or config.window is None:
                parser.exit(
                    2,
                    "Coleta bloqueada: confirme a janela oficial no arquivo de configuração "
                    "antes de iniciar consultas à API.\n",
                )
            if (args.select_candidates or args.pilot or args.full) and args.repo:
                parser.error("Não combine --select-candidates, --pilot ou --full com --repo.")
            if not (args.select_candidates or args.pilot or args.full):
                if not args.repo:
                    parser.error("Defina --repo owner/repo para a coleta real.")
                repository = args.repo
            token = os.environ.get("GITHUB_TOKEN")
            if not token:
                parser.error("Defina GITHUB_TOKEN no ambiente para a coleta real.")
            window = config.window
            cache_path = args.cache
            if not cache_path.is_absolute():
                cache_path = Path.cwd() / cache_path
            resilient = ResilientTransport(
                HttpTransport(token),
                notify=lambda message: print(message, file=sys.stderr, flush=True),
            )
            cache = SQLiteCacheTransport(resilient, cache_path, namespace=config_hash)
            if args.refresh_cache:
                cache.clear()
            transport = cache
            source = "github"

        client = GitHubClient(transport)
        if args.pilot or args.full:
            flag = "--full" if args.full else "--pilot"
            target_size = (
                config.final_sample_minimum if args.full else config.initial_sprint_sample
            )
            selection = None
            slice_range = None
            if args.selection:
                selection = json.loads(args.selection.read_text(encoding="utf-8"))
                if timestamp(selection["window"]["start"]) != window.start or timestamp(
                    selection["window"]["end"]
                ) != window.end:
                    raise ValueError("A janela da seleção difere da janela da configuração.")
            if args.slice_range:
                if not args.selection:
                    parser.error("--slice exige --selection.")
                try:
                    first, last = (int(part) for part in args.slice_range.split(":"))
                except ValueError:
                    parser.error("--slice deve ter o formato INÍCIO:FIM, ex.: 200:300.")
                slice_range = (first, last)
            stream = StreamingJson(args.output) if args.full else None
            output = run_pilot(
                client,
                window=window,
                target_size=target_size,
                stars_min_exclusive=config.stars_min_exclusive,
                minimum_releases=config.minimum_releases,
                minimum_valid_runs=config.minimum_valid_workflow_runs,
                valid_conclusions=config.valid_workflow_conclusions,
                # S02 não usa tags (variante C3, RQ07): economiza milhares de requisições.
                collect_tags=not args.full,
                top_only=args.full,
                workers=args.workers or (3 if args.full else 1),
                maximum_runs=config.maximum_push_runs_in_window,
                maximum_releases=config.maximum_releases_in_window,
                on_start=stream.start if stream else None,
                on_result=stream.add if stream else None,
                # Os runs brutos ficam no cache; as métricas já saem deles.
                include_workflow_runs=not args.full,
                selection=selection,
                slice_range=slice_range,
                notify=lambda message: print(message, file=sys.stderr, flush=True),
                required_repositories=tuple(args.include_repo),
            )
            output["sample_kind"] = "full" if args.full else "pilot"
            output["execution"] = {
                "command": (
                    f"python -m lab03 --config {args.config} {flag} "
                    f"--output {args.output} --cache {args.cache}"
                    + "".join(f" --include-repo {name}" for name in args.include_repo)
                ),
                "config": str(args.config),
                "pipeline_version": __version__,
                "cache": {
                    "path": str(cache_path),
                    "hits": cache.hits,
                    "misses": cache.misses,
                },
                "resilience": {
                    "retries": resilient.retries,
                    "rate_limit_waits": resilient.rate_limit_waits,
                    "waited_seconds": round(resilient.waited_seconds, 1),
                },
                "counts": (
                    {"eligible_repositories": stream.count, "metadata_records": stream.count,
                     **stream.counts}
                    if stream else {
                        "eligible_repositories": len(output["repositories"]),
                        "metadata_records": len(output["repositories"]),
                        "releases": sum(
                            len(item["report"]["catalog"]["releases"])
                            for item in output["repositories"]
                        ),
                        "commits": sum(
                            len(change["commits"])
                            for item in output["repositories"]
                            for change in item["report"]["changes"]
                        ),
                        "workflow_runs": sum(
                            len(item["workflow_runs"]) for item in output["repositories"]
                        ),
                    }
                ),
            }
            if stream:
                stream.finish({
                    "sample_kind": output["sample_kind"],
                    "execution": output["execution"],
                    "source": source,
                    **{
                        field: output[field]
                        for field in ("collection_exclusions", "collection_replacements")
                        if field in output
                    },
                })
                print(f"Resultado: {args.output}")
                return 0
        elif args.select_candidates:
            output = select_candidates(
                client,
                window.start,
                window.end,
                stars_min_exclusive=config.stars_min_exclusive,
                sample_size=config.initial_sprint_sample,
                minimum_releases=config.minimum_releases,
                minimum_valid_runs=config.minimum_valid_workflow_runs,
                valid_conclusions=config.valid_workflow_conclusions,
            )
        else:
            workflow_runs = None
            collection = {}
            if config.mode == "study":
                branch = client.get(repo_path(repository))["default_branch"]
                workflow_runs = collect_workflow_runs(
                    client, repository, window, branch,
                    config.valid_workflow_conclusions, stats=collection,
                )
            output = run(client, repository, window, workflow_runs)
            if workflow_runs is not None:
                output["workflow_runs"] = [asdict(item) for item in workflow_runs]
                output["workflow_run_collection"] = collection
        output["source"] = source
        output["configuration"] = {"sha256": config_hash, "values": config_snapshot}
        args.output.parent.mkdir(parents=True, exist_ok=True)
        temporary = args.output.with_suffix(args.output.suffix + ".tmp")
        temporary.write_text(
            json.dumps(output, default=json_default, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.replace(args.output)
    except KeyboardInterrupt:
        parser.exit(130, (
            "Interrompido. Respostas já coletadas estão no cache; rode o mesmo "
            "comando para retomar de onde parou.\n"
        ))
    except (
        ApiError, DataError, ValueError, KeyError, OSError, RuntimeError, sqlite3.Error,
    ) as error:
        parser.exit(1, f"Erro: {error}\n")
    finally:
        if cache is not None:
            cache.close()
    print(f"Resultado: {args.output}")
    return 0
