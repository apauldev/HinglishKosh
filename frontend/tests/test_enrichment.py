"""Tests for enrichment data integrity."""

from __future__ import annotations


def test_relation_fields_exist_on_synset_entries(sample_entries):
    """Most entries with synsets should have at least one relation field.

    Some synsets are solitary (single member) or have no hypernymy linkage,
    so a tiny fraction may have zero relations. We allow <1% headroom.
    """
    total = 0
    missing = []
    for entry in sample_entries:
        if not entry.get("synsets"):
            continue
        total += 1
        has_same = bool(entry.get("same_synset"))
        has_broader = bool(entry.get("broader_terms"))
        has_narrower = bool(entry.get("narrower_terms"))
        if not (has_same or has_broader or has_narrower):
            missing.append(f"{entry['id']} ({entry.get('word_hindi')})")
    threshold = max(1, int(total * 0.01))
    assert len(missing) <= threshold, (
        f"{len(missing)}/{total} entries with synsets have no relation fields "
        f"(threshold {threshold}): {missing[:5]}"
    )


def test_known_synset_members(sample_entries):
    """Synset iwn-1 should contain known members."""
    target_ids = {"अजन्मा", "अजात", "अनुत्पन्न", "अनुद्भूत", "अप्रादुर्भूत", "अज"}
    members = set()
    for entry in sample_entries:
        if "iwn-1" in entry.get("synsets", []):
            members.add(entry["word_hindi"])
    overlap = members & target_ids
    assert len(overlap) >= 3, (
        f"Expected at least 3 of {target_ids} in iwn-1, got {overlap}"
    )


def test_known_broader_terms(all_entries):
    """पवित्र स्थान should have स्थान in broader_terms."""
    for entry in all_entries:
        if entry["word_hindi"] == "पवित्र स्थान":
            broader_names = {r["word_hindi"] for r in entry.get("broader_terms", [])}
            assert "स्थान" in broader_names, (
                f"पवित्र स्थान should have स्थान as broader term, got {broader_names}"
            )
            return
    pytest.fail("पवित्र स्थान not found in dataset")


def test_known_narrower_terms(all_entries):
    """पवित्र स्थान should have पूजाघर in narrower_terms."""
    for entry in all_entries:
        if entry["word_hindi"] == "पवित्र स्थान":
            narrower_names = {r["word_hindi"] for r in entry.get("narrower_terms", [])}
            assert "पूजाघर" in narrower_names, (
                f"पवित्र स्थान should have पूजाघर as narrower term, got {narrower_names}"
            )
            return
    pytest.fail("पवित्र स्थान not found in dataset")


def test_no_self_references(all_entries):
    """An entry should never reference itself in any relation."""
    self_refs = []
    for entry in all_entries:
        eid = entry["id"]
        for key in ("same_synset", "broader_terms", "narrower_terms"):
            for rel in entry.get(key, []):
                if rel["id"] == eid:
                    self_refs.append(f"{eid} in {key}")
    assert len(self_refs) == 0, f"{len(self_refs)} self-references found: {self_refs[:10]}"


def test_no_orphan_relations(full_db):
    """All related_entry_id values must exist as entry ids."""
    orphans = full_db.execute("""
        SELECT r.entry_id, r.related_entry_id, r.relation_type
        FROM related_words r
        LEFT JOIN entries e ON e.id = r.related_entry_id
        WHERE e.id IS NULL
    """).fetchall()
    assert len(orphans) == 0, (
        f"{len(orphans)} orphan relations found: {[dict(o) for o in orphans[:5]]}"
    )


def test_relation_ids_are_valid(full_db):
    """All entry_id values in related_words must be valid entry ids."""
    orphans = full_db.execute("""
        SELECT r.entry_id, r.related_entry_id, r.relation_type
        FROM related_words r
        LEFT JOIN entries e ON e.id = r.entry_id
        WHERE e.id IS NULL
    """).fetchall()
    assert len(orphans) == 0, (
        f"{len(orphans)} relations with invalid source entry_id: {[dict(o) for o in orphans[:5]]}"
    )
