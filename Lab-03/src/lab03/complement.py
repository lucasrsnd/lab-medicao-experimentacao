"""Coleta complementar das variantes C2 e C3 (RQ07) sobre um dataset já coletado.

    python -m lab03.complement --config config/estudo.json --dataset data/parte2.json --output data/parte2-variantes.json

A coleta `--full` guarda o catálogo de releases (com pré-releases e as
antecessoras de cada cadeia), mas só compara a cadeia de releases publicadas
e não lista tags. Este comando reaproveita o catálogo salvo e o mesmo cache
SQLite (mesmo namespace da configuração) para buscar apenas o que falta:

- C2: `compare` da cadeia releases + pré-releases (pares iguais aos da cadeia
  principal saem do cache);
- C3: tags do default branch, datas dos commits apontados e `compare` entre
  commits marcados consecutivos.

Interrompido, basta repetir o comando: o que já está no cache não é consultado
de novo. Falhas de API que não sejam 404 encerram sem gravar saída parcial.
"""

import argparse
import hashlib
import json
import os
import sqlite3
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from lab03 import __version__
from lab03.cache import SQLiteCacheTransport
from lab03.collectors.commits import collect_changes
from lab03.collectors.tags import collect_tag_history, tag_catalog
from lab03.configuration import load_config
from lab03.domain import Release, ReleaseCatalog, ReleaseChanges, Window, timestamp
from lab03.github import ApiError, DataError, GitHubClient, HttpTransport
from lab03.metrics import (
    calculate_delivery_failure_rate, calculate_deployment_frequency, calculate_lead_time,
)
from lab03.resilience import ResilientTransport

SCHEMA_VERSION = 1


def release_from_dict(raw: dict) -> Release:
    return Release(
        id=raw["id"], tag=raw["tag"], sha=raw["sha"],
        published_at=timestamp(raw["published_at"]), prerelease=raw["prerelease"],
        notes=raw.get("notes") or "", url=raw["url"],
    )


def catalog_from_report(report: dict) -> ReleaseCatalog:
    """Reconstrói só o que `collect_changes` usa; exclusões e tags ficam no JSON."""
    raw = report["catalog"]
    return ReleaseCatalog(
        raw["default_branch"], raw["default_head"],
        tuple(release_from_dict(item) for item in raw["history"]),
        tuple(release_from_dict(item) for item in raw["releases"]),
        tuple(release_from_dict(item) for item in raw["prereleases"]),
        (), (),
    )


def change_summary(change: ReleaseChanges) -> dict:
    """Sem mensagens nem datas de commits: o bruto continua no cache."""
    return {
        "tag": change.release.tag,
        "release_id": change.release.id,
        "sha": change.release.sha,
        "published_at": change.release.published_at,
        "prerelease": change.release.prerelease,
        "previous_tag": change.previous.tag if change.previous else None,
        "previous_sha": change.previous.sha if change.previous else None,
        "exclusion": change.exclusion,
        "commits": len(change.commits),
    }


def complement_repository(client: GitHubClient, item: dict, window: Window) -> dict:
    name = item["metadata"]["full_name"]
    catalog = catalog_from_report(item["report"])

    c2_changes = collect_changes(client, name, catalog, window, include_prereleases=True)
    c2_failure = calculate_delivery_failure_rate(c2_changes, window)

    history = collect_tag_history(client, name, window, catalog.default_head)
    tags = tag_catalog(name, history, window, catalog.default_branch, catalog.default_head)
    c3_changes = collect_changes(client, name, tags, window)
    return {
        "full_name": name,
        "default_branch": catalog.default_branch,
        "default_head": catalog.default_head,
        "c2": {
            "delivery_unit": "published_releases_and_prereleases",
            "deliveries_in_window": len(catalog.releases) + len(catalog.prereleases),
            "lead_time": asdict(calculate_lead_time(c2_changes)),
            "delivery_failure_rate": asdict(c2_failure),
            "changes": [change_summary(change) for change in c2_changes],
        },
        "c3": {
            "delivery_unit": "tagged_commits_on_default_branch",
            "tag_history": asdict(history),
            "deployment_frequency": asdict(calculate_deployment_frequency(
                (release.published_at for release in tags.releases), window,
            )),
            "lead_time": asdict(calculate_lead_time(c3_changes)),
            "changes": [change_summary(change) for change in c3_changes],
        },
    }


