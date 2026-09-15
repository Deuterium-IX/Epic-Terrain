"""Regression checks for accidental world-wide overrides and preset routing."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from build import SOURCE, load, validate


class OptInTests(unittest.TestCase):
    def test_no_implicit_dimension_or_vanilla_worldgen_overrides(self):
        validate()

    def test_vanilla_dimensions_are_unchanged_in_epic_preset(self):
        dims = load(SOURCE / "data/etn/worldgen/world_preset/epic_terrain.json")["dimensions"]
        self.assertEqual(dims["minecraft:the_nether"]["generator"]["biome_source"],
                         {"type": "minecraft:multi_noise", "preset": "minecraft:nether"})
        self.assertEqual(dims["minecraft:the_end"]["generator"]["biome_source"],
                         {"type": "minecraft:the_end"})

    def test_ui_tag_adds_option_without_replacing_default_presets(self):
        tag = load(SOURCE / "data/minecraft/tags/worldgen/world_preset/normal.json")
        self.assertEqual(tag, {"replace": False, "values": ["etn:epic_terrain"]})

    def test_custom_swamps_keep_surface_rules(self):
        import json
        preset = load(SOURCE / "data/etn/worldgen/world_preset/epic_terrain.json")
        source = preset["dimensions"]["minecraft:overworld"]["generator"]["biome_source"]
        biomes = {x["biome"] for x in source["biomes"]}
        rules = json.dumps(load(SOURCE / "data/etn/worldgen/noise_settings/epic/overworld.json")["surface_rule"])
        for name in ("swamp", "mangrove_swamp"):
            self.assertIn(f"etn:epic/{name}", biomes)
            self.assertNotIn(f"minecraft:{name}", biomes)
            self.assertIn(f'"etn:epic/{name}"', rules)
        # A surface-condition type has the same name as a relocated noise resource.
        self.assertIn('"minecraft:temperature"', rules)
        self.assertNotIn('"type": "etn:', rules)

    def test_inherited_shifts_use_epic_offset_without_changing_vanilla(self):
        for axis in ("x", "z"):
            shift = load(SOURCE / f"data/etn/worldgen/density_function/vanilla/shift_{axis}.json")
            self.assertIn('etn:epic/offset', str(shift))
            self.assertFalse((SOURCE / f"data/minecraft/worldgen/density_function/shift_{axis}.json").exists())

    def test_lake_count_provider_uses_1_21_1_codec_shape(self):
        placed = load(SOURCE / "data/etn/worldgen/placed_feature/lake_water_surface.json")
        provider = placed["placement"][0]["count"]["distribution"][0]["data"]
        self.assertEqual(provider, {"type": "minecraft:biased_to_bottom",
                                    "min_inclusive": 5, "max_inclusive": 15})


if __name__ == "__main__":
    unittest.main()
