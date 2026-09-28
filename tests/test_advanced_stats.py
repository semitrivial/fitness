import csv
from pathlib import Path

import numpy as np

from stats.advanced_stats import benjamini_hochberg, fit_ridge_logistic, run_analysis


FOODS = [
    "Normal",
    "StrlFutDescs",
    "StrlAllDescs",
    "StrlFutDescsBonus",
    "StrlAllDescsBonus",
    "FrtlBonus",
    "Insanity",
    "Shortsighted",
]


def write_fixture(path: Path) -> None:
    rows = []
    row_id = 1

    def add(winner, loser, children, **foods):
        nonlocal row_id
        row = {
            "id": row_id,
            "isWinner": winner,
            "isLoser": loser,
            "num_children": children,
            **{food: int(foods.get(food, 0)) for food in FOODS},
        }
        rows.append(row)
        row_id += 1

    for _ in range(8):
        add(True, False, 3, Normal=1, FrtlBonus=1)
    for _ in range(2):
        add(False, True, 1, Normal=1)
    for _ in range(7):
        add(False, True, 0, StrlAllDescs=1)
    for _ in range(3):
        add(True, False, 2, Insanity=1, Shortsighted=1)
    add(True, True, 1, Normal=1)
    add(False, False, 0)

    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["id", "isWinner", "isLoser", *FOODS, "num_children"])
        writer.writeheader()
        writer.writerows(rows)


def test_benjamini_hochberg_is_monotone_and_bounded():
    adjusted = benjamini_hochberg(np.array([0.01, 0.04, 0.03, 0.8]))
    assert np.all((adjusted >= 0) & (adjusted <= 1))
    order = np.argsort(np.array([0.01, 0.04, 0.03, 0.8]))
    assert np.all(np.diff(adjusted[order]) >= 0)


def test_ridge_logistic_remains_finite_under_complete_separation():
    X = np.array([[1, 0], [1, 0], [1, 1], [1, 1]], dtype=float)
    successes = np.array([0, 0, 1, 1], dtype=float)
    totals = np.ones(4)
    coefficients, covariance, converged = fit_ridge_logistic(X, successes, totals, penalty=0.5)
    assert converged
    assert np.isfinite(coefficients).all()
    assert np.isfinite(covariance).all()
    assert coefficients[1] > 0


def test_run_analysis_audits_outcomes_and_writes_all_results(tmp_path):
    source = tmp_path / "study.csv"
    output = tmp_path / "results"
    write_fixture(source)

    result = run_analysis(source, output, threads=1, memory_limit="1GB")

    assert result["audit"]["winner_only"] == 11
    assert result["audit"]["loser_only"] == 9
    assert result["audit"]["both"] == 1
    assert result["audit"]["neither"] == 1

    expected = {
        "outcome_audit.csv",
        "food_associations.csv",
        "food_cooccurrence.csv",
        "food_reproduction.csv",
        "children_associations.csv",
        "adjusted_food_model.csv",
        "adjusted_food_children_model.csv",
        "analysis_report.txt",
        "food_adjusted_odds_ratios.png",
        "winner_probability_by_children.png",
    }
    assert expected.issubset({path.name for path in output.iterdir()})

    with (output / "food_associations.csv").open(encoding="utf-8") as handle:
        associations = {row["food_type"]: row for row in csv.DictReader(handle)}
    assert float(associations["FrtlBonus"]["risk_difference"]) > 0
    assert float(associations["StrlAllDescs"]["risk_difference"]) < 0

    with (output / "food_reproduction.csv").open(encoding="utf-8") as handle:
        reproduction = {row["food_type"]: row for row in csv.DictReader(handle)}
    assert float(reproduction["FrtlBonus"]["mean_children_exposed"]) > float(
        reproduction["FrtlBonus"]["mean_children_unexposed"]
    )

    report = (output / "analysis_report.txt").read_text(encoding="utf-8")
    assert "not independent simulation replicates" in report
    assert "num_children is downstream" in report