def complement_dataset(
    client: GitHubClient, dataset: dict, window: Window, *, repositories=None, notify=None,
) -> list[dict]:
    items = dataset["repositories"]
    if repositories:
        wanted = {name.lower() for name in repositories}
        items = [i for i in items if i["metadata"]["full_name"].lower() in wanted]
        if len(items) != len(wanted):
            raise ValueError("Repositório pedido não está no dataset.")
    result = []
    for index, item in enumerate(items, 1):
        if notify:
            notify(f"Complemento {index}/{len(items)}: {item['metadata']['full_name']}")
        result.append(complement_repository(client, item, window))
    return result


def file_sha256(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def json_default(value):
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(f"Tipo não serializável: {type(value).__name__}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, required=True,
                        help="JSON produzido por --full (ex.: data/parte2.json)")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cache", type=Path, default=Path("data/cache.sqlite3"))
    parser.add_argument("--repo", action="append", default=[],
                        help="limitar a um repositório do dataset (repetível)")
    args = parser.parse_args(argv)
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        parser.error("Defina GITHUB_TOKEN no ambiente.")
    cache = None
    try:
        config = load_config(args.config)
        snapshot = json.loads(args.config.read_text(encoding="utf-8"))
        config_hash = hashlib.sha256(json.dumps(snapshot, sort_keys=True).encode("utf-8")).hexdigest()
        dataset = json.loads(args.dataset.read_text(encoding="utf-8"))
        if dataset["configuration"]["sha256"] != config_hash:
            raise ValueError("Dataset coletado com outra configuração; o cache não seria reaproveitado.")
        window = config.window
        if (timestamp(dataset["window"]["start"]) != window.start
                or timestamp(dataset["window"]["end"]) != window.end):
            raise ValueError("Janela do dataset difere da configuração.")
        resilient = ResilientTransport(
            HttpTransport(token), notify=lambda m: print(m, file=sys.stderr, flush=True),
        )
        cache = SQLiteCacheTransport(resilient, args.cache.resolve(), namespace=config_hash)
        repositories = complement_dataset(
            GitHubClient(cache), dataset, window, repositories=args.repo,
            notify=lambda m: print(m, file=sys.stderr, flush=True),
        )
        output = {
            "schema_version": SCHEMA_VERSION,
            "kind": "rq07_variant_complement",
            "pipeline_version": __version__,
            "generated_at": datetime.now(timezone.utc),
            "window": dataset["window"],
            "dataset": {"path": str(args.dataset), "sha256": file_sha256(args.dataset),
                        "repositories": len(dataset["repositories"])},
            "configuration": {"sha256": config_hash},
            "partial_selection": bool(args.repo),
            "cache": {"hits": cache.hits, "misses": cache.misses},
            "repositories": repositories,
        }
        del dataset
        args.output.parent.mkdir(parents=True, exist_ok=True)
        temporary = args.output.with_suffix(args.output.suffix + ".tmp")
        temporary.write_text(
            json.dumps(output, default=json_default, ensure_ascii=False) + "\n", encoding="utf-8",
        )
        temporary.replace(args.output)
    except KeyboardInterrupt:
        parser.exit(130, "Interrompido. Rode o mesmo comando para retomar pelo cache.\n")
    except (ApiError, DataError, ValueError, KeyError, OSError, RuntimeError, sqlite3.Error) as error:
        parser.exit(1, f"Erro: {error}\n")
    finally:
        if cache is not None:
            cache.close()
    print(f"Resultado: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
