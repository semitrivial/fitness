# Created by OpenAI GPT-6-sol (via Hermes Agent); reviewed and used by Anthropic Claude Opus 5.5
# for the analyses in stats/exploration/.
import csv
import json
from pathlib import Path

import duckdb
import pytest

from stats.analyze_new_export import convert, disk_check, summarize


HEADER = ["id", "run_id", "organism_id", "parent_ids", "birth_turn", "death_turn",
          "winner_turn", "loser_turn", "isWinner", "isLoser", "isDead",
          "num_children", "Normal", "StrlFutDescs", "StrlAllDescs",
          "StrlFutDescsBonus", "StrlAllDescsBonus", "FrtlBonus", "Insanity", "Shortsighted"]


def fixture(tmp_path):
    source = tmp_path / "stats.csv"
    rows = [
        ["1:1", 1, 1, "", 0, 5, 4, "", "True", "False", "True", 2, 1, 0, 0, 0, 0, 0, 0, 0],
        ["1:2", 1, 2, "", 0, 5, "", 4, "False", "True", "True", 0, 0, 1, 0, 0, 0, 0, 0, 0],
        ["2:1", 2, 1, "", 0, "", "", "", "False", "False", "False", 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ]
    with source.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(HEADER)
        writer.writerows(rows)
    runs = tmp_path / "runs.csv"
    with runs.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["run_id", "went_extinct", "organisms_created", "winner_count", "loser_count", "both_count", "unresolved_count"])
        writer.writerows([[1, "False", 2, 1, 1, 0, 0], [2, "False", 1, 0, 0, 0, 1]])
    return source, runs


def test_conversion_resume_and_summary(tmp_path):
    source, runs = fixture(tmp_path)
    output = tmp_path / "out"
    dataset = convert(source, output, 1, 0)
    checkpoint = json.loads((output / "conversion_checkpoint.json").read_text())
    assert checkpoint["offset"] == source.stat().st_size
    with source.open("rb") as stream:
        checkpoint["offset"] = len(stream.readline())
    checkpoint["parts"] = 0
    (output / "conversion_checkpoint.json").write_text(json.dumps(checkpoint))
    assert convert(source, output, 1, 0) == dataset
    assert duckdb.connect().execute("SELECT count(*), count(parent_ids) FROM read_parquet(?)", [str(dataset / "part-000000.parquet")]).fetchone() == (3, 0)
    summarize(dataset, runs, output)
    report = (output / "paper_statistics.md").read_text()
    assert "winner-only: 1; loser-only: 1" in report
    assert "| Normal | 1 | 0 | 1.000000 | 1 |" in report
    with source.open("a") as handle:
        handle.write("\n")
    with pytest.raises(RuntimeError, match="changed"):
        convert(source, output, 1, 0)


def test_disk_shortfall(tmp_path, monkeypatch):
    from stats import analyze_new_export
    monkeypatch.setattr(analyze_new_export.shutil, "disk_usage", lambda _: type("Usage", (), {"free": 1})())
    with pytest.raises(RuntimeError, match="Insufficient disk space"):
        disk_check(tmp_path, 100, 0)
