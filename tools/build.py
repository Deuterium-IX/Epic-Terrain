"""Validate and package the opt-in Minecraft 1.21.1 data pack (Python 3.10+)."""
from pathlib import Path
import hashlib
import json
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "versions/1.20.5-1.21.4"
VERSION = "0.1.4-d9.1"


def load(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"Duplicate key {key} in {path}")
            result[key] = value
        return result
    return json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=unique)


def validate():
    data = {p.relative_to(SOURCE).as_posix(): load(p) for p in SOURCE.rglob("*.json")}
    assert load(SOURCE / "pack.mcmeta")["pack"]["pack_format"] == 48
    # The only vanilla additions are optional UI selection and custom biome tag members.
    for name, value in data.items():
        assert "/dimension/" not in name, f"Auto-loaded dimension: {name}"
        if name.startswith("data/minecraft/"):
            assert name.startswith(("data/minecraft/tags/worldgen/biome/",
                                    "data/minecraft/tags/worldgen/world_preset/")), name
            assert value.get("replace") is False, name
            assert all(isinstance(x, str) and x.startswith("etn:") for x in value["values"]), name
    preset = data["data/etn/worldgen/world_preset/epic_terrain.json"]["dimensions"]
    assert set(preset) == {"minecraft:overworld", "minecraft:the_nether", "minecraft:the_end"}
    assert preset["minecraft:overworld"]["type"] == "etn:epic/overworld"
    assert preset["minecraft:overworld"]["generator"]["settings"] == "etn:epic/overworld"
    assert data["data/etn/dimension_type/epic/overworld.json"]["effects"] == "minecraft:overworld"
    for dimension, settings in [("the_nether", "nether"), ("the_end", "end")]:
        entry = preset[f"minecraft:{dimension}"]
        assert entry["type"] == f"minecraft:{dimension}"
        assert entry["generator"]["type"] == "minecraft:noise"
        assert entry["generator"]["settings"] == f"minecraft:{settings}"
    assert not list(SOURCE.rglob("*.mcfunction")), "Unexpected global behavior"
    return data


def build():
    data = validate()
    output = ROOT / "dist" / f"epic-terrain-{VERSION}-mc1.21.1.zip"
    output.parent.mkdir(exist_ok=True)
    # Stable order and timestamps make identical sources produce identical archives.
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(p for p in SOURCE.rglob("*") if p.is_file()):
            info = zipfile.ZipInfo(path.relative_to(SOURCE).as_posix(), (2026, 9, 16, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            if path.suffix == ".json" or path.name == "pack.mcmeta":
                content = (json.dumps(load(path), ensure_ascii=False, indent=2) + "\n").encode("utf-8")
            else:
                content = path.read_bytes()
            archive.writestr(info, content)
        archive.writestr(zipfile.ZipInfo("LICENSE", (2026, 9, 16, 0, 0, 0)),
                         (ROOT / "LICENSE").read_text(encoding="utf-8-sig").encode("utf-8"))
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix(".zip.sha256").write_text(f"{digest}  {output.name}\n", encoding="utf-8")
    print(f"Validated {len(data)} JSON files. Built {output.name}\nSHA-256 {digest}")
    return output


if __name__ == "__main__":
    build()
