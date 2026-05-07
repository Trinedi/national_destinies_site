#!/usr/bin/env python3
"""Parse definitions.txt into a region/area/province tree.

definitions.txt is a 5-level nested block:
  continent = { subregion = { region = { area = { province = { loc loc loc } } } } }

We emit an inverted index so the frontend can answer:
  - given a region/area, list its locations (for territory highlighting)
  - given a location, find its province/area/region/etc.

Output: data/geography.json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

import yaml


def load_config(repo_root: Path) -> dict:
    with open(repo_root / "build.config.yaml") as f:
        return yaml.safe_load(f)


def expand_path(p: str) -> Path:
    return Path(os.path.expanduser(p)).resolve()


TOKEN_RE = re.compile(r"[A-Za-z0-9_]+|[={}]")


def tokenize(text: str) -> list[str]:
    text = re.sub(r"#[^\n]*", "", text)
    return TOKEN_RE.findall(text)


class Parser:
    def __init__(self, tokens: list[str]) -> None:
        self.toks = tokens
        self.i = 0

    def peek(self, off: int = 0) -> str | None:
        j = self.i + off
        return self.toks[j] if j < len(self.toks) else None

    def take(self) -> str:
        tok = self.toks[self.i]
        self.i += 1
        return tok

    def parse_top(self) -> dict:
        out: dict = {}
        while self.i < len(self.toks):
            entry = self.parse_assignment()
            if entry is None:
                break
            k, v = entry
            out[k] = v
        return out

    def parse_assignment(self) -> tuple[str, object] | None:
        if self.i >= len(self.toks):
            return None
        name = self.take()
        if self.peek() != "=":
            raise SyntaxError(f"expected '=' after {name} at token {self.i}")
        self.take()  # '='
        if self.peek() != "{":
            raise SyntaxError(f"expected '{{' after '=' at token {self.i}")
        self.take()  # '{'
        value = self.parse_block_body()
        # parse_block_body consumes the closing '}' or raises on EOF
        return name, value

    def parse_block_body(self) -> object:
        """Inside {...}: either a dict of name=value pairs OR a leaf name list."""
        # Decide based on lookahead: if next token is '}', empty dict.
        # If pattern is `name = {`, it's a dict block. Otherwise, leaves.
        if self.peek() == "}":
            self.take()
            return {}
        if self.peek(1) == "=":
            # Dict mode
            d: dict = {}
            while self.peek() != "}":
                if self.i >= len(self.toks):
                    raise SyntaxError("unexpected EOF inside dict block")
                entry = self.parse_assignment()
                if entry is None:
                    raise SyntaxError("expected entry inside dict block")
                k, v = entry
                d[k] = v
            self.take()  # '}'
            return d
        # Leaf mode: a sequence of names until '}'
        leaves: list[str] = []
        while self.peek() != "}":
            if self.i >= len(self.toks):
                raise SyntaxError("unexpected EOF inside leaf block")
            leaves.append(self.take())
        self.take()  # '}'
        return leaves


def flatten(tree: dict) -> dict:
    """Build inverted indices from the 5-level nested tree."""
    continents: dict[str, dict] = {}
    subregions: dict[str, dict] = {}
    regions: dict[str, dict] = {}
    areas: dict[str, dict] = {}
    provinces: dict[str, dict] = {}
    locations: dict[str, dict] = {}

    for cont_name, cont in tree.items():
        cont_subregions: list[str] = []
        for sub_name, sub in cont.items():
            sub_regions: list[str] = []
            for reg_name, reg in sub.items():
                reg_areas: list[str] = []
                for area_name, area in reg.items():
                    area_provs: list[str] = []
                    for prov_name, prov in area.items():
                        # prov should be a leaf list of locations
                        if not isinstance(prov, list):
                            print(
                                f"warn: province {prov_name} is not a leaf list",
                                file=sys.stderr,
                            )
                            continue
                        provinces[prov_name] = {
                            "area": area_name,
                            "region": reg_name,
                            "subregion": sub_name,
                            "continent": cont_name,
                            "locations": list(prov),
                        }
                        for loc in prov:
                            locations[loc] = {
                                "province": prov_name,
                                "area": area_name,
                                "region": reg_name,
                                "subregion": sub_name,
                                "continent": cont_name,
                            }
                        area_provs.append(prov_name)
                    areas[area_name] = {
                        "region": reg_name,
                        "subregion": sub_name,
                        "continent": cont_name,
                        "provinces": area_provs,
                    }
                    reg_areas.append(area_name)
                regions[reg_name] = {
                    "subregion": sub_name,
                    "continent": cont_name,
                    "areas": reg_areas,
                }
                sub_regions.append(reg_name)
            subregions[sub_name] = {
                "continent": cont_name,
                "regions": sub_regions,
            }
            cont_subregions.append(sub_name)
        continents[cont_name] = {"subregions": cont_subregions}

    return {
        "continents": continents,
        "subregions": subregions,
        "regions": regions,
        "areas": areas,
        "provinces": provinces,
        "locations": locations,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    repo_root = Path(__file__).resolve().parent.parent.parent
    cfg = load_config(repo_root)
    eu5 = expand_path(cfg["eu5_game_root"])
    defs_path = eu5 / cfg["paths"]["definitions"]
    if not defs_path.exists():
        print(f"error: {defs_path} not found", file=sys.stderr)
        return 1

    print(f"reading {defs_path} ...")
    text = defs_path.read_text(encoding="utf-8-sig")
    t0 = time.time()
    tokens = tokenize(text)
    print(f"  {len(tokens)} tokens in {time.time()-t0:.2f}s")

    print("parsing ...")
    t0 = time.time()
    parser = Parser(tokens)
    tree = parser.parse_top()
    print(f"  parsed in {time.time()-t0:.2f}s")

    print("flattening ...")
    t0 = time.time()
    indices = flatten(tree)
    print(
        f"  continents={len(indices['continents'])} "
        f"subregions={len(indices['subregions'])} "
        f"regions={len(indices['regions'])} "
        f"areas={len(indices['areas'])} "
        f"provinces={len(indices['provinces'])} "
        f"locations={len(indices['locations'])} "
        f"in {time.time()-t0:.2f}s"
    )

    out_path = Path(args.out) if args.out else repo_root / cfg["build"]["data_dir"] / "geography.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump({"version": 1, **indices}, f)
    print(f"wrote {out_path} ({out_path.stat().st_size/1e6:.2f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
