from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import yaml

from test_datapack_harness import HARNESS


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "datapack-smith"
SPEC = importlib.util.spec_from_file_location("okf_index", SKILL / "tools/okf_index.py")
assert SPEC is not None and SPEC.loader is not None
OKF = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(OKF)


class KnowledgeTests(unittest.TestCase):
    def write_concept(self, path: Path, **extra: object) -> None:
        metadata = {
            "type": "Reference",
            "title": "Lootの仕様",
            "description": "対象バージョンのlootを調べる。",
            "tags": ["loot", "minecraft-java"],
            **extra,
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "---\n" + yaml.safe_dump(metadata, allow_unicode=True)
            + "---\n\n# Loot\n",
            encoding="utf-8",
        )

    def test_bundle_metadata_and_indexes_are_current(self) -> None:
        count, errors = OKF.maintain_indexes(SKILL / "docs")
        self.assertGreater(count, 75)
        self.assertEqual([], errors)

    def test_indexes_discover_nested_concepts_and_track_metadata_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            concept = root / "reference/loot.md"
            self.write_concept(concept)
            self.assertTrue(OKF.maintain_indexes(root)[1])
            self.assertEqual((1, []), OKF.maintain_indexes(root, write=True))
            index = (root / "index.md").read_text()
            self.assertIn("reference/index.md", index)
            self.assertIn('okf_version: "0.2"', index)
            child_index = (root / "reference/index.md").read_text()
            self.assertFalse(child_index.startswith("---"))
            self.assertIn("[Lootの仕様](loot.md) - 対象バージョンのlootを調べる。", child_index)
            self.write_concept(concept, description="更新されたlootの仕様。")
            self.assertTrue(OKF.maintain_indexes(root)[1])
            self.assertEqual((1, []), OKF.maintain_indexes(root, write=True))
            self.assertEqual((1, []), OKF.maintain_indexes(root))

    def test_new_types_extensions_and_absent_optional_trust_are_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "concept.md"
            self.write_concept(path, type="Future Concept", extension={"value": 7})
            concept = OKF.read_concept(path)
            self.assertEqual({"value": 7}, concept["extension"])
            self.assertNotIn("verified", concept)
            self.assertEqual((1, []), OKF.maintain_indexes(path.parent, write=True))

    def test_invalid_metadata_does_not_overwrite_existing_index(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "loot.md"
            self.write_concept(path)
            OKF.maintain_indexes(root, write=True)
            before = (root / "index.md").read_bytes()
            for invalid in ({"type": ""}, {"tags": "loot"}, {"sources": [{}]}):
                with self.subTest(invalid=invalid):
                    self.write_concept(path, **invalid)
                    self.assertTrue(OKF.maintain_indexes(root, write=True)[1])
                    self.assertEqual(before, (root / "index.md").read_bytes())
            path.write_text("---\ntype: [broken\n---\n# Loot\n")
            self.assertTrue(OKF.maintain_indexes(root)[1])

    def test_profile_reader_preserves_okf_metadata_and_game_contract(self) -> None:
        profiles = HARNESS.load_profiles()
        payload = HARNESS.resolved_profile_payload("1.21.5", profiles)
        profile = payload["profile"]
        self.assertEqual("Minecraft Version", profile["type"])
        self.assertIn("1.21.5", profile["tags"])
        self.assertTrue(profile["sources"][0]["resource"].startswith("https://"))
        self.assertTrue(any(source["resource"].startswith("https://minecraft.wiki/") for source in profile["sources"]))
        self.assertEqual("71", profile["data_pack_format"])
        original = profiles["1.21.5"]
        metadata = {
            "future_okf_extension": {"keep": True},
            "verified": {"by": "process:example", "at": "2026-11-17T00:00:00Z"},
        }
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "1.21.5.md"
            text = original["_path"].read_text()
            extension = "\n".join(f"{key}: {json.dumps(value)}" for key, value in metadata.items())
            path.write_text(text.replace("---\n", "---\n" + extension + "\n", 1))
            extended = HARNESS.read_profile(path)
            profiles["1.21.5"] = extended
            self.assertEqual([], HARNESS.validate_profile(extended, profiles))
            for key, value in metadata.items():
                self.assertEqual(value, HARNESS.public_profile(extended)[key])
            extended["data_pack_format"] = "invalid"
            self.assertTrue(HARNESS.validate_profile(extended, profiles))

    def test_minimal_okf_concept_needs_neither_index_nor_optional_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "minimal.md").write_text(
                '---\ntype: Future Concept\ncustom: {retained: true}\n---\n'
                '# Minimal\n[Unwritten concept](/future.md)\n'
            )
            self.assertEqual((1, []), OKF.maintain_indexes(root, conformance_only=True))
            self.assertFalse((root / "index.md").exists())
            self.assertTrue(OKF.maintain_indexes(root)[1])

    def test_conformance_does_not_impose_single_line_types_or_log_title(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "concept.md").write_text('---\ntype: |\n  Future\n  Concept\n---\n# Concept\n')
            (root / "log.md").write_text('## 2026-11-17\n- Creation.\n')
            self.assertEqual((1, []), OKF.maintain_indexes(root, conformance_only=True))
            self.assertTrue(OKF.maintain_indexes(root)[1])

    def test_reserved_files_are_validated_instead_of_skipped(self) -> None:
        invalid_files = {
            "nested/index.md": '---\ntype: Reference\n---\n# Index\n',
            "index.md": '---\ntype: Reference\n---\n# Index\n',
            "log.md": '# Updates\n\n## 2026-02-30\n- Impossible date.\n',
            "nested/log.md": '# Updates\n\n## 2026-11-16\n- Old.\n\n## 2026-11-17\n- New.\n',
        }
        for name, content in invalid_files.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content)
                self.assertTrue(OKF.maintain_indexes(root, conformance_only=True)[1])

    def test_valid_log_is_preserved_and_discoverable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.write_concept(root / "concept.md")
            log = root / "log.md"
            text = '# Updates\n\n## 2026-11-17\n- [Concept](concept.md) created.\n'
            log.write_text(text)
            self.assertEqual((1, []), OKF.maintain_indexes(root, write=True))
            self.assertEqual(text, log.read_text())
            self.assertIn("(log.md)", (root / "index.md").read_text())

    def test_provenance_ids_and_footnotes_must_join(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            concept = root / "concept.md"
            self.write_concept(concept, sources=[{"id": "source", "resource": "https://example.com"}])
            with concept.open("a") as stream:
                stream.write('Claim.[^missing]: explanation\n\n[^missing]: Source\n')
            self.assertTrue(OKF.maintain_indexes(root)[1])
            concept.write_text(concept.read_text().replace("missing", "source"))
            self.assertEqual((1, []), OKF.maintain_indexes(root, write=True))

    def test_maintenance_rejects_duplicate_yaml_keys_and_source_ids(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            concept = root / "concept.md"
            self.write_concept(concept)
            concept.write_text(concept.read_text().replace('---\n', '---\ntype: Duplicate\n', 1))
            self.assertTrue(OKF.maintain_indexes(root)[1])
            self.write_concept(concept, sources=[
                {"id": "collision", "resource": "https://example.com/one"},
                {"id": "collision", "resource": "https://example.com/two"},
            ])
            self.assertTrue(OKF.maintain_indexes(root)[1])

    def test_source_ids_cannot_silently_change_attribution_to_another_resource(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            concept = root / "concept.md"
            self.write_concept(concept, sources=[
                {"id": "first", "resource": "https://example.com/one"},
                {"id": "second", "resource": "https://example.com/two"},
            ])
            with concept.open("a") as stream:
                stream.write('\nClaim.[^first]\n\n[^first]: [Wrong](https://example.com/two)\n')
            self.assertTrue(OKF.maintain_indexes(root)[1])
            concept.write_text(concept.read_text().replace('[Wrong](https://example.com/two)', '[Right](https://example.com/one)'))
            self.assertEqual((1, []), OKF.maintain_indexes(root, write=True))

    def test_bundle_relative_source_and_relative_footnote_resolve_to_same_concept(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.write_concept(root / "source.md")
            concept = root / "nested/concept.md"
            self.write_concept(concept, sources=[{"id": "internal", "resource": "/source.md"}])
            with concept.open("a") as stream:
                stream.write('\nClaim.[^internal]\n\n[^internal]: [Source](../source.md)\n')
            self.assertEqual((2, []), OKF.maintain_indexes(root, write=True))

    def test_markdown_links_keep_parentheses_and_adjacent_citations(self) -> None:
        text = (
            '- [First](https://example.com/first)\n'
            '- [Wiki](https://example.com/Function_(Java_Edition))\n'
            '- [Profile](../versions/1.21.5.md)\n'
        )
        self.assertEqual([
            ("First", "https://example.com/first"),
            ("Wiki", "https://example.com/Function_(Java_Edition)"),
            ("Profile", "../versions/1.21.5.md"),
        ], list(OKF.markdown_links(text)))

    def test_trust_mapping_and_list_forms_are_accepted_without_fabricating_events(self) -> None:
        event = {"by": "process:review", "at": "2026-11-17T00:00:00Z"}
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "concept.md"
            for verified in (event, [event], [{"by": "human:reviewer", "at": event["at"]}]):
                self.write_concept(path, verified=verified)
                self.assertEqual(verified, OKF.read_concept(path)["verified"])
            self.write_concept(path)
            self.assertNotIn("verified", OKF.read_concept(path))
            for extra in (
                {"verified": {"by": "reviewer", "at": event["at"]}},
                {"stale_after": "2026-11-17T00:00:00"},
                {"status": "unknown"},
            ):
                self.write_concept(path, **extra)
                with self.assertRaises(ValueError):
                    OKF.read_concept(path)

    def test_optional_family_guidance_does_not_change_minimal_conformance(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.write_concept(root / "concept.md", sources=[{}])
            self.assertEqual((1, []), OKF.maintain_indexes(root, conformance_only=True))
            self.assertTrue(OKF.maintain_indexes(root)[1])

    def test_missing_external_provenance_is_reported_but_code_examples_are_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "concept.md"
            self.write_concept(path)
            with path.open("a") as stream:
                stream.write('\n~~~markdown\n[Example](https://example.com/example)\n~~~\n')
            OKF.read_concept(path)
            with path.open("a") as stream:
                stream.write('\n[Actual source](https://example.com/source)\n')
            with self.assertRaises(ValueError):
                OKF.read_concept(path)


if __name__ == "__main__":
    unittest.main()
