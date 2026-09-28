#!/usr/bin/env python3
# Created by OpenAI GPT-6-sol (via Hermes Agent); reviewed and used by Anthropic Claude Opus 5.5
# for the analyses in stats/exploration/.
"""Resumable CSV-to-Parquet conversion and run-aware fitness summary.

Run: uv run python stats/analyze_new_export.py [--chunk-mib 64]
Each completed Parquet part is durable; rerunning skips completed parts. Do not
modify the source CSV while an analysis is in progress.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import sys
from collections import defaultdict
from pathlib import Path

import duckdb

FOODS = ("Normal", "StrlFutDescs", "StrlAllDescs", "StrlFutDescsBonus",
         "StrlAllDescsBonus", "FrtlBonus", "Insanity", "Shortsighted")
BOOLS = {"isWinner", "isLoser", "isDead", "sterile_at_export",
         "future_descendants_sterile_at_export", "extra_fertile_at_export",
         "is_insane_at_export", "is_shortsighted_at_export"}
INTS = {"run_id", "organism_id", "birth_turn", "death_turn", "winner_turn",
        "loser_turn", "age_at_export", "satiety_at_export", "num_children"}
for food in FOODS:
    INTS.update((food, food + "_count", food + "_first_turn", food + "_last_turn"))


def progress(done: int, total: int, label: str) -> None:
    width = 30
    fraction = done / total if total else 1
    print(f"\r{label}: [{'#' * int(width * fraction):30}] {fraction:6.1%} "
          f"({done:,}/{total:,} bytes)", end="\n" if done >= total else "", flush=True)


def disk_check(path: Path, remaining: int, reserve: int) -> None:
    free = shutil.disk_usage(path).free
    # Compression is data-dependent; this is a planning estimate, not a guarantee.
    estimated = int(remaining * .55) + reserve
    if free < estimated:
        raise RuntimeError(f"Insufficient disk space: {free / 2**30:.1f} GiB free; "
                           f"estimated {estimated / 2**30:.1f} GiB needed "
                           "(55% of remaining CSV plus reserve). Use --output-dir "
                           "on a larger volume or free space. Compression may vary.")


def csv_header(source: Path) -> tuple[bytes, list[str]]:
    with source.open("rb") as stream:
        raw = stream.readline()
    names = next(csv.reader([raw.decode("utf-8-sig")]))
    required = {"run_id", "isWinner", "isLoser", "num_children", *FOODS}
    if len(names) != len(set(names)) or not required.issubset(names):
        raise ValueError(f"Invalid CSV header; missing {sorted(required - set(names))}")
    return raw, names


def convert_chunk(conn: duckdb.DuckDBPyConnection, chunk: Path, target: Path,
                  names: list[str]) -> None:
    columns = []
    for name in names:
        quoted = '"' + name.replace('"', '""') + '"'
        kind = "BOOLEAN" if name in BOOLS else "BIGINT" if name in INTS else "VARCHAR"
        columns.append(f"TRY_CAST({quoted} AS {kind}) AS {quoted}")
    # Chunk is a real CSV with a header; all_varchar avoids inference differences
    # between parts (especially optional turn fields).
    destination = "'" + str(target).replace("'", "''") + "'"
    query = ("COPY (SELECT " + ", ".join(columns) +
             " FROM read_csv(?, header=true, all_varchar=true)) TO " + destination +
             " (FORMAT PARQUET, COMPRESSION ZSTD)")
    conn.execute(query, [str(chunk)])


def convert(source: Path, output: Path, chunk_mib: int, reserve_gib: float) -> Path:
    source = source.resolve()
    output.mkdir(parents=True, exist_ok=True)
    dataset = output / "organisms.parquet.parts"
    dataset.mkdir(exist_ok=True)
    header, names = csv_header(source)
    stat = source.stat()
    identity = {"source": str(source), "bytes": stat.st_size, "mtime_ns": stat.st_mtime_ns,
                "header": names, "chunk_mib": chunk_mib}
    checkpoint = output / "conversion_checkpoint.json"
    if checkpoint.exists():
        state = json.loads(checkpoint.read_text())
        if state["source_identity"] != identity:
            raise RuntimeError("CSV source or chunk size changed; use a different --output-dir "
                               "to avoid combining incompatible data")
    else:
        if any(dataset.iterdir()):
            raise RuntimeError("Parquet parts exist without checkpoint; use a new output directory")
        state = {"source_identity": identity, "offset": len(header), "parts": 0}
        pending = checkpoint.with_suffix(".json.tmp")
        pending.write_text(json.dumps(state, indent=2) + "\n")
        os.replace(pending, checkpoint)
    reserve = int(reserve_gib * 2**30)
    disk_check(output, stat.st_size - state["offset"], reserve)
    conn = duckdb.connect()
    chunk_path = output / "current_chunk.csv"
    partial = dataset / "current.parquet.tmp"
    # Interrupted writes are never trusted. The checkpoint is advanced only
    # after the final part has been atomically renamed into place.
    chunk_path.unlink(missing_ok=True)
    partial.unlink(missing_ok=True)
    for orphan in dataset.glob("part-*.parquet"):
        if int(orphan.stem.split("-")[-1]) >= state["parts"]:
            orphan.unlink()
    for number in range(state["parts"]):
        if not (dataset / f"part-{number:06d}.parquet").exists():
            raise RuntimeError(f"Committed Parquet part {number} is missing; cannot resume")
    with source.open("rb") as stream:
        stream.seek(state["offset"])
        progress(state["offset"], stat.st_size, "Converting CSV")
        while stream.tell() < stat.st_size:
            if state["parts"] % 10 == 0:
                disk_check(output, stat.st_size - state["offset"], reserve)
            with chunk_path.open("wb") as chunk:
                chunk.write(header)
                while chunk.tell() < chunk_mib * 2**20:
                    line = stream.readline()
                    if not line:
                        break
                    chunk.write(line)
            end = stream.tell()
            part = dataset / f"part-{state['parts']:06d}.parquet"
            if part.exists():
                # A crash between rename and checkpoint: overwrite this uncommitted part.
                part.unlink()
            convert_chunk(conn, chunk_path, partial, names)
            os.replace(partial, part)
            new_state = {**state, "offset": end, "parts": state["parts"] + 1}
            pending = checkpoint.with_suffix(".json.tmp")
            pending.write_text(json.dumps(new_state, indent=2) + "\n")
            os.replace(pending, checkpoint)
            state = new_state
            chunk_path.unlink()
            progress(end, stat.st_size, "Converting CSV")
    conn.close()
    return dataset


def summarize(dataset: Path, runs_csv: Path, output: Path) -> None:
    parts = sorted(dataset.glob("part-*.parquet"))
    if not parts:
        raise ValueError("No Parquet parts to analyze")
    conn = duckdb.connect()
    totals = defaultdict(lambda: [0, 0, 0, 0])
    food_counts = defaultdict(lambda: [0, 0])
    children = defaultdict(lambda: [0, 0])
    print(f"Analyzing {len(parts)} Parquet parts", flush=True)
    for index, part in enumerate(parts, 1):
        path = str(part)
        for run, winner, loser, n in conn.execute(
            "SELECT run_id, isWinner, isLoser, count(*) FROM read_parquet(?) "
            "GROUP BY 1,2,3", [path]).fetchall():
            category = 0 if winner and not loser else 1 if loser and not winner else 2 if winner and loser else 3
            totals[run][category] += n
        for food in FOODS:
            query = (f'SELECT run_id, isWinner, isLoser, count(*) FROM read_parquet(?) '
                     f'WHERE "{food}" > 0 GROUP BY 1,2,3')
            for run, winner, loser, n in conn.execute(query, [path]).fetchall():
                if bool(winner) != bool(loser):
                    food_counts[run, food][0 if winner else 1] += n
        for run, winner, loser, count, n in conn.execute(
            "SELECT run_id, isWinner, isLoser, num_children, count(*) "
            "FROM read_parquet(?) GROUP BY 1,2,3,4", [path]).fetchall():
            if bool(winner) != bool(loser) and count is not None:
                children[count][0 if winner else 1] += n
        print(f"\rAnalyzing Parquet: {index}/{len(parts)} parts", end="\n" if index == len(parts) else "", flush=True)
    conn.close()
    with runs_csv.open(newline="") as handle:
        runs = {int(row["run_id"]): row for row in csv.DictReader(handle)}
    if set(runs) != set(totals):
        raise ValueError(f"Run IDs mismatch: only in runs.csv={sorted(set(runs)-set(totals))[:10]}; "
                         f"only in stats.csv={sorted(set(totals)-set(runs))[:10]}")
    for run, row in runs.items():
        observed = totals[run]
        expected = [int(row[key]) for key in ("winner_count", "loser_count", "both_count", "unresolved_count")]
        if observed != expected or sum(observed) != int(row["organisms_created"]):
            raise ValueError(f"Run {run}: CSV audit {observed} disagrees with runs.csv {expected}")
    with (output / "food_by_run.csv").open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["run_id", "food", "winners", "losers", "fitness"])
        for run in sorted(runs):
            for food in FOODS:
                w, l = food_counts[run, food]
                writer.writerow([run, food, w, l, w / (w + l) if w + l else ""])
    with (output / "children_fitness.csv").open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["num_children", "winners", "losers", "fitness"])
        for count, (w, l) in sorted(children.items()):
            writer.writerow([count, w, l, w / (w + l)])
    aggregate = [sum(totals[r][i] for r in runs) for i in range(4)]
    lines = ["# Simulation results (generated from the updated exports)", "",
             "Fitness means winners / (winners + losers), among organisms with exactly",
             "one outcome flag. Foods are ever-eaten exposures and can overlap; these",
             "are descriptive associations, not causal effects. Organisms share a run,",
             "so organism-level binomial intervals would be misleading.", "",
             f"Runs: {len(runs):,}; extinct: {sum(r['went_extinct'].lower() == 'true' for r in runs.values()):,}.",
             f"Organisms: {sum(aggregate):,}; winner-only: {aggregate[0]:,}; "
             f"loser-only: {aggregate[1]:,}; both: {aggregate[2]:,}; "
             f"unresolved: {aggregate[3]:,}.", "",
             "## Fitness by food (pooled organism counts)", "",
             "| Food | Winners | Losers | Fitness | Runs with exposure |", "|---|---:|---:|---:|---:|"]
    for food in FOODS:
        w = sum(food_counts[r, food][0] for r in runs)
        l = sum(food_counts[r, food][1] for r in runs)
        nrun = sum(sum(food_counts[r, food]) > 0 for r in runs)
        lines.append(f"| {food} | {w:,} | {l:,} | {w/(w+l):.6f} | {nrun:,} |" if w+l else
                     f"| {food} | 0 | 0 | NA | 0 |")
    lines += ["", "## Fitness by number of children", "",
              "| Children | Winners | Losers | Fitness |", "|---:|---:|---:|---:|"]
    for count, (w, l) in sorted(children.items()):
        lines.append(f"| {count} | {w:,} | {l:,} | {w/(w+l):.6f} |")
    lines += ["", "## Run-level context", "",
              "Run-level denominators and food-specific counts are in food_by_run.csv.",
              "Pooled proportions weight runs by the number of organisms exposed; they",
              "are not averages over independent simulations. Extinct runs and unresolved",
              "organisms are retained in the audit but excluded from the fitness denominator.",
              "Food timing, offspring, age and winner timing are preserved in the Parquet",
              "parts for later sensitivity analyses. Differences in food or children",
              "fitness cannot by themselves establish an effect of exposure or crowding.", ""]
    (output / "paper_statistics.md").write_text("\n".join(lines))
    print(f"Wrote {output / 'paper_statistics.md'}")


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stats", type=Path, default=root / "stats.csv")
    parser.add_argument("--runs", type=Path, default=root / "runs.csv")
    parser.add_argument("--output-dir", type=Path, default=root / "stats" / "new_results")
    parser.add_argument("--chunk-mib", type=int, default=64)
    parser.add_argument("--reserve-gib", type=float, default=5)
    args = parser.parse_args()
    if args.chunk_mib < 1 or args.reserve_gib < 0:
        parser.error("chunk-mib must be positive and reserve-gib nonnegative")
    try:
        dataset = convert(args.stats, args.output_dir, args.chunk_mib, args.reserve_gib)
        summarize(dataset, args.runs, args.output_dir)
    except (RuntimeError, ValueError) as exc:
        parser.exit(1, f"Error: {exc}\n")


if __name__ == "__main__":
    main()
