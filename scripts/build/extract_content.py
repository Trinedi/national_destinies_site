#!/usr/bin/env python3
"""Write what the mod gives each formable, ready to draw.

For every formable the mod has content for, this reads the country's own
files (formation event, timed modifiers, advances, destiny tree, units,
levies, buildings, bureaucracies) and writes dist/data/content/<key>.json
with every name in English and every number formatted the way the game's
tooltips show it. The icons the content refers to are converted from the
game's and the mod's DDS files into dist/icons/.

A formable's files are named after its key (`RUM_f` gives `nd_rum`), which
is not always its tag. Formables that share one country's content (the three
Irelands) share one content file.

Run with --report to list what could not be named, formatted or drawn.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image

from parse_formables import expand_path, load_config
from parse_localization import parse_dir
from render_requirements import UNWORDED_CONDITIONS, parse, prettify, render_clauses, strip_ref

FILE_KEY_RE = re.compile(r"^(?:\d+_0?)?nd_(.+)\.txt$")
NUMBER_RE = re.compile(r"^-?\d+(?:\.\d+)?$")

AGES = [
    "age_1_traditions", "age_2_renaissance", "age_3_discovery",
    "age_4_reformation", "age_5_absolutism", "age_6_revolutions",
]

ADVANCE_UNLOCKS = {
    "unlock_building": "building",
    "unlock_unit": "unit",
    "unlock_levy": "levy",
    "unlock_production_method": "production_method",
    "unlock_policy": "policy",
    "unlock_government_reform": "reform",
    "unlock_cabinet_action": "cabinet_action",
    "unlock_subject_type": "subject_type",
    "unlock_town_rights": "town_rights",
}
ADVANCE_STRUCTURE_KEYS = {
    "age", "potential", "icon", "requires", "ai_weight", "allow", "depth",
    "allow_children",
}

# How a unit's own numbers read. Under copy_from they are added to the
# template (in_game/common/unit_types/readme.txt), so each is shown signed.
UNIT_STAT_FORMAT = {
    "max_strength": "men", "crew_size": "men",
    "combat_power": "flat", "initiative": "flat", "frontage": "flat",
    "hull_size": "flat", "cannons": "flat", "artillery_barrage": "flat",
    "transport_capacity": "flat", "blockade_capacity": "flat",
    "maritime_presence": "flat", "anti_piracy_warfare": "flat",
    "combat_speed": "flat", "supply_weight": "flat",
    "food_storage_per_strength": "flat", "food_consumption_per_strength": "flat",
    "morale_damage_done": "percent", "morale_damage_taken": "percent",
    "strength_damage_done": "percent", "strength_damage_taken": "percent",
    "attrition_loss": "percent", "flanking_ability": "percent",
    "secure_flanks_defense": "percent", "movement_speed": "flat",
    "bombard_efficiency": "percent",
}
UNIT_STATS_WHERE_LESS_IS_BETTER = {
    "morale_damage_taken", "strength_damage_taken", "attrition_loss",
    "supply_weight", "food_consumption_per_strength",
}

BUILDING_MODIFIER_BLOCKS = {
    "modifier": "Per level, in its location",
    # Not multiplied by the level (in_game/common/building_types/readme.txt).
    "raw_modifier": "In its location, whatever its level",
    "capital_modifier": "In the capital",
    "capital_country_modifier": "To the country, when built in the capital",
    "market_center_modifier": "In a market centre",
}

# Names the game shows without a text key of that name.
TEXT_THE_GAME_LACKS = {
    "game_concept_supply_weight": "Supply Weight",
    "river": "River",
    "coastal": "Coast",
    "inland": "Inland",
}

# Event keys and their text keys carry a dot (`nd_mex.1.t`), which the
# statement parser does not read as part of a name.
DOT = "_DOT_"
DOTTED_NAME_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\.(?=[A-Za-z0-9_])")


def protect_dots(text: str) -> str:
    previous = None
    while previous != text:
        previous = text
        text = DOTTED_NAME_RE.sub(rf"\1{DOT}", text)
    return text


def restore_dots(name: str) -> str:
    return name.replace(DOT, ".")


STAGE_TAKEN_SUFFIX = "_taken"

COUNTRY_FILE_DIRS = (
    "in_game/common/advances", "in_game/events", "in_game/common/unit_types",
    "in_game/common/building_types", "in_game/common/bureaucracies",
    "main_menu/common/static_modifiers",
)

ICONS_IN_USE_DIR = "data/cache/icons_in_use"
ICON_SIZES = {
    "advance": 88, "modifier": 40, "building": 88, "goods": 48,
    "estate": 48, "age": 64, "unit": 64, "bureaucracy": 88,
}


class Report:
    def __init__(self) -> None:
        self.unnamed = Counter()
        self.unknown_keys = Counter()
        self.unresolved_values = Counter()
        self.missing_icons = Counter()

    def print(self) -> None:
        for title, counter in (
            ("Names with no English text", self.unnamed),
            ("Keys that are neither a modifier nor known structure", self.unknown_keys),
            ("Values that are not a number or a known named value", self.unresolved_values),
            ("Icons with no file", self.missing_icons),
        ):
            print(f"\n{title}: {len(counter)} distinct, {sum(counter.values())} uses")
            for name, n in counter.most_common(25):
                print(f"  {n:5d}  {name}")


class Game:
    """The lookups every section needs: text, modifier formats, named values, icons."""

    def __init__(self, game_root: Path, mod_root: Path, report: Report) -> None:
        self.game_root = game_root
        self.mod_root = mod_root
        self.report = report
        self.loc = {}
        for root in (game_root, mod_root):
            self.loc.update(parse_dir(root / "main_menu/localization/english"))
            self.loc.update(parse_dir(root / "in_game/localization/english"))
        self.modifier_formats = self._load_modifier_formats()
        self.named_values = self._load_named_values()
        self.modifier_icon_paths = self._load_modifier_icon_paths()
        self.goods = self._top_level_keys("in_game/common/goods")
        self.vanilla_advance_icons = self._load_vanilla_advance_icons()
        for key, fallback in TEXT_THE_GAME_LACKS.items():
            self.loc.setdefault(key, fallback)
        self.icon_sources: dict[str, Path] = {}

    def _files(self, relative_dir: str) -> list[Path]:
        files: list[Path] = []
        for root in (self.game_root, self.mod_root):
            files.extend(sorted((root / relative_dir).glob("*.txt")))
        return files

    def _statements(self, relative_dir: str):
        for path in self._files(relative_dir):
            yield from parse(path.read_text(encoding="utf-8-sig"))

    def _top_level_keys(self, relative_dir: str) -> set[str]:
        return {s[1] for s in self._statements(relative_dir) if s[0] == "block"}

    def _load_modifier_formats(self) -> dict[str, dict]:
        formats: dict[str, dict] = {}
        for s in self._statements("main_menu/common/modifier_type_definitions"):
            if s[0] != "block":
                continue
            formats[s[1]] = {c[1]: c[3] for c in s[3] if c[0] == "atom"}
        return formats

    def _load_named_values(self) -> dict[str, float]:
        values: dict[str, float] = {}
        for relative_dir in ("main_menu/common/script_values", "in_game/common/script_values"):
            for s in self._statements(relative_dir):
                if s[0] == "atom" and NUMBER_RE.match(s[3]):
                    values[s[1]] = float(s[3])
        return values

    def _load_modifier_icon_paths(self) -> dict[str, dict[str, str]]:
        paths: dict[str, dict[str, str]] = {}
        for s in self._statements("main_menu/common/modifier_icons"):
            if s[0] != "block":
                continue
            paths[s[1]] = {c[1]: c[3] for c in s[3] if c[0] == "atom"}
        return paths

    def _load_vanilla_advance_icons(self) -> dict[str, str]:
        icons: dict[str, str] = {}
        for path in sorted((self.game_root / "in_game/common/advances").glob("*.txt")):
            for s in parse(path.read_text(encoding="utf-8-sig")):
                if s[0] == "block":
                    icons[s[1]] = atoms(s[3]).get("icon", s[1])
        return icons

    def advance_icon(self, icon_name: str | None) -> str | None:
        """An advance's icon is the name of a picture file. Where the mod
        names a vanilla advance instead, the picture that advance uses is
        the one meant."""
        if not icon_name:
            return None
        inherited = self.vanilla_advance_icons.get(icon_name, icon_name)
        return self.icon(
            "advance",
            f"gfx/interface/advance/{icon_name}.dds",
            f"gfx/interface/advance/{inherited}.dds",
        )

    # ---- text -----------------------------------------------------------

    def text(self, key: str | None) -> str | None:
        if not key or key not in self.loc:
            return None
        return self.clean(self.loc[key])

    def name(self, key: str, *alternatives: str) -> str:
        for candidate in (key, *alternatives):
            found = self.text(candidate)
            if found:
                return found
        self.report.unnamed[key] += 1
        return prettify(key)

    def clean(self, text: str, depth: int = 0) -> str:
        if depth < 5:
            text = re.sub(
                r"\$([A-Za-z_][A-Za-z0-9_.]*)\$",
                lambda m: self.clean(self.loc[m.group(1)], depth + 1)
                if m.group(1) in self.loc else prettify(m.group(1)),
                text,
            )
        text = re.sub(r"\[([A-Za-z_0-9]+)\|[A-Za-z]+\]", self._concept_name, text)
        text = re.sub(r"\[[^\]]*\]", "", text)
        text = re.sub(r"#[A-Za-z_]+(?:;[A-Za-z_]+)*\s", "", text).replace("#!", "")
        text = re.sub(r"@[A-Za-z_0-9]+!", "", text)
        return re.sub(r"[ \t]{2,}", " ", text).strip()

    def conditions(self, statements: list) -> list[dict]:
        """A trigger block as English lines, with every text key inside a
        line resolved and its styling marks removed."""
        def cleaned(clause: dict) -> dict:
            clause["text"] = self.clean(clause["text"])
            for child in clause.get("children", []):
                cleaned(child)
            return clause
        return [cleaned(clause) for clause in render_clauses(statements, self.loc)]

    def _concept_name(self, match: re.Match) -> str:
        concept = match.group(1)
        named = self.loc.get(f"game_concept_{concept}")
        return self.clean(named, 5) if named else concept.replace("_", " ")

    # ---- numbers --------------------------------------------------------

    def number(self, raw: str) -> float | None:
        if NUMBER_RE.match(raw):
            return float(raw)
        if raw in self.named_values:
            return self.named_values[raw]
        return None

    def effect(self, key: str, raw: str) -> dict:
        """One modifier line: its name, its value as the game prints it, and
        whether the game would colour it as good."""
        fmt = self.modifier_formats.get(key, {})
        out = {"name": self.name(f"MODIFIER_TYPE_NAME_{key}"), "icon": self.modifier_icon(key, raw)}
        if fmt.get("boolean") == "yes":
            out["value"] = "Yes" if raw == "yes" else "No"
            if fmt.get("color") != "neutral":
                out["good"] = (raw == "yes") == (fmt.get("color") != "bad")
            return out
        value = self.number(raw)
        if value is None:
            self.report.unresolved_values[f"{key} = {raw}"] += 1
            return out
        out["value"] = format_signed(value, fmt)
        colour = fmt.get("color", "good")
        if colour != "neutral" and value != 0:
            out["good"] = (value > 0) == (colour == "good")
        return out

    def effects(self, statements: list) -> list[dict]:
        out = []
        for s in statements:
            if s[0] != "atom":
                continue
            if s[1] in self.modifier_formats:
                out.append(self.effect(s[1], s[3]))
        return out

    # ---- icons ----------------------------------------------------------

    def icon(self, pool: str, *relative_paths: str) -> str | None:
        """Register the first of the given icon files that exists and return
        its address on the site. An icon shared by many things is stored once."""
        for relative in relative_paths:
            ref = f"{pool}/{Path(relative).stem}"
            if ref in self.icon_sources:
                return ref
            for root in (self.mod_root, self.game_root):
                source = root / "main_menu" / relative
                if source.exists():
                    self.icon_sources[ref] = source
                    return ref
        self.report.missing_icons[f"{pool}/{Path(relative_paths[0]).stem}"] += 1
        return None

    def modifier_icon(self, key: str, raw: str) -> str | None:
        entry = self.modifier_icon_paths.get(key)
        if not entry:
            return None
        value = self.number(raw)
        side = "negative" if value is not None and value < 0 and "negative" in entry else "positive"
        relative = entry.get(side)
        if not relative:
            return None
        return self.icon("modifier", relative)

    def write_icons(self, icons_dir: Path, in_use_lists: Path, step: str) -> int:
        """Convert the icons this step uses, and remove the icons no step
        uses any more. Each step that draws icons keeps a list of its own in
        `in_use_lists`, so one step does not remove another's."""
        written = 0
        in_use_lists.mkdir(parents=True, exist_ok=True)
        (in_use_lists / f"{step}.json").write_text(json.dumps(sorted(self.icon_sources)))
        in_use = {
            icons_dir / f"{ref}.webp"
            for listed in in_use_lists.glob("*.json")
            for ref in json.loads(listed.read_text())
        }
        for stale in icons_dir.rglob("*.webp"):
            if stale not in in_use:
                stale.unlink()
        for ref, source in self.icon_sources.items():
            target = icons_dir / f"{ref}.webp"
            if target.exists() and target.stat().st_mtime >= source.stat().st_mtime:
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            size = ICON_SIZES[ref.split("/")[0]]
            with Image.open(source) as image:
                image = image.convert("RGBA")
                image.thumbnail((size, size), Image.LANCZOS)
                image.save(target, "WEBP", quality=82, method=4)
            written += 1
        return written


