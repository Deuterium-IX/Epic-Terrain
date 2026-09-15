"""Isolated Youer/MV smoke test. Requires an existing accepted-EULA runtime and nbtlib.

Copies only libraries, youer.jar and eula.txt from the supplied template. Never
copies worlds/configuration or changes the template. All output stays in build/.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
import time
import zlib
import io

import nbtlib
from build import ROOT, build

SEED = 246813579
SAMPLES = [(256, 256), (-257, 193)]


def block_payload(path, cx, cz):
    region = path / "region" / f"r.{cx // 32}.{cz // 32}.mca"
    with region.open("rb") as f:
        f.seek(4 * ((cx % 32) + 32 * (cz % 32)))
        location = int.from_bytes(f.read(4), "big")
        assert location >> 8, f"Missing chunk {cx},{cz} in {path}"
        f.seek((location >> 8) * 4096)
        size = struct.unpack(">I", f.read(4))[0]
        compression = f.read(1)[0]
        assert compression == 2, f"Unexpected MCA compression {compression}"
        chunk = nbtlib.File.parse(io.BytesIO(zlib.decompress(f.read(size - 1))))
    assert str(chunk["Status"]) == "minecraft:full", (path, cx, cz, chunk["Status"])
    # Exclude timestamps, entities and lighting; compare terrain and biome content.
    payload = nbtlib.Compound({"sections": nbtlib.List[nbtlib.Compound]([
        nbtlib.Compound({k: section[k] for k in ("Y", "block_states", "biomes") if k in section})
        for section in chunk["sections"]
    ])})
    buf = io.BytesIO()
    payload.write(buf)
    biomes = []
    for section in sorted(chunk["sections"], key=lambda s: int(s["Y"])):
        container = section["biomes"]
        palette = list(map(str, container["palette"]))
        if len(palette) == 1:
            values = palette * 64
        else:
            bits = max(1, (len(palette) - 1).bit_length())
            per_long = 64 // bits
            values = [palette[(int(container["data"][i // per_long]) >>
                               (bits * (i % per_long))) & ((1 << bits) - 1)] for i in range(64)]
        biomes.append((int(section["Y"]), values))
    def digest(value):
        return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()
    return {
        "blockAndBiomeNbtHash": hashlib.sha256(buf.getvalue()).hexdigest(),
        "oceanFloorHash": digest([int(x) for x in chunk["Heightmaps"]["OCEAN_FLOOR"]]),
        "biomeHash": digest(biomes),
    }


def metadata(path):
    data = nbtlib.load(path / "level.dat")["Data"]
    dims = data["WorldGenSettings"]["dimensions"]
    return {str(key): {"type": str(value["type"]),
                       "settings": str(value["generator"].get("settings", ""))}
            for key, value in dims.items()}


def verify_run(run):
    evidence = json.loads((run / "evidence.json").read_text())
    cases = {}
    for label in ("baseline", "normal-with-pack", "epic-with-pack"):
        cases[label] = {}
        for name in ("world", "resource"):
            root = run / label / name
            cases[label][name] = {"dimensions": metadata(root),
                                  "samples": [block_payload(root, x, z) for x, z in SAMPLES]}
    def shape_and_biomes(world):
        return [(s["oceanFloorHash"], s["biomeHash"]) for s in world["samples"]]
    for label in cases:
        assert shape_and_biomes(cases[label]["resource"]) == shape_and_biomes(cases["baseline"]["resource"]), label
        assert cases[label]["resource"]["dimensions"]["minecraft:overworld"] == {
            "type": "minecraft:overworld", "settings": "minecraft:overworld"}, label
    assert shape_and_biomes(cases["normal-with-pack"]["world"]) == shape_and_biomes(cases["baseline"]["world"])
    assert cases["normal-with-pack"]["world"]["dimensions"] == cases["baseline"]["world"]["dimensions"]
    assert shape_and_biomes(cases["epic-with-pack"]["world"]) != shape_and_biomes(cases["baseline"]["world"])
    assert cases["epic-with-pack"]["world"]["dimensions"]["minecraft:overworld"] == {
        "type": "etn:epic/overworld", "settings": "etn:epic/overworld"}
    evidence["cases"] = cases
    evidence["comparison"] = "OCEAN_FLOOR heightmap and decoded per-position biome palette"
    evidence["limitation"] = (
        "Full block NBT hashes are diagnostic only: repeated no-EPC baseline runs also differed "
        "in ore and vegetation placement. No claim of bit-identical decoration or every block."
    )
    evidence["passed"] = True
    (run / "evidence.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print("PASS: normal terrain height/biomes match baseline; explicit EPC differs; MV resources reload and match.", flush=True)


class Server:
    def __init__(self, root, java, round_name):
        self.root = root
        self.log = root / f"console-{round_name}.log"
        self.output = self.log.open("wb")
        self.process = subprocess.Popen([
            java, "-Xms512M", "-Xmx2G", "-Dterminal.jline=false", "-Dterminal.ansi=false",
            "-jar", "youer.jar", "nogui",
        ], cwd=root, stdin=subprocess.PIPE, stdout=self.output, stderr=subprocess.STDOUT)

    def text(self):
        return self.log.read_text(encoding="utf-8", errors="replace")

    def wait(self, marker, timeout=240, offset=0):
        start = time.monotonic()
        while time.monotonic() - start < timeout:
            if self.process.poll() is not None:
                raise RuntimeError(f"Server exited; inspect {self.log}")
            if marker in self.text()[offset:]:
                return
            time.sleep(0.5)
        raise TimeoutError(f"Waiting for {marker}; inspect {self.log}")

    def command(self, text):
        self.process.stdin.write((text + "\n").encode("utf-8"))
        self.process.stdin.flush()

    def ready(self):
        self.wait("Done (")
        self.command("gamerule spawnChunkRadius 0")
        self.command("datapack list enabled")
        self.command("mv list")

    def sample(self, dimension, index):
        cx, cz = SAMPLES[index]
        x, z = cx * 16, cz * 16
        self.command(f"execute in {dimension} run forceload add {x} {z}")
        marker = f"EPC_SMOKE_LOADED_{dimension}_{index}"
        start = time.monotonic()
        offset = len(self.text())
        while marker not in self.text()[offset:]:
            if self.process.poll() is not None or time.monotonic() - start > 180:
                raise RuntimeError(f"Sample did not load: {dimension}; inspect {self.log}")
            self.command(f"execute in {dimension} if loaded {x} 64 {z} run say {marker}")
            time.sleep(1)
        self.command(f"execute in {dimension} run forceload remove {x} {z}")

    def stop(self):
        if self.process.poll() is None:
            self.command("stop")
            try:
                self.process.wait(timeout=90)
            except subprocess.TimeoutExpired:
                self.process.terminate()
                self.process.wait(timeout=15)
                raise RuntimeError(f"Server failed to stop cleanly; inspect {self.log}")
        self.output.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", type=Path)
    parser.add_argument("--mv-jar", type=Path)
    parser.add_argument("--yourfix-jar", type=Path)
    parser.add_argument("--java")
    parser.add_argument("--verify-only", type=Path, help="Recheck saved chunks from a completed, stopped run")
    parser.add_argument("--port", type=int, default=25686)
    args = parser.parse_args()
    if args.verify_only:
        verify_run(args.verify_only)
        return
    if not all((args.template, args.mv_jar, args.yourfix_jar, args.java)):
        parser.error("--template, --mv-jar, --yourfix-jar and --java are required for a server run")
    assert "eula=true" in (args.template / "eula.txt").read_text(encoding="utf-8-sig")
    pack = build()
    run = ROOT / "build" / f"smoke-{time.strftime('%Y%m%d-%H%M%S')}"
    run.mkdir(parents=True)
    evidence = {"seed": SEED, "sampleChunks": SAMPLES, "cases": {}, "sha256": {
        "pack": hashlib.sha256(pack.read_bytes()).hexdigest(),
        "youer": hashlib.sha256((args.template / "youer.jar").read_bytes()).hexdigest(),
        "mv": hashlib.sha256(args.mv_jar.read_bytes()).hexdigest(),
        "yourfix": hashlib.sha256(args.yourfix_jar.read_bytes()).hexdigest(),
    }}
    print(f"Smoke test output: {run}", flush=True)
    for label, enabled, preset in [("baseline", False, "minecraft:normal"),
                                    ("normal-with-pack", True, "minecraft:normal"),
                                    ("epic-with-pack", True, "etn:epic_terrain")]:
        root = run / label
        root.mkdir()
        shutil.copytree(args.template / "libraries", root / "libraries")
        for name in ("youer.jar", "eula.txt"):
            shutil.copy2(args.template / name, root / name)
        for folder, artifact in [("plugins", args.mv_jar), ("mods", args.yourfix_jar)]:
            (root / folder).mkdir()
            shutil.copy2(artifact, root / folder / artifact.name)
        # Stock MV 5.8.1 on this Youer build repeats the End import on restart,
        # even without EPC. Keep automatic loading of registered MV worlds, but
        # disable discovery/import of server-owned worlds in all three cases.
        mv_config = root / "plugins/Multiverse-Core"
        mv_config.mkdir()
        (mv_config / "config.yml").write_text(
            "world:\n  auto-import-default-worlds: false\n"
            "  auto-import-3rd-party-worlds: false\n", encoding="utf-8")
        packs = "vanilla,mod_data"
        if enabled:
            (root / "world/datapacks").mkdir(parents=True)
            shutil.copy2(pack, root / "world/datapacks/epic-terrain-d9.zip")
            packs += ",file/epic-terrain-d9.zip"
        (root / "server.properties").write_text(
            f"server-ip=127.0.0.1\nserver-port={args.port}\nonline-mode=false\n"
            f"level-name=world\nlevel-seed={SEED}\nlevel-type={preset}\n"
            f"initial-enabled-packs={packs}\nview-distance=3\nsimulation-distance=3\n"
            "sync-chunk-writes=true\nmax-players=1\nenable-rcon=false\n", encoding="utf-8")
        for round_number in range(2):
            print(f"START {label} round {round_number + 1}", flush=True)
            server = Server(root, args.java, str(round_number + 1))
            try:
                server.ready()
                if round_number == 0:
                    server.command(f"mv create resource normal --seed {SEED}")
                    server.wait("World 'resource' created!", timeout=180)
                for dimension in ("minecraft:overworld", "minecraft:resource"):
                    server.sample(dimension, round_number)
            finally:
                server.stop()
            print(f"STOP {label} round {round_number + 1}", flush=True)
        worlds = {}
        for name in ("world", "resource"):
            worlds[name] = {"dimensions": metadata(root / name),
                            "samples": [block_payload(root / name, x, z) for x, z in SAMPLES]}
        evidence["cases"][label] = worlds
        (run / "evidence.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    verify_run(run)


if __name__ == "__main__":
    main()
