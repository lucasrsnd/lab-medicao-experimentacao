"""Sorteio da amostra-ouro e planilhas cegas de rotulagem (seção 6 do enunciado).

Uso, depois da coleta completa:

    python -m lab03.gold_sample --dataset data/amostra_completa.json --out labels

O sorteio é reproduzível: a semente (padrão 42) e o hash do dataset de origem
ficam registrados em `amostra_ouro_sorteio.json`. As planilhas dos avaliadores
são **cegas**: só trazem identificação e links; nunca a saída da heurística, as
métricas DORA nem o rótulo de outro avaliador.
"""

import argparse
import csv
import hashlib
import json
import random
import sys
from pathlib import Path

SEED = 42
GOLD_REPOSITORIES = 60
RELEASES_PER_REPOSITORY = 5
RATERS = ("A", "B", "C")

REPOSITORY_FIELDS = (
    "repositorio", "url", "tipo_projeto", "releases_sao_entregas", "observacoes",
)
RELEASE_FIELDS = (
    "repositorio", "tag", "publicada_em", "url_release", "url_comparacao",
    "e_corretiva", "observacoes",
)
SORTEIO_FIELDS = ("repositorio", "tag", "release_id", "publicada_em")


def draw_repositories(full_names, n=GOLD_REPOSITORIES, seed=SEED) -> list[str]:
    """Amostra sem reposição, independente da ordem de entrada."""
    names = sorted(set(full_names))
    if len(names) < n:
        raise ValueError(f"Amostra tem {len(names)} repositórios; são necessários {n}.")
    return sorted(random.Random(seed).sample(names, n))


def _comparable_releases(item: dict) -> list[dict]:
    report = item["report"]
    labelable = {
        change["release"]["id"]
        for change in report["changes"] if change["exclusion"] is None
    }
    candidates = sorted(
        (r for r in report["catalog"]["releases"] if r["id"] in labelable),
        key=lambda r: (r["published_at"], r["tag"]),
    )
    return candidates


def draw_releases(item: dict, k=RELEASES_PER_REPOSITORY, seed=SEED) -> list[dict]:
    """Sorteia k releases com lista de commits disponível (rotulável)."""
    name = item["metadata"]["full_name"]
    candidates = _comparable_releases(item)
    if len(candidates) < k:
        raise ValueError(
            f"{name} tem {len(candidates)} releases comparáveis; são necessárias {k}."
        )
    # Semente por repositório: o sorteio de um não depende dos demais.
    chosen = random.Random(f"{seed}:{name}").sample(candidates, k)
    return sorted(chosen, key=lambda r: (r["published_at"], r["tag"]))


def previous_tags(item: dict) -> dict[int, str | None]:
    return {
        change["release"]["id"]: (change["previous"] or {}).get("tag")
        for change in item["report"]["changes"]
    }


def draw_gold_sample(dataset: dict, *, n=GOLD_REPOSITORIES,
                     releases_per_repository=RELEASES_PER_REPOSITORY, seed=SEED) -> dict:
    by_name = {item["metadata"]["full_name"]: item for item in dataset["repositories"]}
    labelable_names = [
        name for name, item in by_name.items()
        if len(_comparable_releases(item)) >= releases_per_repository
    ]
    if len(labelable_names) < n:
        raise ValueError(
            f"Amostra tem {len(labelable_names)} repositórios com "
            f"{releases_per_repository} releases comparáveis; são necessários {n}."
        )
    repositories, releases = [], []
    for name in draw_repositories(labelable_names, n, seed):
        item = by_name[name]
        previous = previous_tags(item)
        repositories.append({"repositorio": name, "url": f"https://github.com/{name}"})
        for release in draw_releases(item, releases_per_repository, seed):
            before = previous[release["id"]]
            releases.append({
                "repositorio": name,
                "tag": release["tag"],
                "release_id": release["id"],
                "publicada_em": release["published_at"],
                "url_release": release["url"],
                "url_comparacao": (
                    f"https://github.com/{name}/compare/{before}...{release['tag']}"
                    if before else ""
                ),
            })
    return {
        "repositories": repositories,
        "releases": releases,
        "repository_sampling": {
            "eligible_repository_count": len(labelable_names),
            "excluded_insufficient_comparable_releases": len(by_name) - len(labelable_names),
        },
    }


def _write_csv(path: Path, fields, rows) -> None:
    # utf-8-sig: o Excel abre acentos corretamente.
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_outputs(sample: dict, out: Path, *, seed: int, dataset_sha256: str,
                  dataset: dict, raters=RATERS, force=False) -> list[Path]:
    out.mkdir(parents=True, exist_ok=True)
    manifest = out / "amostra_ouro_sorteio.json"
    release_draw = out / "amostra_ouro_releases.csv"
    targets = [manifest, release_draw]
    for rater in raters:
        targets += [out / f"rotulos_{rater}_repositorios.csv", out / f"rotulos_{rater}_releases.csv"]
    existing = [path for path in targets if path.exists()]
    if existing and not force:
        # Planilhas preenchidas são trabalho humano: nunca sobrescrever em silêncio.
        raise FileExistsError(
            "Já existem: " + ", ".join(p.name for p in existing) + ". Use --force só se quiser refazer o sorteio."
        )
    manifest.write_text(json.dumps({
        "seed": seed,
        "repositories": len(sample["repositories"]),
        "releases": len(sample["releases"]),
        "releases_per_repository": RELEASES_PER_REPOSITORY,
        "source_dataset_sha256": dataset_sha256,
        "source_collected_at": dataset.get("collected_at"),
        "source_window": dataset.get("window"),
        "repository_sampling": sample["repository_sampling"],
        "sampling": (
            "random.Random(seed).sample sobre nomes ordenados com releases "
            "comparáveis suficientes; releases por random.Random(f'{seed}:{repo}')"
        ),
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _write_csv(release_draw, SORTEIO_FIELDS, sample["releases"])
    for rater in raters:
        _write_csv(out / f"rotulos_{rater}_repositorios.csv", REPOSITORY_FIELDS, sample["repositories"])
        _write_csv(out / f"rotulos_{rater}_releases.csv", RELEASE_FIELDS, sample["releases"])
    return targets


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dataset", type=Path, required=True, help="JSON da coleta completa (--full)")
    parser.add_argument("--out", type=Path, default=Path("labels"))
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--force", action="store_true", help="sobrescrever sorteio e planilhas existentes")
    args = parser.parse_args(argv)
    raw = args.dataset.read_bytes()
    dataset = json.loads(raw)
    try:
        sample = draw_gold_sample(dataset, seed=args.seed)
        paths = write_outputs(
            sample, args.out, seed=args.seed,
            dataset_sha256=hashlib.sha256(raw).hexdigest(), dataset=dataset, force=args.force,
        )
    except (ValueError, KeyError, FileExistsError) as error:
        print(f"Erro: {error}", file=sys.stderr)
        return 1
    print(f"{len(sample['repositories'])} repositórios, {len(sample['releases'])} releases.")
    for path in paths:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