def format_signed(value: float, fmt: dict) -> str:
    if fmt.get("percent") == "yes" and fmt.get("already_percent") != "yes":
        value *= 100
    decimals = int(fmt.get("decimals", 2))
    # A value smaller than the game's two decimals (0.004 manpower a month)
    # would print as zero, so it gets the decimals it needs.
    while value and round(value, decimals) == 0 and decimals < 6:
        decimals += 1
    text = f"{value:+.{decimals}f}"
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    if fmt.get("percent") == "yes" or fmt.get("already_percent") == "yes":
        text += "%"
    return text


def atoms(statements: list) -> dict[str, str]:
    return {s[1]: s[3] for s in statements if s[0] == "atom"}


def block(statements: list, key: str) -> list | None:
    for s in statements:
        if s[0] == "block" and s[1] == key:
            return s[3]
    return None


def walk(statements: list):
    """Every statement at any depth."""
    for s in statements:
        yield s
        if s[0] == "block":
            yield from walk(s[3])


def bare_names(text: str, key: str) -> list[str]:
    """The names inside `key = { a b c }`, which the statement parser drops
    because they are not assignments."""
    match = re.search(rf"\b{key}\s*=\s*\{{([^{{}}]*)\}}", text)
    return match.group(1).split() if match else []


class Country:
    """One country's files, parsed."""

    def __init__(self, key: str, mod_root: Path) -> None:
        self.key = key
        self.mod_root = mod_root

    def _paths(self, relative_dir: str) -> list[Path]:
        return [
            p for p in sorted((self.mod_root / relative_dir).glob("*.txt"))
            if (m := FILE_KEY_RE.match(p.name)) and m.group(1) == self.key
        ]

    def text(self, relative_dir: str) -> str:
        return "\n".join(p.read_text(encoding="utf-8-sig") for p in self._paths(relative_dir))

    def blocks(self, relative_dir: str) -> list[tuple[str, list]]:
        return [(s[1], s[3]) for s in parse(self.text(relative_dir)) if s[0] == "block"]

    def raw_blocks(self, relative_dir: str) -> dict[str, str]:
        """Top-level blocks as text, for the bare-name lists inside them."""
        text = re.sub(r"#[^\n]*", "", self.text(relative_dir))
        out: dict[str, str] = {}
        for match in re.finditer(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*\{", text, re.MULTILINE):
            depth, i = 1, match.end()
            while depth and i < len(text):
                depth += {"{": 1, "}": -1}.get(text[i], 0)
                i += 1
            out[match.group(1)] = text[match.end():i - 1]
        return out


class ContentBuilder:
    def __init__(self, game: Game, country: Country, events_fired_on_forming: list[str]) -> None:
        self.game = game
        self.country = country
        self.events_fired_on_forming = events_fired_on_forming
        self.timed_modifiers = {
            name: game.effects(body)
            for name, body in country.blocks("main_menu/common/static_modifiers")
        }
        self.events = {
            restore_dots(s[1]): s[3]
            for s in parse(protect_dots(country.text("in_game/events")))
            if s[0] == "block"
        }
        self.advances = country.blocks("in_game/common/advances")
        self.units = dict(country.blocks("in_game/common/unit_types"))
        self.levies = dict(country.blocks("in_game/common/levies"))
        self.buildings = dict(country.blocks("in_game/common/building_types"))
        self.unlocked_by = self._unlocked_by()

    def _unlocked_by(self) -> dict[tuple[str, str], str]:
        out: dict[tuple[str, str], str] = {}
        for advance_key, body in self.advances:
            for s in body:
                if s[0] == "atom" and s[1] in ADVANCE_UNLOCKS:
                    out.setdefault((ADVANCE_UNLOCKS[s[1]], s[3]), advance_key)
        return out

    def build(self) -> dict:
        out = {
            "formation": self.formation(),
            "ages": self.ages(),
            "destiny": self.destiny(),
            "units": self.unit_cards(),
            "buildings": self.building_cards(),
            "bureaucracies": self.bureaucracy_cards(),
        }
        out["counts"] = {
            "choices": len(out["formation"]["options"]) if out["formation"] else 0,
            "advances": sum(len(a["advances"]) for a in out["ages"]),
            "destiny": len(out["destiny"]),
            "units": len(out["units"]),
            "buildings": len(out["buildings"]),
            "bureaucracies": len(out["bureaucracies"]["list"]) if out["bureaucracies"] else 0,
        }
        return out

    # ---- events ---------------------------------------------------------

    def event_card(self, event_key: str) -> dict | None:
        body = self.events.get(event_key)
        if body is None:
            return None
        fields = atoms(body)
        options = []
        for s in body:
            if s[0] != "block" or s[1] != "option":
                continue
            option_fields = {k: restore_dots(v) for k, v in atoms(s[3]).items()}
            modifiers = []
            for inner in walk(s[3]):
                if inner[0] == "block" and inner[1] == "add_country_modifier":
                    modifiers.append(self.timed_modifier(atoms(inner[3])))
            options.append({
                "text": self.game.name(option_fields.get("name", "")),
                "modifiers": [m for m in modifiers if m],
            })
        # A description that varies is a block of candidates, of which the
        # last has no condition.
        descriptions = [
            restore_dots(s[3]) for s in walk(body) if s[0] == "atom" and s[1] == "desc"
        ]
        return {
            "title": self.game.name(restore_dots(fields.get("title", f"{event_key}.t"))),
            "text": self.game.text(descriptions[-1] if descriptions else f"{event_key}.d"),
            "options": options,
        }

    def timed_modifier(self, fields: dict[str, str]) -> dict | None:
        key = fields.get("modifier")
        if not key:
            return None
        duration = None
        for unit in ("years", "months", "days"):
            if unit in fields:
                amount = fields[unit]
                duration = f"{amount} {unit if amount != '1' else unit[:-1]}"
        return {
            "name": self.game.name(f"STATIC_MODIFIER_NAME_{key}"),
            "text": self.game.text(f"STATIC_MODIFIER_DESC_{key}"),
            "duration": duration,
            "effects": self.timed_modifiers.get(key, []),
        }

    def formation(self) -> dict | None:
        """The country's own event among those its formation fires. Where
        one only asks a question and leads on to another (the Danubian
        Monarchy), the one whose options grant the timed modifiers is shown."""
        cards = [self.event_card(e) for e in self.events_fired_on_forming if e in self.events]
        with_modifiers = [c for c in cards if any(o["modifiers"] for o in c["options"])]
        return (with_modifiers or cards or [None])[0]

    def events_by_advance(self) -> dict[str, str]:
        out: dict[str, str] = {}
        for event_key, body in self.events.items():
            trigger = block(body, "trigger") or []
            for s in walk(trigger):
                if s[0] == "atom" and s[1] == "has_advance":
                    out.setdefault(s[3], event_key)
        return out

    # ---- advances -------------------------------------------------------

    def is_destiny(self, advance_key: str, body: list) -> bool:
        potential = block(body, "potential") or []
        return any(
            s[0] == "atom" and s[1] == "has_game_rule" and s[3] == "nd_destinies_enabled"
            for s in walk(potential)
        )

    def advance_card(self, advance_key: str, body: list, events: dict[str, str]) -> dict:
        fields = atoms(body)
        unlocks = []
        for s in body:
            if s[0] != "atom":
                continue
            if s[1] in ADVANCE_UNLOCKS:
                unlocks.append(self.unlock(ADVANCE_UNLOCKS[s[1]], s[3]))
            elif s[1] not in ADVANCE_STRUCTURE_KEYS and s[1] not in self.game.modifier_formats:
                self.game.report.unknown_keys[f"advance: {s[1]}"] += 1
        card = {
            "key": advance_key,
            "name": self.game.name(advance_key),
            "text": self.game.text(f"{advance_key}_desc"),
            "icon": self.game.advance_icon(fields.get("icon")),
            "effects": self.game.effects(body),
            "unlocks": unlocks,
        }
        allow = block(body, "allow")
        if allow:
            card["conditions"] = self.game.conditions(allow)
        if advance_key in events:
            card["event"] = self.event_card(events[advance_key])
        return card

    def unlock(self, kind: str, key: str) -> dict:
        if kind == "levy":
            unit_key = atoms(self.levies.get(key, [])).get("unit", key)
            return {"kind": "levy", "key": unit_key, "name": self.game.name(unit_key)}
        if kind == "production_method":
            for building_key, body in self.buildings.items():
                methods = block(body, "unique_production_methods") or []
                if any(m[1] == key for m in methods):
                    return {"kind": kind, "key": building_key, "name": self.game.name(key),
                            "of": self.game.name(building_key)}
        return {"kind": kind, "key": key, "name": self.game.name(key)}

    def ages(self) -> list[dict]:
        events = self.events_by_advance()
        by_age: dict[str, list[dict]] = defaultdict(list)
        for advance_key, body in self.advances:
            if self.is_destiny(advance_key, body):
                continue
            by_age[atoms(body).get("age", "")].append(self.advance_card(advance_key, body, events))
        return [
            {
                "key": age,
                "name": self.game.name(age),
                "icon": self.game.icon("age", f"gfx/interface/icons/age/{age}.dds"),
                "advances": by_age[age],
            }
            for age in AGES if by_age.get(age)
        ]

    def destiny(self) -> list[dict]:
        events = self.events_by_advance()
        stages = []
        for advance_key, body in self.advances:
            if not self.is_destiny(advance_key, body):
                continue
            card = self.advance_card(advance_key, body, events)
            card["requires"] = atoms(body).get("requires")
            stages.append(card)
        own_keys = {stage["key"] for stage in stages}
        bodies = dict(self.advances)
        for stage in stages:
            if stage["requires"] not in own_keys:
                stage["requires"] = self.stage_named_in_allow(bodies[stage["key"]], own_keys)
        return stages

    def stage_named_in_allow(self, body: list, own_keys: set[str]) -> str | None:
        """A tree whose stages hang from vanilla advances orders them in
        `allow` instead, by the marker an earlier stage leaves
        (`has_variable = nd_dnm_dest_sava_line_taken`)."""
        for s in walk(block(body, "allow") or []):
            if s[0] == "atom" and s[1] == "has_variable" and s[3].endswith(STAGE_TAKEN_SUFFIX):
                earlier = s[3][: -len(STAGE_TAKEN_SUFFIX)]
                if earlier in own_keys:
                    return earlier
        return None

    # ---- units ----------------------------------------------------------

    def unit_cards(self) -> list[dict]:
        levy_of_unit: dict[str, tuple[str, list]] = {}
        for levy_key, body in self.levies.items():
            unit_key = atoms(body).get("unit")
            if unit_key:
                levy_of_unit.setdefault(unit_key, (levy_key, body))
        cards = []
        for unit_key, body in self.units.items():
            fields = atoms(body)
            category = fields.get("category")
            stats = [
                self.unit_stat(s[1], s[3]) for s in body
                if s[0] == "atom" and s[1] in UNIT_STAT_FORMAT
            ]
            for terrain_block, label in (("combat", "Combat in"), ("impact", "Speed in")):
                for s in block(body, terrain_block) or []:
                    if s[0] == "atom":
                        stats.append(self.terrain_stat(label, s[1], s[3], terrain_block))
            card = {
                "key": unit_key,
                "name": self.game.name(unit_key),
                "text": self.game.text(f"{unit_key}_desc"),
                "category": self.game.name(category) if category else None,
                "icon": self.game.icon("unit", f"gfx/interface/icons/unit_category/{category}.dds")
                if category else None,
                "stats": [s for s in stats if s],
                "upgrades_to": self.game.name(fields["upgrades_to"]) if "upgrades_to" in fields else None,
            }
            if unit_key in levy_of_unit:
                levy_key, levy_body = levy_of_unit[unit_key]
                card["levy"] = {
                    "pops": [self.game.name(s[3]) for s in levy_body
                             if s[0] == "atom" and s[1] == "allowed_pop_type"],
                    "cultures": [self.game.name(strip_ref(s[3])) for s in levy_body
                                 if s[0] == "atom" and s[1] == "allowed_culture"],
                }
                unlocker = self.unlocked_by.get(("levy", levy_key))
            else:
                unlocker = None
            unlocker = unlocker or self.unlocked_by.get(("unit", unit_key))
            if unlocker:
                card["unlocked_by"] = self.game.name(unlocker)
            cards.append(card)
        return cards

    def unit_stat(self, key: str, raw: str) -> dict | None:
        value = self.game.number(raw)
        if value is None or value == 0:
            return None
        kind = UNIT_STAT_FORMAT[key]
        if kind == "percent":
            shown = format_signed(value, {"percent": "yes"})
        elif kind == "men":
            shown = f"{value * 1000:+,.0f} men"
        else:
            shown = format_signed(value, {})
        return {
            "name": self.game.name(f"game_concept_{key}"),
            "value": shown,
            "good": (value > 0) != (key in UNIT_STATS_WHERE_LESS_IS_BETTER),
        }

    def terrain_stat(self, label: str, terrain: str, raw: str, terrain_block: str) -> dict | None:
        value = self.game.number(raw)
        if value is None or value == 0:
            return None
        # `impact` slows the unit down, so a positive number there is the bad one.
        return {
            "name": f"{label} {self.game.name(terrain).lower()}",
            "value": format_signed(value, {"percent": "yes"}),
            "good": (value > 0) == (terrain_block == "combat"),
        }

    # ---- buildings ------------------------------------------------------

    def building_cards(self) -> list[dict]:
        cards = []
        for building_key, body in self.buildings.items():
            fields = atoms(body)
            category = fields.get("category")
            settlements = [
                label for flag, label in (
                    ("rural_settlement", "Rural"), ("town", "Town"),
                    ("city", "City"), ("megalopolis", "Megalopolis"),
                ) if fields.get(flag) == "yes"
            ]
            effect_groups = []
            for block_key, label in BUILDING_MODIFIER_BLOCKS.items():
                effects = self.game.effects(block(body, block_key) or [])
                if effects:
                    effect_groups.append({"label": label, "effects": effects})
            card = {
                "key": building_key,
                "name": self.game.name(building_key),
                "text": self.game.text(f"{building_key}_desc"),
                "icon": self.game.icon(
                    "building",
                    f"gfx/interface/icons/buildings/{building_key}.dds",
                    f"gfx/interface/icons/building_categories/{category}.dds",
                ),
                "category": self.game.name(category) if category else None,
                "workers": self.game.name(fields["pop_type"]) if "pop_type" in fields else None,
                "max_levels": self.max_levels(fields.get("max_levels")),
                "settlements": settlements,
                "effect_groups": effect_groups,
                "methods": self.production_methods(block(body, "unique_production_methods") or []),
            }
            where = block(body, "location_potential")
            if where:
                card["where"] = self.game.conditions(where)
            unlocker = self.unlocked_by.get(("building", building_key))
            if not unlocker:
                for s in walk(block(body, "country_potential") or []):
                    if s[0] == "atom" and s[1] == "has_advance":
                        unlocker = s[3]
                        break
            if unlocker:
                card["unlocked_by"] = self.game.name(unlocker)
            cards.append(card)
        return cards

    def max_levels(self, raw: str | None) -> str | None:
        """The level cap as a whole number; a cap worked out by script is not shown."""
        value = self.game.number(raw) if raw else None
        return f"{value:g}" if value is not None else None

    def production_methods(self, methods: list) -> list[dict]:
        out = []
        for method in methods:
            if method[0] != "block":
                continue
            fields = atoms(method[3])
            inputs = [
                self.goods_amount(s[1], s[3]) for s in method[3]
                if s[0] == "atom" and s[1] in self.game.goods
            ]
            produced = fields.get("produced")
            out.append({
                "name": self.game.name(method[1]),
                "inputs": inputs,
                "output": self.goods_amount(produced, fields.get("output", "")) if produced else None,
                "effects": self.game.effects(method[3]),
                "unlocked_by": self.game.name(self.unlocked_by[("production_method", method[1])])
                if ("production_method", method[1]) in self.unlocked_by else None,
            })
        return out

    def goods_amount(self, good: str, raw: str) -> dict:
        value = self.game.number(raw)
        return {
            "name": self.game.name(good),
            "amount": f"{value:.2f}".rstrip("0").rstrip(".") if value is not None else None,
            "icon": self.game.icon("goods", f"gfx/interface/icons/trade_goods/icon_goods_{good}.dds"),
        }

    # ---- bureaucracies --------------------------------------------------

    def bureaucracy_cards(self) -> dict | None:
        blocks = self.country.blocks("in_game/common/bureaucracies")
        if not blocks:
            return None
        raw = self.country.raw_blocks("in_game/common/bureaucracies")
        cards = []
        for bureaucracy_key, body in blocks:
            card = {
                "key": bureaucracy_key,
                "name": self.game.name(bureaucracy_key),
                "text": self.game.text(f"{bureaucracy_key}_desc"),
                "icon": self.game.icon(
                    "bureaucracy",
                    f"gfx/interface/icons/bureaucracy/{bureaucracy_key}.dds",
                ),
                "likes": [self.estate(e) for e in bare_names(raw.get(bureaucracy_key, ""), "estates_that_like")],
                "dislikes": [self.estate(e) for e in bare_names(raw.get(bureaucracy_key, ""), "estates_that_dislike")],
                "always": self.game.effects(block(body, "neutral_modifier") or []),
                "funded": self.game.effects(block(body, "positive_modifier") or []),
                "neglected": self.game.effects(block(body, "negative_modifier") or []),
            }
            allow = block(body, "allow")
            if allow:
                card["conditions"] = self.game.conditions(allow)
            cards.append(card)
        slots = None
        for _, body in self.country.blocks("main_menu/common/auto_modifiers"):
            raw_slots = atoms(body).get("global_max_bureaucracy_slots")
            if raw_slots and NUMBER_RE.match(raw_slots):
                slots = int(float(raw_slots))
        return {"slots": slots, "list": cards}

    def estate(self, estate_key: str) -> dict:
        return {
            "name": self.game.name(estate_key),
            "icon": self.game.icon("estate", f"gfx/interface/icons/estates/{estate_key}.dds"),
        }


def content_key_for(record: dict, keys_with_content: set[str]) -> str | None:
    block_key = record["block_key"]
    candidates = [block_key[:-2].lower() if block_key.endswith("_f") else block_key.lower()]
    event = record.get("formation_event") or ""
    if event.startswith("nd_"):
        candidates.append(event.split(".")[0][3:])
    if record.get("tag"):
        candidates.append(record["tag"].lower())
    for candidate in candidates:
        if candidate in keys_with_content:
            return candidate
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", action="store_true",
                        help="List what could not be named, formatted or drawn")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    config = load_config(repo_root)
    mod_root = expand_path(config["mod_root"])
    game_root = expand_path(config["eu5_game_root"])
    web_data_dir = repo_root / config["build"]["web_data_dir"]
    content_dir = web_data_dir / "content"
    icons_dir = repo_root / config["build"]["dist_dir"] / "icons"

    report = Report()
    game = Game(game_root, mod_root, report)

    keys_with_content = {
        m.group(1)
        for relative_dir in COUNTRY_FILE_DIRS
        for p in (mod_root / relative_dir).glob("*.txt")
        if (m := FILE_KEY_RE.match(p.name))
    }

    formables_path = web_data_dir / "formables.json"
    data = json.loads(formables_path.read_text())
    content_dir.mkdir(parents=True, exist_ok=True)
    written: dict[str, dict] = {}
    for record in data["formables"]:
        record.pop("content", None)
        key = content_key_for(record, keys_with_content)
        if key is None:
            continue
        if key not in written:
            fired = re.findall(r"trigger_event\w*\s*=\s*([A-Za-z_0-9.]+)", record.get("form_effect_raw") or "")
            builder = ContentBuilder(game, Country(key, mod_root), fired)
            content = builder.build()
            written[key] = content["counts"]
            if any(content["counts"].values()):
                (content_dir / f"{key}.json").write_text(
                    json.dumps(content, ensure_ascii=False, separators=(",", ":")))
        # A country whose files hold nothing the tab draws gets no tab.
        if any(written[key].values()):
            record["content"] = {"key": key, "counts": written[key]}

    for stale in content_dir.glob("*.json"):
        if not any(written.get(stale.stem, {}).values()):
            stale.unlink()
    formables_path.write_text(json.dumps(data, ensure_ascii=False, indent=1))

    new_icons = game.write_icons(icons_dir, repo_root / ICONS_IN_USE_DIR, "content")
    totals = Counter()
    for counts in written.values():
        totals.update(counts)
    print(f"content for {sum(1 for c in written.values() if any(c.values()))} countries: " +
          ", ".join(f"{n} {name}" for name, n in totals.items()))
    print(f"icons: {len(game.icon_sources)} in use, {new_icons} converted")
    unused = sorted(keys_with_content - set(written))
    if unused:
        print(f"files that belong to no formable: {', '.join(unused)}")
    if args.report:
        report.print()
        print(f"\nConditions with no wording of their own: {len(UNWORDED_CONDITIONS)} distinct")
        for name, n in UNWORDED_CONDITIONS.most_common(70):
            print(f"  {n:5d}  {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
