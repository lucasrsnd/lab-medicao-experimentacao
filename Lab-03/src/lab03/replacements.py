"""Repõe somente vagas rejeitadas de uma fatia; preserva a seleção original."""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys

from lab03.cache import SQLiteCacheTransport
from lab03.cli import StreamingJson
from lab03.collectors.candidates import _count_releases, _has_actions, _metadata, _push_runs_total
from lab03.configuration import load_config
from lab03.domain import timestamp
from lab03.github import DataError, GitHubClient, HttpTransport
from lab03.pilot import RepositoryIneligible, run_pilot
from lab03.resilience import ResilientTransport


def reconcile(part, selection, replacements):
    """Aplica substituições apenas às posições rejeitadas da fatia, com auditoria."""
    first, last = part["pilot_sample"]["slice"]
    original = selection["eligible_repositories"]
    if not 0 <= first < last <= len(original):
        raise ValueError("Fatia inválida.")
    if part["window"] != selection["window"] or part["criteria"] != selection["criteria"]:
        raise ValueError("Janela ou critérios diferentes da seleção.")
    expected = [m["full_name"] for m in original[first:last]]
    accepted = {r["metadata"]["full_name"]: r for r in part["repositories"]}
    rejected = {r["repository"] for r in part["collection_validation"]["excluded"]}
    if len(accepted) != len(part["repositories"]) or set(accepted) & rejected:
        raise ValueError("Duplicatas ou exclusões inconsistentes.")
    if set(accepted) | rejected != set(expected):
        raise ValueError("A parte não explica todas as posições da fatia.")
    missing = [n for n in expected if n in rejected]
    names = [r["metadata"]["full_name"] for r in replacements]
    if len(replacements) != len(missing) or len(set(n.lower() for n in names)) != len(names):
        raise ValueError("Quantidade de substitutos incorreta ou repetida.")
    if {n.lower() for n in names} & {m["full_name"].lower() for m in original}:
        raise ValueError("Substituto já pertence à seleção original.")
    revised = deepcopy(selection)
    mappings = []
    for old, item in zip(missing, replacements):
        index = first + expected.index(old)
        revised["eligible_repositories"][index] = item["metadata"]
        mappings.append({"index": index, "previous": old, "replacement": item["metadata"]["full_name"]})
        accepted[item["metadata"]["full_name"]] = item
    revised["collection_revision"] = {
        "reason": "Elegibilidade da seleção rápida divergiu da coleta completa",
        "replacements": mappings, "excluded": part["collection_validation"]["excluded"],
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }
    metadata = revised["eligible_repositories"][first:last]
    records = [accepted[m["full_name"]] for m in metadata]
    return revised, records


def candidates(client, selection, config):
    # Apenas candidatos além da fronteira de popularidade; não refaz os 300.
    ceiling = min(m["stars"] for m in selection["eligible_repositories"])
    query = f"is:public stars:{config.stars_min_exclusive + 1}..{ceiling}"
    seen = {m["full_name"].lower() for m in selection["eligible_repositories"]}
    for page in range(1, 11):
        data = client.get("/search/repositories", {
            "q": query, "sort": "stars", "order": "desc", "per_page": 100, "page": page,
        })
        if data.get("incomplete_results") is True or not isinstance(data.get("items"), list):
            raise DataError("Busca de substitutos incompleta.")
        for record in data["items"]:
            name = record["full_name"].lower()
            if name not in seen:
                seen.add(name)
                yield record
        if len(data["items"]) < 100:
            break


