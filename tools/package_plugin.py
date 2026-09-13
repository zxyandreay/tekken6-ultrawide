#!/usr/bin/env python3
from pathlib import Path
import argparse
import zipfile

PREFIX = "PSP/PLUGINS/Tekken6Ultrawide"

parser = argparse.ArgumentParser()
parser.add_argument("--prx", required=True, type=Path)
parser.add_argument("--output", required=True, type=Path)
args = parser.parse_args()

root = Path(__file__).parents[1]
args.output.parent.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(args.output, "w", zipfile.ZIP_DEFLATED) as z:
    z.write(args.prx, f"{PREFIX}/Tekken6Ultrawide.prx")
    z.write(root / "plugin/config/plugin.ini", f"{PREFIX}/plugin.ini")
    z.write(root / "README-PLUGIN.md", "README-PLUGIN.md")
print(args.output)
