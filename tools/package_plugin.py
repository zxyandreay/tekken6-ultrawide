#!/usr/bin/env python3
from pathlib import Path
import argparse
import zipfile

PLUGIN_PREFIX = "PSP/PLUGINS/Tekken6Ultrawide"
CHEAT_PATH = "PSP/Cheats/ULUS10466.ini"

parser = argparse.ArgumentParser()
parser.add_argument("--prx", required=True, type=Path)
parser.add_argument("--output", required=True, type=Path)
args = parser.parse_args()

root = Path(__file__).parents[1]
args.output.parent.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(args.output, "w", zipfile.ZIP_DEFLATED) as z:
    z.write(args.prx, f"{PLUGIN_PREFIX}/Tekken6Ultrawide.prx")
    z.write(root / "plugin/config/plugin.ini", f"{PLUGIN_PREFIX}/plugin.ini")
    z.write(root / "ULUS10466.ini", CHEAT_PATH)
    z.write(root / "README-PLUGIN.md", "README-PLUGIN.md")
print(args.output)
