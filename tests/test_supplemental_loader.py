"""Tests for supplemental dataset loader."""

import csv
import json
from pathlib import Path

from src.ingestion.supplemental_loader import load_supplemental


class TestLoadSupplemental:
    def test_load_csv(self, tmp_path):
        csv_file = tmp_path / "test.csv"
        with open(csv_file, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["hindi", "english", "roman"])
            writer.writeheader()
            writer.writerow({"hindi": "पानी", "english": "water", "roman": "paani"})
            writer.writerow({"hindi": "आग", "english": "fire", "roman": "aag"})

        entries = load_supplemental(tmp_path)
        assert len(entries) == 2
        assert entries[0]["word_hindi"] == "पानी"
        assert entries[0]["definition"] == "water"

    def test_load_json_array(self, tmp_path):
        json_file = tmp_path / "test.json"
        data = [
            {"word_hindi": "चाय", "definition": "tea", "word_hinglish_roman": "chai"},
        ]
        json_file.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

        entries = load_supplemental(tmp_path)
        assert len(entries) == 1
        assert entries[0]["word_hindi"] == "चाय"

    def test_load_jsonl(self, tmp_path):
        jsonl_file = tmp_path / "test.jsonl"
        lines = [
            json.dumps({"hindi": "किताब", "meaning": "book"}),
            json.dumps({"hindi": "कलम", "meaning": "pen"}),
        ]
        jsonl_file.write_text("\n".join(lines), encoding="utf-8")

        entries = load_supplemental(tmp_path)
        assert len(entries) == 2

    def test_empty_directory(self, tmp_path):
        entries = load_supplemental(tmp_path)
        assert entries == []

    def test_schema_compliance(self, tmp_path):
        csv_file = tmp_path / "test.csv"
        with open(csv_file, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["hindi", "english"])
            writer.writeheader()
            writer.writerow({"hindi": "नमस्ते", "english": "hello"})

        entries = load_supplemental(tmp_path)
        entry = entries[0]
        required_fields = ["id", "word_hindi", "definition", "source", "confidence_score"]
        for field in required_fields:
            assert field in entry, f"Missing field: {field}"
