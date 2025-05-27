import csv
import subprocess
import pytest
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
TEST_OUTPUT = PROJECT_DIR / "output.csv"

def test_output_file_exists():
    assert TEST_OUTPUT.exists(), "output.csv is niet aangemaakt."


def test_output_has_valid_rows():
    # Open alleen als het bestand bestaat, anders laat de vorige test falen
    with TEST_OUTPUT.open("r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        assert len(reader) > 0, "output.csv bevat geen rijen."
        for row in reader[:10]:  # Alleen eerste 10 rijen controleren
            assert row["url"].startswith("http"), "Ongeldige URL in rij."
            assert len(row["raw_text"].strip()) > 10, "raw_text is te kort of leeg."

