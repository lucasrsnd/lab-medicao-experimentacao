"""Validação offline da evidência do piloto antes de concluir o manifesto."""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from lab03.domain import Window, timestamp


def validate_pilot(report: dict, *, target: int = 100, required: tuple[str, ...] = ()) -> dict:
    def check(condition, message):
        if not condition:
            raise ValueError(message)

    check(report.get("source") == "github", "O piloto deve conter dados reais do GitHub.")
    config = report["configuration"]["values"]
    config_hash = hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()
    check(config_hash == report["configuration"]["sha256"], "Hash da configuração inconsistente.")
    check(config["mode"] == "study", "Configuração não pertence ao estudo.")
    window = Window(timestamp(config["window"]["start"]), timestamp(config["window"]["end"]))
    check(timestamp(report["window"]["start"]) == window.start
          and timestamp(report["window"]["end"]) == window.end, "Janela do piloto divergente.")
    entries = report["repositories"]
    check(len(entries) == target, f"Esperados {target} repositórios completos.")
    check(report["pilot_sample"]["selected"] == target, "Contagem da amostra inconsistente.")
    identifiers = [item["metadata"]["id"] for item in entries]
    names = [item["metadata"]["full_name"].lower() for item in entries]
    check(len(set(identifiers)) == target and len(set(names)) == target, "Repositórios duplicados.")
    check(set(name.lower() for name in required).issubset(names), "Repositório obrigatório ausente.")
    check(identifiers == [r["id"] for r in report["eligible_repositories"]], "Seleção e coleta divergentes.")
    counts = {"eligible_repositories": target, "metadata_records": target,
              "releases": 0, "commits": 0, "workflow_runs": 0}
    population = config["population"]
    conclusions = set(config["workflow_runs"]["valid_conclusions"])
    for item in entries:
        metadata, result, runs = item["metadata"], item["report"], item["workflow_runs"]
        name = metadata["full_name"]
        releases = result["catalog"]["releases"]
        check(result["repository"] == name, f"Identidade inconsistente: {name}")
        check(metadata["stars"] > population["stars_min_exclusive"], f"Estrelas: {name}")
        check(len(releases) >= population["minimum_releases_in_window"], f"Releases insuficientes: {name}")
        check(len(runs) >= population["minimum_valid_workflow_runs_in_default_branch"], f"Runs insuficientes: {name}")
        check(len({r["id"] for r in runs}) == len(runs), f"Runs duplicados: {name}")
        check(len({r["id"] for r in releases}) == len(releases), f"Releases duplicadas: {name}")
        check(timestamp(result["window"]["start"]) == window.start
              and timestamp(result["window"]["end"]) == window.end, f"Janela divergente: {name}")
        check(all(r["sha"] and not r["prerelease"] and window.contains(timestamp(r["published_at"]))
                  for r in releases), f"Release fora dos critérios: {name}")
        check(all(r["branch"] == metadata["default_branch"] and r["event"] == "push"
                  and r["conclusion"] in conclusions and window.contains(timestamp(r["created_at"]))
                  for r in runs), f"Run fora dos critérios: {name}")
        check(metadata["release_count"] == len(releases)
              and metadata["valid_workflow_run_count"] == len(runs), f"Elegibilidade divergente: {name}")
        counts["releases"] += len(releases)
        counts["workflow_runs"] += len(runs)
        counts["commits"] += sum(len(change["commits"]) for change in result["changes"])
    check(counts == report["execution"]["counts"], "Contagens consolidadas inconsistentes.")
    return {"status": "validated", "validated_at": datetime.now(timezone.utc).isoformat(),
            "configuration_sha256": config_hash, "counts": counts,
            "repositories": [item["metadata"]["full_name"] for item in entries]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--require-repo", action="append", default=[])
    args = parser.parse_args(argv)
    try:
        payload = args.input.read_bytes()
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        evidence = validate_pilot(json.loads(payload), target=manifest["target_eligible_repositories"],
                                  required=tuple(args.require_repo))
        evidence["artifact"] = str(args.input)
        evidence["artifact_sha256"] = hashlib.sha256(payload).hexdigest()
        evidence["artifact_bytes"] = len(payload)
        manifest["execution_status"] = "completed"
        manifest["execution_evidence"] = evidence
        temporary = args.manifest.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(args.manifest)
        print(f"Piloto validado: {evidence['counts']['eligible_repositories']} repositórios únicos.")
        return 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f"Validação do piloto falhou: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
