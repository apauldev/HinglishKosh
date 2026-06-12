"""Enrich the dictionary dataset with related word relationships.

Reads the merged dataset JSON and WordNet hypernymy files, then adds:
- same_synset_members: other entries sharing a synset
- broader_terms: entries in parent (hypernym) synsets
- narrower_terms: entries in child (hyponym) synsets

Usage:
    python frontend/src/seed/enrich.py
    python frontend/src/seed/enrich.py --input data/output/hinglish_dictionary_v1.json --output data/output/hinglish_dictionary_v1.json
"""

from __future__ import annotations

import argparse
import json
import logging
from collections import defaultdict
from pathlib import Path
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

SYNSET_PREFIX = "iwn-"


def load_hypernymy(data_dir: Path) -> dict[str, list[str]]:
    """Load hypernymy relations from WordNet data.

    Returns mapping: child_synset_id -> list of parent synset IDs
    (e.g., "11" -> ["2377"] meaning iwn-11 is-a iwn-2377)
    """
    child_to_parents: dict[str, list[str]] = defaultdict(list)
    parent_to_children: dict[str, list[str]] = defaultdict(list)

    for filename in ["hypernymy.noun", "hypernymy.verb"]:
        path = data_dir / "wordnet" / "iwn_data" / "synset_relations" / filename
        if not path.exists():
            logger.warning("Hypernymy file not found: %s", path)
            continue

        count = 0
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split("\t")
                if len(parts) != 2:
                    continue
                child, parent = parts[0], parts[1]
                child_to_parents[child].append(parent)
                parent_to_children[parent].append(child)
                count += 1
        logger.info("Loaded %d relations from %s", count, path)

    return {
        "child_to_parents": dict(child_to_parents),
        "parent_to_children": dict(parent_to_children),
    }


def build_synset_index(
    entries: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """Build index of synset_id -> entries belonging to that synset.

    Synset IDs in the dataset have 'iwn-' prefix.
    """
    synset_index: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry in entries:
        for synset_id in entry.get("synsets", []):
            synset_index[synset_id].append(entry)
    return dict(synset_index)


def extract_related(
    entry: dict[str, Any],
    synset_index: dict[str, list[dict[str, Any]]],
    relations: dict[str, list[str]],
    max_per_group: int = 20,
) -> dict[str, list[dict[str, Any]]]:
    """Extract related words for a single entry.

    Returns dict with keys: same_synset, broader_terms, narrower_terms
    Each value is a list of dicts with word_hindi, word_hinglish_roman, id
    """
    entry_synsets = entry.get("synsets", [])
    entry_hindi = entry.get("word_hindi", "")
    entry_id = entry.get("id", "")

    child_to_parents = relations["child_to_parents"]
    parent_to_children = relations["parent_to_children"]

    related: dict[str, list[dict[str, Any]]] = {
        "same_synset": [],
        "broader_terms": [],
        "narrower_terms": [],
    }

    seen_same: set[str] = set()
    seen_broader: set[str] = set()
    seen_narrower: set[str] = set()

    for synset_id in entry_synsets:
        # Strip 'iwn-' prefix to look up in hypernymy files
        raw_id = synset_id.replace(SYNSET_PREFIX, "")

        # Same synset members (excluding self)
        for member in synset_index.get(synset_id, []):
            mid = member.get("id", "")
            if mid != entry_id and mid not in seen_same:
                seen_same.add(mid)
                related["same_synset"].append(
                    {
                        "id": mid,
                        "word_hindi": member.get("word_hindi", ""),
                        "word_hinglish_roman": member.get("word_hinglish_roman", ""),
                    }
                )

        # Broader terms: parent synsets
        for parent_raw in child_to_parents.get(raw_id, []):
            parent_id = SYNSET_PREFIX + parent_raw
            for member in synset_index.get(parent_id, []):
                mid = member.get("id", "")
                if mid != entry_id and mid not in seen_broader:
                    seen_broader.add(mid)
                    related["broader_terms"].append(
                        {
                            "id": mid,
                            "word_hindi": member.get("word_hindi", ""),
                            "word_hinglish_roman": member.get("word_hinglish_roman", ""),
                        }
                    )

        # Narrower terms: child synsets
        for child_raw in parent_to_children.get(raw_id, []):
            child_id = SYNSET_PREFIX + child_raw
            for member in synset_index.get(child_id, []):
                mid = member.get("id", "")
                if mid != entry_id and mid not in seen_narrower:
                    seen_narrower.add(mid)
                    related["narrower_terms"].append(
                        {
                            "id": mid,
                            "word_hindi": member.get("word_hindi", ""),
                            "word_hinglish_roman": member.get("word_hinglish_roman", ""),
                        }
                    )

    # Trim to max per group to avoid bloating entries
    for key in related:
        if len(related[key]) > max_per_group:
            logger.debug(
                "Truncating %s for %s from %d to %d",
                key,
                entry_hindi,
                len(related[key]),
                max_per_group,
            )
            related[key] = related[key][:max_per_group]

    return related


def enrich(
    input_path: Path,
    output_path: Path,
    data_dir: Path,
    max_per_group: int = 20,
):
    """Main enrichment function."""
    # Load dataset
    logger.info("Loading dataset from %s", input_path)
    with open(input_path, encoding="utf-8") as f:
        dataset = json.load(f)

    entries = dataset.get("dictionary", [])
    logger.info("Loaded %d entries", len(entries))

    # Load hypernymy relations
    relations = load_hypernymy(data_dir)

    # Build synset index
    synset_index = build_synset_index(entries)
    logger.info(
        "Built synset index: %d synsets with entries",
        len(synset_index),
    )

    # Enrich each entry
    enriched_count = 0
    for entry in entries:
        if not entry.get("synsets"):
            continue
        related = extract_related(entry, synset_index, relations, max_per_group)
        added = False
        for key, values in related.items():
            if values:
                entry[key] = values
                added = True
        if added:
            enriched_count += 1

    dataset["meta"]["enriched"] = True
    dataset["meta"]["entries_with_relations"] = enriched_count
    dataset["meta"]["total_relations"] = sum(
        len(e.get("same_synset", []))
        + len(e.get("broader_terms", []))
        + len(e.get("narrower_terms", []))
        for e in entries
    )

    logger.info("Enriched %d entries with related words", enriched_count)
    total_relations = dataset["meta"]["total_relations"]
    logger.info("Total relation links added: %d", total_relations)

    # Write enriched dataset
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)
    logger.info("Wrote enriched dataset to %s", output_path)

    # Also write compact version
    compact_path = output_path.with_suffix(".min.json")
    with open(compact_path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, separators=(",", ":"))
    logger.info("Wrote compact enriched dataset to %s", compact_path)


def main():
    parser = argparse.ArgumentParser(description="Enrich dictionary with related words")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/output/hinglish_dictionary_v1.json"),
        help="Input dataset JSON",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/output/hinglish_dictionary_v1.json"),
        help="Output enriched JSON (can be same as input)",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data/raw"),
        help="Data directory containing WordNet files",
    )
    parser.add_argument(
        "--max-per-group",
        type=int,
        default=20,
        help="Maximum related words per category",
    )
    args = parser.parse_args()

    enrich(
        input_path=args.input,
        output_path=args.output,
        data_dir=args.data_dir,
        max_per_group=args.max_per_group,
    )


if __name__ == "__main__":
    main()
