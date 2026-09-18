from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from test_datapack_harness import HARNESS, SKILL


class JsonBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profiles = HARNESS.load_profiles()

    def errors(self, version, family, value):
        chain = {p["version"] for p in HARNESS.resolve_chain(version, self.profiles)}
        result = HARNESS.ValidationResult()
        HARNESS.validate_json_version(value, Path("data/example") / family / "test.json", chain, result)
        return result.errors

    def test_recipe_result_boundary_does_not_mix_consumer_shapes(self):
        cases = [
            ("1.13", "crafting_shaped", {"item": "minecraft:stone"}, {"id": "minecraft:stone"}),
            ("1.14", "stonecutting", "minecraft:stone", {"item": "minecraft:stone"}),
            ("1.20.4", "smelting", "minecraft:stone", {"id": "minecraft:stone"}),
            ("1.20.5", "smelting", {"id": "minecraft:stone"}, "minecraft:stone"),
            ("1.20.5", "stonecutting", {"id": "minecraft:stone", "count": 2}, {"item": "minecraft:stone"}),
            ("1.21.11", "smelting", {"id": "minecraft:stone"}, {"id": "minecraft:stone", "count": 2}),
        ]
        for version, kind, valid, invalid in cases:
            with self.subTest(version=version, kind=kind):
                recipe = {"type": "minecraft:" + kind, "result": valid}
                self.assertEqual([], self.errors(version, "recipe", recipe))
                recipe["result"] = invalid
                self.assertTrue(self.errors(version, "recipe", recipe))
        for version in ("26.1", "26.1.1", "26.1.2", "26.2", "26.3"):
            for output in ("minecraft:stone", {"id": "minecraft:stone", "count": 2}):
                self.assertEqual([], self.errors(version, "recipe", {"type": "minecraft:smelting", "result": output, "cookingtime": 200}))

    def test_ingredient_boundary_applies_inside_shaped_and_shapeless(self):
        for kind in ("crafting_shaped", "crafting_shapeless", "smelting"):
            for version, valid, invalid in (
                ("1.21.1", {"item": "minecraft:stone"}, "minecraft:stone"),
                ("1.21.2", "minecraft:stone", {"item": "minecraft:stone"}),
            ):
                def recipe(value):
                    fields = {"key": {"S": value}} if kind == "crafting_shaped" else {"ingredients": [value]} if kind == "crafting_shapeless" else {"ingredient": value}
                    return {"type": "minecraft:" + kind, **fields}
                with self.subTest(version=version, kind=kind):
                    self.assertEqual([], self.errors(version, "recipe", recipe(valid)))
                    self.assertTrue(self.errors(version, "recipe", recipe(invalid)))

    def test_entity_predicate_and_discriminator_are_separate_boundaries(self):
        old = {"condition": "minecraft:entity_properties", "entity": "this", "predicate": {"type": "minecraft:player"}}
        component_map = copy.deepcopy(old)
        component_map["predicate"] = {"minecraft:entity_type": "minecraft:player"}
        unified = copy.deepcopy(component_map)
        unified["type"] = unified.pop("condition")
        for version, valid, invalid in (
            ("26.1.2", old, component_map),
            ("26.2", component_map, old),
            ("26.3-snapshot-3", component_map, unified),
            ("26.3-snapshot-4", unified, component_map),
            ("26.3-pre-1", unified, component_map),
            ("26.3-rc-3", unified, component_map),
            ("26.3", unified, component_map),
        ):
            with self.subTest(version=version):
                self.assertEqual([], self.errors(version, "predicate", valid))
                self.assertTrue(self.errors(version, "predicate", invalid))
        component_map["predicate"] = {"flags": {"is_sneaking": True}}
        self.assertEqual([], self.errors("26.2", "predicate", component_map))

    def test_predicate_resource_introduction_and_explicit_all_of(self):
        condition = {"condition": "minecraft:random_chance", "chance": 1.0}
        self.assertTrue(self.errors("1.14.4", "predicates", condition))
        self.assertEqual([], self.errors("1.15", "predicates", condition))
        self.assertEqual([], self.errors("1.16", "predicates", [condition]))
        modern = {"type": "minecraft:random_chance", "chance": 1.0}
        self.assertTrue(self.errors("26.3", "predicate", [modern]))
        self.assertEqual([], self.errors("26.3", "predicate", {"type": "minecraft:all_of", "terms": [modern]}))

    def test_modifier_boundary_does_not_reject_legacy_non_discriminator_type(self):
        old = {"function": "minecraft:set_loot_table", "type": "minecraft:chest", "name": "example:reward"}
        self.assertEqual([], self.errors("1.20.4", "item_modifiers", old))
        self.assertTrue(self.errors("26.3", "item_modifier", old))
        modern = {"type": "minecraft:set_count", "count": 2}
        self.assertEqual([], self.errors("26.3", "item_modifier", modern))
        self.assertTrue(self.errors("26.2", "item_modifier", modern))
        modern["condition"] = {"condition": "minecraft:random_chance", "chance": 1}
        self.assertTrue(self.errors("26.3", "item_modifier", modern))

    def test_cookingtime_begins_at_pre_release_not_first_snapshot(self):
        recipe = {"type": "minecraft:smelting", "ingredient": "minecraft:cobblestone", "result": {"id": "minecraft:stone"}}
        for version in ("26.2", "26.3-snapshot-1", "26.3-snapshot-10"):
            self.assertEqual([], self.errors(version, "recipe", recipe))
        for version in ("26.3-pre-1", "26.3-rc-3", "26.3"):
            self.assertTrue(self.errors(version, "recipe", recipe))
            self.assertEqual([], self.errors(version, "recipe", {**recipe, "cookingtime": 200}))

    def test_custom_data_and_other_resources_are_not_global_key_rewritten(self):
        self.assertEqual([], self.errors("26.3", "storage", {"type": "a", "function": "b"}))
        self.assertEqual([], self.errors("26.3", "recipe", {"type": "minecraft:crafting_shaped", "result": {"id": "minecraft:stone", "components": {"minecraft:custom_data": {"item": "user value", "condition": "user value"}}}}))


class AuthoringIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profiles = HARNESS.load_profiles()

    def pack(self, root):
        (root / "pack.mcmeta").write_text('{"pack":{"pack_format":71,"description":"test"}}')
        functions = root / "data/example/function"
        functions.mkdir(parents=True)
        (functions / "load.mcfunction").write_text("say ready\n")
        return functions

    def test_load_tag_required_optional_and_external_references(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.pack(root)
            tag = root / "data/minecraft/tags/function/load.json"
            tag.parent.mkdir(parents=True)
            tag.write_text(json.dumps({"values": ["example:load", "example:missing", "#example:missing_tag", {"id": "example:optional", "required": False}, "dependency:init"]}))
            result = HARNESS.validate_pack("1.21.5", root, None, self.profiles)
            self.assertEqual(2, len(result.errors), result.errors)
            self.assertTrue(any("missing local function example:missing" in e for e in result.errors))
            self.assertTrue(any("missing local function tag #example:missing_tag" in e for e in result.errors))
            self.assertTrue(any("dependency:init" in w for w in result.warnings))

    def test_version_checks_are_used_by_pack_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.pack(root)
            recipe = root / "data/example/recipe/old.json"
            recipe.parent.mkdir()
            recipe.write_text('{"type":"minecraft:crafting_shaped","key":{"S":{"item":"minecraft:stone"}},"result":{"item":"minecraft:stone"}}')
            result = HARNESS.validate_pack("1.21.5", root, None, self.profiles)
            self.assertEqual(2, len(result.errors), result.errors)

    def test_report_mismatch_cannot_certify_another_version(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.pack(root)
            reports = root / "reports-under-test"
            reports.mkdir()
            (reports / HARNESS.REPORT_PROVENANCE_FILE).write_text('{"version":"26.3"}')
            result = HARNESS.validate_pack("1.21.5", root, reports, self.profiles)
            self.assertTrue(any("report version" in e for e in result.errors))

    def test_generation_refuses_mixing_with_previous_files_before_download(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            existing = output / "previous.json"
            existing.write_text("{}")
            with mock.patch.object(HARNESS, "fetch_release") as fetch:
                with self.assertRaises(HARNESS.HarnessError):
                    HARNESS.run_reports("1.21.5", "java", output / "cache", output, self.profiles)
                fetch.assert_not_called()
            self.assertEqual("{}", existing.read_text())

    def test_overlay_pack_cannot_be_reported_as_fully_statically_checked(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.pack(root)
            metadata = json.loads((root / "pack.mcmeta").read_text())
            metadata["overlays"] = {"entries": [{"directory": "v1_21", "formats": 71}]}
            (root / "pack.mcmeta").write_text(json.dumps(metadata))
            result = HARNESS.validate_pack("1.21.5", root, None, self.profiles)
            self.assertTrue(any("overlay resolution" in e for e in result.errors))

    def test_macro_and_message_text_are_not_missing_function_references(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            functions = self.pack(root)
            (functions / "load.mcfunction").write_text(
                'say function example:message\n'
                '$function example:dynamic/$(name)\n'
                'execute as @a run tellraw @s {text:"function example:message"}\n'
                'execute as @a run say function example:message\n'
                'return run execute as @a run say run function example:message\n'
                'execute as @a run function example:load\n'
            )
            result = HARNESS.validate_pack("1.21.5", root, None, self.profiles)
            self.assertEqual([], result.errors)

    def test_nested_calls_and_execute_function_conditions_are_checked(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            functions = self.pack(root)
            (functions / "load.mcfunction").write_text(
                'execute if function example:condition run say done\n'
                'return run execute as @a run function example:body\n'
                'schedule function example:later 1t\n'
            )
            result = HARNESS.validate_pack("1.21.5", root, None, self.profiles)
            for name in ("condition", "body", "later"):
                self.assertTrue(any(f"missing local function example:{name}" in error for error in result.errors))

    def test_malformed_reports_raise_diagnostic_not_attribute_error(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reports = root / "reports"
            reports.mkdir()
            for content in ("[]", "{", '{"children": []}'):
                (reports / "commands.json").write_text(content)
                with self.assertRaises(HARNESS.HarnessError):
                    HARNESS.load_command_roots(root)
            (reports / "registries.json").write_text("[]")
            with self.assertRaises(HARNESS.HarnessError):
                HARNESS.load_registry_ids(root)

    def test_complete_example_is_portable_and_has_resolvable_entrypoints(self):
        import shutil
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "different-name"
            shutil.copytree(SKILL / "templates/examples/cooldown-1.21.5", root)
            config, checked = HARNESS.validate_project_config(root / "datapack-project.json", self.profiles)
            self.assertEqual([], checked.errors)
            self.assertIsNotNone(config)
            result = HARNESS.validate_pack(config["target_version"], root / config["pack_root"], None, self.profiles)
            self.assertEqual([], result.errors)


if __name__ == "__main__":
    unittest.main()