def complete(client, part, selection, config, notify=print):
    excluded = part["collection_validation"]["excluded"]
    needed = len(excluded)
    replacements = []
    attempts = []
    if not needed:
        return reconcile(part, selection, []) + (attempts,)
    for record in candidates(client, selection, config):
        name = record["full_name"]
        root = f"/repos/{name}"
        notify(f"Reposição: avaliando {name} ({len(replacements)}/{needed} vagas preenchidas)")
        def reject(reason):
            attempts.append({"repository": name, "reason": reason})
        if record.get("private") or record["stargazers_count"] <= config.stars_min_exclusive:
            reject("outside_population")
            continue
        if not _has_actions(client, root):
            reject("no_actions")
            continue
        releases, _ = _count_releases(client, root, config.window.start, config.window.end,
                                      stop_above=config.maximum_releases_in_window)
        if releases < config.minimum_releases or (
            config.maximum_releases_in_window is not None and releases > config.maximum_releases_in_window
        ):
            reject("release_count_outside_limits")
            continue
        total = _push_runs_total(client, root, record["default_branch"], config.window.start, config.window.end)
        if total < config.minimum_valid_workflow_runs or (
            config.maximum_push_runs_in_window is not None and total > config.maximum_push_runs_in_window
        ):
            reject("push_runs_outside_limits")
            continue
        metadata = _metadata(client, record, root, datetime.now(timezone.utc), fast=True)
        metadata["push_runs_total"] = total
        one = {**selection, "eligible_repositories": [metadata]}
        try:
            result = run_pilot(
                client, window=config.window, target_size=1,
                stars_min_exclusive=config.stars_min_exclusive,
                minimum_releases=config.minimum_releases,
                minimum_valid_runs=config.minimum_valid_workflow_runs,
                valid_conclusions=config.valid_workflow_conclusions,
                collect_tags=False, top_only=True, include_workflow_runs=False,
                selection=one, notify=notify,
            )["repositories"][0]
        except RepositoryIneligible as error:
            attempts.append(error.record)
            continue
        metadata["release_count"] = len(result["report"]["catalog"]["releases"])
        metadata["valid_workflow_run_count"] = result["workflow_run_count"]
        replacements.append(result)
        attempts.append({"repository": name, "result": "accepted"})
        if len(replacements) == needed:
            break
    if len(replacements) != needed:
        raise DataError(f"Reposição incompleta: {len(replacements)}/{needed}; saída parcial preservada.")
    revised, records = reconcile(part, selection, replacements)
    return revised, records, attempts


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--partial", type=Path, required=True)
    parser.add_argument("--selection", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--revised-selection", type=Path, required=True)
    parser.add_argument("--cache", type=Path, default=Path("data/cache.sqlite3"))
    args = parser.parse_args(argv)
    config = load_config(args.config)
    values = json.loads(args.config.read_text(encoding="utf-8"))
    selection = json.loads(args.selection.read_text(encoding="utf-8"))
    with args.partial.open(encoding="utf-8") as handle:
        part = json.load(handle)
    if config.window.start != timestamp(part["window"]["start"]) or config.window.end != timestamp(part["window"]["end"]):
        raise ValueError("Janela da parte incompatível com configuração.")
    if part.get("configuration", {}).get("values") != values:
        raise ValueError("Configuração difere da usada na parte original.")
    namespace = hashlib.sha256(json.dumps(values, sort_keys=True).encode("utf-8")).hexdigest()
    notify = lambda message: print(message, file=sys.stderr, flush=True)
    with SQLiteCacheTransport(ResilientTransport(HttpTransport(os.environ["GITHUB_TOKEN"]), notify=notify),
                              args.cache, namespace=namespace) as cache:
        revised, records, attempts = complete(GitHubClient(cache), part, selection, config, notify)
    revised["collection_revision"]["candidate_audit"] = attempts
    revised["collection_revision"]["search_policy"] = "stars_desc_below_original_selection_boundary_max_1000_candidates"
    args.revised_selection.parent.mkdir(parents=True, exist_ok=True)
    revised_tmp = args.revised_selection.with_suffix(".json.tmp")
    revised_tmp.write_text(json.dumps(revised, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    revised_tmp.replace(args.revised_selection)
    first, last = part["pilot_sample"]["slice"]
    header = {k: v for k, v in part.items() if k not in (
        "repositories", "execution", "collection_validation", "eligible_repositories",
    )}
    header["eligible_repositories"] = revised["eligible_repositories"][first:last]
    header["selection_revision"] = revised["collection_revision"]
    writer = StreamingJson(args.output)
    writer.start(header)
    for item in records:
        writer.add(item)
    execution = {**part["execution"], "counts": {"eligible_repositories": len(records),
                 "metadata_records": len(records), **writer.counts},
                 "replacement_command": "python -m lab03.replacements " + " ".join(sys.argv[1:])}
    writer.finish({"execution": execution, "collection_validation": {
        "status": "complete", "requested": last - first, "accepted": len(records),
        "excluded": part["collection_validation"]["excluded"],
        "replacements": revised["collection_revision"]["replacements"],
    }})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
