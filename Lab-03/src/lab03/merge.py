"""Junta partes de uma coleta dividida entre pessoas (`--slice`) em um único JSON.

    python -m lab03.merge data/parte1.json data/parte2.json --output data/amostra_completa.json

Verifica que as partes usam a mesma janela e seleção, que não há repositório
repetido e que juntas cobrem exatamente a lista da seleção.
"""

import argparse
import json
import sys
from pathlib import Path


def merge_parts(parts: list[dict], selection: dict | None = None) -> dict:
    if not parts:
        raise ValueError("Nenhuma parte informada.")
    if any(part.get("collection_validation", {}).get("status") == "partial" for part in parts):
        raise ValueError("Parte com exclusões de elegibilidade: resolver reposição antes da junção.")
    first = parts[0]
    for part in parts[1:]:
        if part["window"] != first["window"] or part["criteria"] != first["criteria"]:
            raise ValueError("As partes foram coletadas com janela ou critérios diferentes.")
    by_name: dict[str, dict] = {}
    for part in parts:
        for item in part["repositories"]:
            name = item["metadata"]["full_name"]
            if name in by_name:
                raise ValueError(f"Repositório repetido entre as partes: {name}")
            by_name[name] = item
    if selection is not None:
        ordered = selection["eligible_repositories"]
    else:
        # Sem a seleção de referência, a ordem é a das fatias; a cobertura só
        # pode ser conferida contra o que as próprias partes declaram.
        ordered = [
            m for part in sorted(parts, key=lambda p: (p["pilot_sample"].get("slice") or [0])[0])
            for m in part["eligible_repositories"]
        ]
    order = [m["full_name"] for m in ordered]
    missing = [name for name in order if name not in by_name]
    extra = [name for name in by_name if name not in set(order)]
    if missing or extra:
        raise ValueError(
            f"Partes não cobrem a seleção: faltam {len(missing)} ({missing[:3]}...), "
            f"sobram {len(extra)}."
        )
    repositories = [by_name[name] for name in order]
    merged = {key: value for key, value in first.items() if key not in ("repositories", "execution")}
    merged["eligible_repositories"] = ordered
    merged["pilot_sample"] = {
        "target": len(order), "selected": len(repositories),
        "eligible_not_selected": first["pilot_sample"].get("eligible_not_selected", 0),
        "slices": [part["pilot_sample"].get("slice") for part in parts],
    }
    merged["repositories"] = repositories
    counts: dict[str, int] = {}
    for part in parts:
        for key, value in part["execution"]["counts"].items():
            counts[key] = counts.get(key, 0) + value
    merged["execution"] = {"parts": [part["execution"] for part in parts], "counts": counts}
    return merged


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("parts", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--selection", type=Path, default=None,
                        help="selecao-amostra.json (define a ordem e a cobertura esperada)")
    args = parser.parse_args(argv)
    try:
        selection = json.loads(args.selection.read_text(encoding="utf-8")) if args.selection else None
        merged = merge_parts([json.loads(p.read_text(encoding="utf-8")) for p in args.parts], selection)
    except (ValueError, KeyError, OSError) as error:
        print(f"Erro: {error}", file=sys.stderr)
        return 1
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(json.dumps(merged, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(args.output)
    print(f"{len(merged['repositories'])} repositórios -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
