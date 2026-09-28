#!/usr/bin/env python3
"""Run multivariable and exploratory analyses on the fitness simulation export.

The 25 GB organism-level CSV is collapsed to a small table of unique outcome,
food-exposure, and offspring-count patterns with DuckDB. Subsequent analyses use
that aggregate, so repeated runs are fast. Formal run-level inference is not
possible because the current export has no run/seed identifier; the report
states this limitation explicitly.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Iterable

import duckdb
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.special import expit
from scipy.stats import chi2, norm


FOOD_COLUMNS = [
    "Normal",
    "StrlFutDescs",
    "StrlAllDescs",
    "StrlFutDescsBonus",
    "StrlAllDescsBonus",
    "FrtlBonus",
    "Insanity",
    "Shortsighted",
]

INTERACTIONS = [
    ("Normal", "FrtlBonus"),
    ("StrlFutDescs", "FrtlBonus"),
    ("StrlAllDescs", "FrtlBonus"),
    ("StrlFutDescsBonus", "FrtlBonus"),
    ("StrlAllDescsBonus", "FrtlBonus"),
    ("Insanity", "Shortsighted"),
]

CHILD_BANDS = ["0", "1", "2", "3", "4-5", "6-10", "11+"]


def parse_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "t", "yes", "y"}


def child_band(value: int) -> str:
    if value <= 0:
        return "0"
    if value <= 3:
        return str(value)
    if value <= 5:
        return "4-5"
    if value <= 10:
        return "6-10"
    return "11+"


def benjamini_hochberg(p_values: np.ndarray) -> np.ndarray:
    """Return Benjamini-Hochberg FDR-adjusted p-values."""
    values = np.asarray(p_values, dtype=float)
    if values.size == 0:
        return values.copy()
    order = np.argsort(values)
    ranked = values[order]
    adjusted_ranked = ranked * values.size / np.arange(1, values.size + 1)
    adjusted_ranked = np.minimum.accumulate(adjusted_ranked[::-1])[::-1]
    adjusted = np.empty_like(adjusted_ranked)
    adjusted[order] = np.clip(adjusted_ranked, 0.0, 1.0)
    return adjusted


def fit_ridge_logistic(
    design: np.ndarray,
    successes: np.ndarray,
    totals: np.ndarray,
    penalty: float = 1.0,
    max_iterations: int = 250,
    tolerance: float = 1e-9,
) -> tuple[np.ndarray, np.ndarray, bool]:
    """Fit grouped-binomial ridge logistic regression by Newton iteration.

    The intercept is unpenalized. Ridge regularization keeps estimates finite
    under the complete separation present in several food indicators.
    """
    X = np.asarray(design, dtype=float)
    y = np.asarray(successes, dtype=float)
    n = np.asarray(totals, dtype=float)
    beta = np.zeros(X.shape[1], dtype=float)
    penalty_matrix = np.eye(X.shape[1], dtype=float) * penalty
    penalty_matrix[0, 0] = 0.0
    converged = False

    for _ in range(max_iterations):
        probability = np.clip(expit(X @ beta), 1e-12, 1 - 1e-12)
        weights = n * probability * (1 - probability)
        information = X.T @ (weights[:, None] * X) + penalty_matrix
        gradient = X.T @ (y - n * probability) - penalty_matrix @ beta
        try:
            step = np.linalg.solve(information, gradient)
        except np.linalg.LinAlgError:
            step = np.linalg.pinv(information) @ gradient
        beta += step
        if np.max(np.abs(step)) < tolerance:
            converged = True
            break

    probability = np.clip(expit(X @ beta), 1e-12, 1 - 1e-12)
    weights = n * probability * (1 - probability)
    information = X.T @ (weights[:, None] * X) + penalty_matrix
    covariance = np.linalg.pinv(information)
    return beta, covariance, converged


def write_csv(path: Path, rows: Iterable[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def aggregate_csv(
    source: Path,
    output: Path,
    threads: int = 4,
    memory_limit: str = "4GB",
) -> list[dict]:
    """Collapse the raw CSV to unique analysis patterns, with a valid cache."""
    aggregate_path = output / "aggregated_patterns.csv"
    metadata_path = output / "aggregated_patterns.metadata.json"
    source_stat = source.stat()
    expected_metadata = {
        "source": str(source.resolve()),
        "size": source_stat.st_size,
        "mtime_ns": source_stat.st_mtime_ns,
    }

    if aggregate_path.exists() and metadata_path.exists():
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            metadata = None
        if metadata == expected_metadata:
            return read_aggregate(aggregate_path)

    output.mkdir(parents=True, exist_ok=True)
    connection = duckdb.connect()
    connection.execute(f"SET threads TO {max(1, int(threads))}")
    connection.execute(f"SET memory_limit = '{memory_limit}'")
    food_select = ",\n                ".join(
        f"CAST({column} AS BOOLEAN) AS {column}" for column in FOOD_COLUMNS
    )
    food_group = ", ".join(FOOD_COLUMNS)
    query = f"""
        SELECT
            CAST(isWinner AS BOOLEAN) AS isWinner,
            CAST(isLoser AS BOOLEAN) AS isLoser,
            {food_select},
            CAST(num_children AS INTEGER) AS num_children,
            COUNT(*)::UBIGINT AS n
        FROM read_csv_auto(?, header=true, sample_size=100000)
        GROUP BY isWinner, isLoser, {food_group}, num_children
        ORDER BY isWinner, isLoser, {food_group}, num_children
    """
    cursor = connection.execute(query, [str(source)])
    columns = [item[0] for item in cursor.description]
    rows = [dict(zip(columns, values)) for values in cursor.fetchall()]
    connection.close()
    write_csv(aggregate_path, rows, columns)
    metadata_path.write_text(json.dumps(expected_metadata, indent=2) + "\n", encoding="utf-8")
    return rows


def read_aggregate(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as handle:
        for raw in csv.DictReader(handle):
            row = {
                "isWinner": parse_bool(raw["isWinner"]),
                "isLoser": parse_bool(raw["isLoser"]),
                "num_children": int(raw["num_children"]),
                "n": int(raw["n"]),
            }
            row.update({food: parse_bool(raw[food]) for food in FOOD_COLUMNS})
            rows.append(row)
    return rows


def outcome_audit(rows: list[dict]) -> dict[str, int]:
    result = {"winner_only": 0, "loser_only": 0, "both": 0, "neither": 0}
    for row in rows:
        winner, loser, count = bool(row["isWinner"]), bool(row["isLoser"]), int(row["n"])
        if winner and not loser:
            result["winner_only"] += count
        elif loser and not winner:
            result["loser_only"] += count
        elif winner and loser:
            result["both"] += count
        else:
            result["neither"] += count
    return result


def unambiguous_rows(rows: list[dict]) -> list[dict]:
    return [row for row in rows if bool(row["isWinner"]) != bool(row["isLoser"])]


def two_by_two_statistics(a: int, b: int, c: int, d: int) -> dict[str, float]:
    """Analyze [[winner exposed, loser exposed], [winner unexposed, loser unexposed]]."""
    exposed_total = a + b
    unexposed_total = c + d
    exposed_risk = a / exposed_total if exposed_total else math.nan
    unexposed_risk = c / unexposed_total if unexposed_total else math.nan
    risk_difference = exposed_risk - unexposed_risk
    rd_se = math.sqrt(
        exposed_risk * (1 - exposed_risk) / exposed_total
        + unexposed_risk * (1 - unexposed_risk) / unexposed_total
    ) if exposed_total and unexposed_total else math.nan

    aa, bb, cc, dd = (float(a), float(b), float(c), float(d))
    correction = 0.5 if min(a, b, c, d) == 0 else 0.0
    aa += correction
    bb += correction
    cc += correction
    dd += correction
    log_or = math.log(aa) + math.log(dd) - math.log(bb) - math.log(cc)
    log_or_se = math.sqrt(1 / aa + 1 / bb + 1 / cc + 1 / dd)

    total = a + b + c + d
    denominator = math.sqrt((a + b) * (c + d) * (a + c) * (b + d))
    phi = (a * d - b * c) / denominator if denominator else math.nan
    chi_square = total * phi * phi if denominator else math.nan
    p_value = float(chi2.sf(chi_square, 1)) if math.isfinite(chi_square) else math.nan
    return {
        "winner_exposed": a,
        "loser_exposed": b,
        "winner_unexposed": c,
        "loser_unexposed": d,
        "winner_probability_exposed": exposed_risk,
        "winner_probability_unexposed": unexposed_risk,
        "risk_difference": risk_difference,
        "risk_difference_ci_low": risk_difference - 1.96 * rd_se,
        "risk_difference_ci_high": risk_difference + 1.96 * rd_se,
        "odds_ratio": math.exp(np.clip(log_or, -700, 700)),
        "odds_ratio_ci_low": math.exp(np.clip(log_or - 1.96 * log_or_se, -700, 700)),
        "odds_ratio_ci_high": math.exp(np.clip(log_or + 1.96 * log_or_se, -700, 700)),
        "phi": phi,
        "chi_square": chi_square,
        "p_value": p_value,
    }


def food_associations(rows: list[dict]) -> list[dict]:
    results = []
    for food in FOOD_COLUMNS:
        a = b = c = d = 0
        for row in rows:
            count = int(row["n"])
            exposed = bool(row[food])
            winner = bool(row["isWinner"])
            if winner and exposed:
                a += count
            elif (not winner) and exposed:
                b += count
            elif winner:
                c += count
            else:
                d += count
        results.append({"food_type": food, **two_by_two_statistics(a, b, c, d)})
    adjusted = benjamini_hochberg(np.array([row["p_value"] for row in results]))
    for row, q_value in zip(results, adjusted):
        row["fdr_q_value"] = float(q_value)
    return results


def food_cooccurrence(rows: list[dict]) -> list[dict]:
    total = sum(int(row["n"]) for row in rows)
    results = []
    for index, first in enumerate(FOOD_COLUMNS):
        for second in FOOD_COLUMNS[index + 1 :]:
            n11 = n10 = n01 = n00 = 0
            for row in rows:
                count = int(row["n"])
                left, right = bool(row[first]), bool(row[second])
                if left and right:
                    n11 += count
                elif left:
                    n10 += count
                elif right:
                    n01 += count
                else:
                    n00 += count
            denominator = math.sqrt((n11 + n10) * (n01 + n00) * (n11 + n01) * (n10 + n00))
            phi = (n11 * n00 - n10 * n01) / denominator if denominator else math.nan
            union = n11 + n10 + n01
            results.append(
                {
                    "food_1": first,
                    "food_2": second,
                    "both_count": n11,
                    "food_1_only_count": n10,
                    "food_2_only_count": n01,
                    "neither_count": n00,
                    "jaccard": n11 / union if union else math.nan,
                    "phi": phi,
                    "total": total,
                }
            )
    return results


def food_reproduction(rows: list[dict]) -> list[dict]:
    """Summarize offspring counts by food exposure as a mediation diagnostic."""
    results = []
    for food in FOOD_COLUMNS:
        exposed_n = unexposed_n = 0
        exposed_positive = unexposed_positive = 0
        exposed_children = unexposed_children = 0
        for row in rows:
            count = int(row["n"])
            children = int(row["num_children"])
            if bool(row[food]):
                exposed_n += count
                exposed_children += count * children
                exposed_positive += count * int(children > 0)
            else:
                unexposed_n += count
                unexposed_children += count * children
                unexposed_positive += count * int(children > 0)
        results.append(
            {
                "food_type": food,
                "exposed_count": exposed_n,
                "unexposed_count": unexposed_n,
                "probability_any_children_exposed": exposed_positive / exposed_n if exposed_n else math.nan,
                "probability_any_children_unexposed": unexposed_positive / unexposed_n if unexposed_n else math.nan,
                "mean_children_exposed": exposed_children / exposed_n if exposed_n else math.nan,
                "mean_children_unexposed": unexposed_children / unexposed_n if unexposed_n else math.nan,
                "mean_children_difference": (
                    exposed_children / exposed_n - unexposed_children / unexposed_n
                    if exposed_n and unexposed_n
                    else math.nan
                ),
            }
        )
    return results


def wilson_interval(successes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    if total == 0:
        return math.nan, math.nan
    p = successes / total
    denominator = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    margin = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return center - margin, center + margin


def children_associations(rows: list[dict]) -> list[dict]:
    counts = {band: [0, 0] for band in CHILD_BANDS}
    for row in rows:
        band = child_band(int(row["num_children"]))
        counts[band][0 if bool(row["isWinner"]) else 1] += int(row["n"])
    results = []
    for band in CHILD_BANDS:
        winners, losers = counts[band]
        total = winners + losers
        low, high = wilson_interval(winners, total)
        results.append(
            {
                "children_band": band,
                "winner_count": winners,
                "loser_count": losers,
                "total_count": total,
                "winner_probability": winners / total if total else math.nan,
                "winner_probability_ci_low": low,
                "winner_probability_ci_high": high,
            }
        )
    return results


def build_design(rows: list[dict], include_children: bool) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[str]]:
    names = ["Intercept", *FOOD_COLUMNS]
    names.extend(f"{left}:{right}" for left, right in INTERACTIONS)
    if include_children:
        names.extend(f"children={band}" for band in CHILD_BANDS[1:])

    patterns: dict[tuple[float, ...], list[int]] = {}
    for row in rows:
        vector = [1.0, *[float(bool(row[food])) for food in FOOD_COLUMNS]]
        vector.extend(float(bool(row[left]) and bool(row[right])) for left, right in INTERACTIONS)
        if include_children:
            band = child_band(int(row["num_children"]))
            vector.extend(float(band == candidate) for candidate in CHILD_BANDS[1:])
        key = tuple(vector)
        bucket = patterns.setdefault(key, [0, 0])
        count = int(row["n"])
        bucket[1] += count
        if bool(row["isWinner"]):
            bucket[0] += count

    design = np.array(list(patterns.keys()), dtype=float)
    successes = np.array([value[0] for value in patterns.values()], dtype=float)
    totals = np.array([value[1] for value in patterns.values()], dtype=float)
    return design, successes, totals, names


def adjusted_model(rows: list[dict], include_children: bool, penalty: float) -> tuple[list[dict], bool]:
    design, successes, totals, names = build_design(rows, include_children)
    coefficients, covariance, converged = fit_ridge_logistic(design, successes, totals, penalty=penalty)
    standard_errors = np.sqrt(np.clip(np.diag(covariance), 0, np.inf))
    results = []
    for name, coefficient, standard_error in zip(names, coefficients, standard_errors):
        z_score = coefficient / standard_error if standard_error > 0 else math.nan
        p_value = 2 * norm.sf(abs(z_score)) if math.isfinite(z_score) else math.nan
        results.append(
            {
                "term": name,
                "coefficient": coefficient,
                "approx_standard_error": standard_error,
                "odds_ratio": math.exp(np.clip(coefficient, -700, 700)),
                "odds_ratio_ci_low": math.exp(np.clip(coefficient - 1.96 * standard_error, -700, 700)),
                "odds_ratio_ci_high": math.exp(np.clip(coefficient + 1.96 * standard_error, -700, 700)),
                "approx_p_value": p_value,
                "ridge_penalty": penalty,
                "converged": converged,
            }
        )
    return results, converged


def plot_adjusted_odds_ratios(rows: list[dict], output: Path) -> None:
    selected = [row for row in rows if row["term"] in FOOD_COLUMNS]
    odds = np.array([row["odds_ratio"] for row in selected])
    low = np.array([row["odds_ratio_ci_low"] for row in selected])
    high = np.array([row["odds_ratio_ci_high"] for row in selected])
    positions = np.arange(len(selected))
    figure, axis = plt.subplots(figsize=(7.2, 4.8), constrained_layout=True)
    axis.errorbar(odds, positions, xerr=[odds - low, high - odds], fmt="o", capsize=3, color="#245a75")
    axis.axvline(1.0, color="#68757d", linestyle="--", linewidth=1)
    axis.set_xscale("log")
    axis.set_yticks(positions, [row["term"] for row in selected])
    axis.set_xlabel("Adjusted odds ratio (ridge-stabilized model; log scale)")
    axis.invert_yaxis()
    axis.grid(axis="x", color="#d9dee2", linewidth=0.7)
    axis.spines[["top", "right"]].set_visible(False)
    figure.savefig(output, dpi=220)
    plt.close(figure)


def plot_children(rows: list[dict], output: Path) -> None:
    positions = np.arange(len(rows))
    probability = np.array([row["winner_probability"] for row in rows])
    low = np.array([row["winner_probability_ci_low"] for row in rows])
    high = np.array([row["winner_probability_ci_high"] for row in rows])
    figure, axis = plt.subplots(figsize=(7.0, 4.3), constrained_layout=True)
    axis.errorbar(positions, probability, yerr=[probability - low, high - probability], fmt="o-", capsize=3, color="#245a75")
    axis.set_xticks(positions, [row["children_band"] for row in rows])
    axis.set_xlabel("Number of children (banded)")
    axis.set_ylabel("Winner probability")
    axis.set_ylim(-0.02, 1.02)
    axis.grid(axis="y", color="#d9dee2", linewidth=0.7)
    axis.spines[["top", "right"]].set_visible(False)
    figure.savefig(output, dpi=220)
    plt.close(figure)


def format_probability(value: float) -> str:
    return "NA" if not math.isfinite(value) else f"{value:.6f}"


def write_report(
    output: Path,
    audit: dict[str, int],
    food_rows: list[dict],
    cooccurrence_rows: list[dict],
    reproduction_rows: list[dict],
    children_rows: list[dict],
    adjusted_rows: list[dict],
    adjusted_children_rows: list[dict],
) -> None:
    total = sum(audit.values())
    unambiguous = audit["winner_only"] + audit["loser_only"]
    marginal_sorted = sorted(food_rows, key=lambda row: abs(math.log(max(row["odds_ratio"], 1e-300))), reverse=True)
    adjusted_food = [row for row in adjusted_rows if row["term"] in FOOD_COLUMNS]
    adjusted_sorted = sorted(adjusted_food, key=lambda row: abs(row["coefficient"]), reverse=True)
    cooccurrence_sorted = sorted(cooccurrence_rows, key=lambda row: abs(row["phi"]), reverse=True)

    lines = [
        "ADVANCED FITNESS-SIMULATION ANALYSIS",
        "",
        "Scope and inferential limitations",
        "---------------------------------",
        f"Rows represented: {total:,}",
        f"Unambiguous winner/loser rows analyzed: {unambiguous:,}",
        f"Winner only: {audit['winner_only']:,}",
        f"Loser only: {audit['loser_only']:,}",
        f"Both winner and loser (excluded from models): {audit['both']:,}",
        f"Neither (excluded from models): {audit['neither']:,}",
        "",
        "Organism rows are not independent simulation replicates. The current export",
        "has no run/seed identifier, so p-values and intervals below are organism-level",
        "descriptions and are likely much too confident for run-level inference.",
        "",
        "num_children is downstream of reproduction and closely connected to the",
        "winner definition. Its model is a descriptive sensitivity analysis, not an",
        "independent or causal explanation of winning.",
        "",
        "Marginal food associations",
        "--------------------------",
    ]
    for row in marginal_sorted:
        p_text = "<1e-300" if row["p_value"] == 0 else f"{row['p_value']:.3g}"
        lines.append(
            f"{row['food_type']}: P(win|ate)={row['winner_probability_exposed']:.6f}, "
            f"P(win|not)={row['winner_probability_unexposed']:.6f}, "
            f"risk difference={row['risk_difference']:+.6f}, OR={row['odds_ratio']:.5g} "
            f"[{row['odds_ratio_ci_low']:.5g}, {row['odds_ratio_ci_high']:.5g}], p={p_text}"
        )

    lines.extend(["", "Offspring count by food exposure", "--------------------------------"])
    for row in sorted(reproduction_rows, key=lambda item: abs(item["mean_children_difference"]), reverse=True):
        lines.append(
            f"{row['food_type']}: mean children ate={row['mean_children_exposed']:.6f}, "
            f"did not eat={row['mean_children_unexposed']:.6f}, "
            f"difference={row['mean_children_difference']:+.6f}"
        )

    lines.extend(["", "Adjusted food model", "-------------------"])
    for row in adjusted_sorted:
        lines.append(
            f"{row['term']}: adjusted OR={row['odds_ratio']:.5g} "
            f"[{row['odds_ratio_ci_low']:.5g}, {row['odds_ratio_ci_high']:.5g}]"
        )
    lines.append("Interactions are reported in adjusted_food_model.csv.")

    lines.extend(["", "Strongest food co-occurrences", "-----------------------------"])
    for row in cooccurrence_sorted[:8]:
        lines.append(f"{row['food_1']} + {row['food_2']}: phi={row['phi']:+.6f}, Jaccard={row['jaccard']:.6f}")

    lines.extend(["", "Winner probability by offspring band", "------------------------------------"])
    for row in children_rows:
        lines.append(
            f"{row['children_band']} children: {format_probability(row['winner_probability'])} "
            f"(n={row['total_count']:,})"
        )

    lines.extend(
        [
            "",
            "Model notes",
            "-----------",
            "The adjusted models are grouped-binomial logistic regressions with an L2",
            "ridge penalty. This keeps estimates finite under complete separation.",
            "Their Wald intervals and p-values are approximate and should not be treated",
            "as a substitute for run-clustered or hierarchical inference.",
            f"Food-only model converged: {all(row['converged'] for row in adjusted_rows)}",
            f"Food-plus-children model converged: {all(row['converged'] for row in adjusted_children_rows)}",
            "Food tests use Benjamini-Hochberg FDR correction; see food_associations.csv.",
        ]
    )
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_analysis(
    source: Path,
    output: Path,
    threads: int = 4,
    memory_limit: str = "4GB",
    ridge_penalty: float = 1.0,
) -> dict:
    source = Path(source)
    output = Path(output)
    patterns = aggregate_csv(source, output, threads=threads, memory_limit=memory_limit)
    audit = outcome_audit(patterns)
    analysis_rows = unambiguous_rows(patterns)
    if not analysis_rows:
        raise ValueError("No unambiguous winner/loser observations were found")

    audit_rows = [{"outcome_category": category, "count": count} for category, count in audit.items()]
    food_rows = food_associations(analysis_rows)
    cooccurrence_rows = food_cooccurrence(analysis_rows)
    reproduction_rows = food_reproduction(analysis_rows)
    children_rows = children_associations(analysis_rows)
    adjusted_rows, _ = adjusted_model(analysis_rows, include_children=False, penalty=ridge_penalty)
    adjusted_children_rows, _ = adjusted_model(analysis_rows, include_children=True, penalty=ridge_penalty)

    write_csv(output / "outcome_audit.csv", audit_rows, ["outcome_category", "count"])
    write_csv(output / "food_associations.csv", food_rows, list(food_rows[0]))
    write_csv(output / "food_cooccurrence.csv", cooccurrence_rows, list(cooccurrence_rows[0]))
    write_csv(output / "food_reproduction.csv", reproduction_rows, list(reproduction_rows[0]))
    write_csv(output / "children_associations.csv", children_rows, list(children_rows[0]))
    write_csv(output / "adjusted_food_model.csv", adjusted_rows, list(adjusted_rows[0]))
    write_csv(output / "adjusted_food_children_model.csv", adjusted_children_rows, list(adjusted_children_rows[0]))
    plot_adjusted_odds_ratios(adjusted_rows, output / "food_adjusted_odds_ratios.png")
    plot_children(children_rows, output / "winner_probability_by_children.png")
    write_report(
        output / "analysis_report.txt",
        audit,
        food_rows,
        cooccurrence_rows,
        reproduction_rows,
        children_rows,
        adjusted_rows,
        adjusted_children_rows,
    )
    return {
        "audit": audit,
        "food_associations": food_rows,
        "cooccurrence": cooccurrence_rows,
        "food_reproduction": reproduction_rows,
        "children": children_rows,
        "adjusted_food": adjusted_rows,
        "adjusted_food_children": adjusted_children_rows,
    }


def parse_args() -> argparse.Namespace:
    script_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_csv", nargs="?", type=Path, default=script_dir.parent / "stats.csv")
    parser.add_argument("--output-dir", type=Path, default=script_dir / "advanced_results")
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--memory-limit", default="4GB")
    parser.add_argument("--ridge-penalty", type=float, default=1.0)
    return parser.parse_args()


def main() -> None:
    arguments = parse_args()
    run_analysis(
        arguments.input_csv,
        arguments.output_dir,
        threads=arguments.threads,
        memory_limit=arguments.memory_limit,
        ridge_penalty=arguments.ridge_penalty,
    )
    print(f"Results written to {arguments.output_dir.resolve()}")


if __name__ == "__main__":
    main()
