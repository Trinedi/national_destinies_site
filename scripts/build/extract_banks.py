#!/usr/bin/env python3
"""Write what the mod's bank system holds, ready to draw on the Banks page.

Reads the bank files of the mod (laws, privileges, the bank's value, its
advances and buildings, every action, the bank run, the two organisations
and the countries a bank can become) and writes dist/data/banks.json, with
every name in English and every number formatted as the game shows it.

The bank's advances and buildings are read like a country's (the files are
named nd_bank), so they come out as the same cards the Content tab draws.

Run with --report to list what could not be named, formatted or drawn.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from extract_content import ICONS_IN_USE_DIR, ContentBuilder, Country, Game, Report, atoms, block, walk
from parse_formables import expand_path, load_config
from render_requirements import parse

BANK_FILES_KEY = "bank"
COMMON = "in_game/common"

# The page groups a bank's actions the way a player meets them. An action
# file that is new lands under "Other" until it is given a group here.
ACTION_GROUPS = {
    "country_interactions/99_nd_bank_ask_loan.txt": "Loans",
    "country_interactions/99_nd_bank_pledge.txt": "Loans",
    "country_interactions/99_nd_bank_buy_back.txt": "Loans",
    "country_interactions/99_nd_bank_war_bond.txt": "Wars",
    "country_interactions/99_nd_bank_finance_war.txt": "Wars",
    "country_interactions/99_nd_bank_debt_war.txt": "Wars",
    "generic_actions/99_nd_bank_war.txt": "Wars",
    "generic_actions/99_nd_bank_standing.txt": "Standing",
    "country_interactions/99_nd_bank_close_offices.txt": "Standing",
    "country_interactions/99_nd_bank_crown.txt": "Standing",
    "generic_actions/99_nd_bank_standing_rivals.txt": "Rival banks",
    "generic_actions/99_nd_bank.txt": "Patronage",
}
ACTION_GROUP_ORDER = ["Loans", "Wars", "Standing", "Rival banks", "Patronage", "Other"]
ACTION_FILES_SHOWN_ELSEWHERE = {
    "generic_actions/99_nd_bank_run.txt",
    "country_interactions/99_nd_bank_house.txt",
    # These two change interactions of the base game and add none.
    "country_interactions/99_nd_bank_take_over_loan.txt",
    "country_interactions/99_nd_bank_vanilla_replace.txt",
}

STANDING_STEPS = [
    ("nd_bank_gui_band_stranger", None),
    ("nd_bank_gui_band_known", "nd_bank_st_known_from"),
    ("nd_bank_gui_band_trusted", "nd_bank_st_trusted_from"),
    ("game_concept_nd_bank_court_banker", "nd_bank_st_court_from"),
    ("game_concept_nd_bank_master_of_the_purse", "nd_bank_st_master_from"),
]
STANDING_CONCEPTS = [
    "nd_bank_standing", "nd_bank_hold", "nd_bank_court_banker",
    "nd_bank_master_of_the_purse", "nd_bank_charter", "nd_bank_client",
]

ORGANISATIONS = [
    {
        "key": "nd_money_market",
        "laws": "laws/99_nd_money_market.txt",
        "statuses": "international_organization_special_statuses/99_nd_money_market.txt",
    },
    {
        "key": "nd_bank_house",
        "laws": "laws/99_nd_bank_house.txt",
        "statuses": "international_organization_special_statuses/99_nd_bank_house.txt",
        "payments": "international_organization_payments/99_nd_bank_house.txt",
        "subjects": "subject_types/99_nd_bank.txt",
        "actions": "country_interactions/99_nd_bank_house.txt",
    },
]

# A bank becomes a country through one action. Its requirements are the
# tooltip lines of the trigger named <prefix>_requirements_met. The country
# is a formable of the mod, or the country whose name the action's effects
# give to the bank's subject.
COUNTRY_ROADS = [
    {"action": "nd_rsg_proclaim_republic", "file": "generic_actions/99_nd_rsg.txt",
     "prefix": "nd_rsg", "formable": "RSG_f"},
    {"action": "nd_acc_proclaim_dukes", "file": "generic_actions/99_nd_acc_athens.txt",
     "prefix": "nd_acc", "effects": "scripted_effects/nd_acc_athens_effects.txt"},
    {"action": "nd_mnd_ask_naxos", "file": "generic_actions/99_nd_mnd_naxos.txt",
     "prefix": "nd_mnd", "effects": "scripted_effects/nd_mnd_naxos_effects.txt"},
    {"action": "nd_kwh_raise_counts", "file": "generic_actions/99_nd_kwh.txt",
     "prefix": "nd_kwh", "formable": "KWH_f"},
]

MODIFIER_BLOCKS_OF_A_POLICY = ("country_modifier",)
BANK_REFORM = "banking_country"
CONDITIONS_NOT_SHOWN = {"nd_bank_rule_on", "nd_bank_land_on", "nd_bank_is_bank", "hidden_trigger"}
NAME_GIVEN_TO_A_SUBJECT = re.compile(r"copy_country_name_and_adjective\s*=\s*c:([A-Z][A-Z0-9]{2,4})")
# A bank the game creates during play is named where it is created, some
# lines above the tag it is given.
NAME_BEFORE_ITS_TAG = r"\bname\s*=\s*(\w+)(?:(?!\bname\s*=)[\s\S]){{0,1500}}?define_unique_country_tag\s*=\s*{tag}\b"


def shown_conditions(statements: list) -> list:
    """A trigger without what the page's reader need not be told: that the
    bank rule is on, that the country is a bank, and what the game hides."""
    out = []
    for s in statements:
        if s[1] in CONDITIONS_NOT_SHOWN:
            continue
        out.append((s[0], s[1], s[2], shown_conditions(s[3])) if s[0] == "block" else s)
    return out


class Banks:
    def __init__(self, game: Game, mod_root: Path, game_root: Path, formables: list[dict]) -> None:
        self.game = game
        self.mod_root = mod_root
        self.game_root = game_root
        self.formables = {f["block_key"]: f for f in formables}
        self.unplaced_action_files: list[str] = []

    def blocks(self, relative: str) -> list[tuple[str, list]]:
        text = (self.mod_root / COMMON / relative).read_text(encoding="utf-8-sig")
        return [(s[1], s[3]) for s in parse(text) if s[0] == "block"]

    def text(self, key: str) -> str | None:
        return self.game.text(key)

    def country_name(self, tag: str) -> str:
        """A country's name, also for a bank the game creates during play,
        which has no text under its tag."""
        if self.text(tag):
            return self.text(tag)
        pattern = re.compile(NAME_BEFORE_ITS_TAG.format(tag=tag))
        for path in sorted((self.game_root / "in_game/events").rglob("*.txt")):
            found = pattern.search(path.read_text(encoding="utf-8-sig"))
            if found and self.text(found.group(1)):
                return self.text(found.group(1))
        return self.game.name(tag)

    def named(self, key: str) -> dict:
        return {"key": key, "name": self.game.name(key), "text": self.text(f"{key}_desc")}

    # ---- the game rule --------------------------------------------------

    def rule(self) -> dict:
        text = (self.mod_root / "main_menu/common/game_rules/99_nd_game_rules.txt").read_text(encoding="utf-8-sig")
        for s in parse(text):
            if s[0] == "block" and s[1] == "nd_bank_rule":
                default = atoms(s[3]).get("default")
                settings = [
                    {
                        "name": self.game.name(f"setting_{c[1]}"),
                        "text": self.text(f"setting_{c[1]}_desc"),
                        "default": c[1] == default,
                    }
                    for c in s[3] if c[0] == "block"
                ]
                return {"name": self.game.name("rule_nd_bank_rule"), "settings": settings}
        raise SystemExit("the mod has no game rule nd_bank_rule")

    # ---- the banks of the start date ------------------------------------

    def starting_banks(self) -> list[dict]:
        setup = (self.game_root / "main_menu/setup/1337/10_countries.txt").read_text(encoding="utf-8-sig")
        banks = []
        for match in re.finditer(r"^\t([A-Z][A-Z0-9]{2})\s*=\s*\{(.*?)^\t\}", setup, re.S | re.M):
            tag, body = match.groups()
            if not re.search(rf"reforms\s*=\s*\{{[^}}]*\b{BANK_REFORM}\b", body):
                continue
            capital = re.search(r"\bcapital\s*=\s*(\w+)", body)
            banks.append({
                "tag": tag,
                "name": self.country_name(tag),
                "home": self.game.name(capital.group(1)) if capital else None,
            })
        return banks

    # ---- laws, privileges, the bank's value ------------------------------

    def policies(self, law_body: list) -> list[dict]:
        out = []
        for s in law_body:
            if s[0] != "block" or s[1] in ("potential", "allow", "custom_tags", "locked"):
                continue
            effects = []
            for modifier_block in MODIFIER_BLOCKS_OF_A_POLICY:
                effects.extend(self.game.effects(block(s[3], modifier_block) or []))
            out.append({**self.named(s[1]), "effects": effects})
        return out

    def laws(self, relative: str) -> list[dict]:
        return [{**self.named(key), "policies": self.policies(body)} for key, body in self.blocks(relative)]

    def privileges(self) -> list[dict]:
        return [
            {**self.named(key), "effects": self.game.effects(block(body, "country_modifier") or [])}
            for key, body in self.blocks("estate_privileges/99_nd_bank.txt")
        ]

    def value(self) -> dict | None:
        for key, body in self.blocks("societal_values/99_nd_bank.txt"):
            left, right = key.split("_vs_")
            return {
                "text": self.text(f"{key}_desc"),
                "sides": [
                    {"name": self.game.name(f"{left}_focus"),
                     "effects": self.game.effects(block(body, "left_modifier") or [])},
                    {"name": self.game.name(f"{right}_focus"),
                     "effects": self.game.effects(block(body, "right_modifier") or [])},
                ],
            }
        return None

    # ---- actions ----------------------------------------------------------

    def actions_in(self, relative: str) -> list[dict]:
        return [self.named(key) for key, _ in self.blocks(relative)]

    def action_groups(self) -> list[dict]:
        grouped: dict[str, list[dict]] = {title: [] for title in ACTION_GROUP_ORDER}
        for folder in ("country_interactions", "generic_actions"):
            for path in sorted((self.mod_root / COMMON / folder).glob("99_nd_bank*.txt")):
                relative = f"{folder}/{path.name}"
                if relative in ACTION_FILES_SHOWN_ELSEWHERE:
                    continue
                if relative not in ACTION_GROUPS:
                    self.unplaced_action_files.append(relative)
                grouped[ACTION_GROUPS.get(relative, "Other")].extend(self.actions_in(relative))
        return [{"title": title, "actions": grouped[title]} for title in ACTION_GROUP_ORDER if grouped[title]]

    # ---- standing ---------------------------------------------------------

    def standing(self) -> dict:
        steps = []
        for name_key, threshold in STANDING_STEPS:
            value = self.game.number(threshold) if threshold else 0
            if value is None:
                self.game.report.unresolved_values[threshold] += 1
                value = 0
            steps.append({"name": self.game.name(name_key), "from": int(value)})
        full = self.game.number("nd_bank_st_max")
        concepts = [
            {"name": self.game.name(f"game_concept_{c}"), "text": self.text(f"game_concept_{c}_desc")}
            for c in STANDING_CONCEPTS
        ]
        return {"steps": steps, "max": int(full) if full else 100, "concepts": concepts}

    # ---- the run on the bank ---------------------------------------------

    def run(self) -> dict | None:
        for key, body in self.blocks("disasters/99_nd_bank_run.txt"):
            return {
                **self.named(key),
                "starts": self.game.conditions(shown_conditions(block(body, "can_start") or [])),
                "ends": self.game.conditions(shown_conditions(block(body, "can_end") or [])),
                "actions": self.actions_in("generic_actions/99_nd_bank_run.txt"),
            }
        return None

    # ---- organisations ----------------------------------------------------

    def organisation(self, spec: dict) -> dict:
        out = {
            **self.named(spec["key"]),
            "statuses": [self.named(key) for key, _ in self.blocks(spec["statuses"])],
            "laws": self.laws(spec["laws"]),
        }
        if "payments" in spec:
            out["payments"] = [self.named(key) for key, _ in self.blocks(spec["payments"])]
        if "subjects" in spec:
            out["subjects"] = [self.named(key) for key, _ in self.blocks(spec["subjects"])]
        if "actions" in spec:
            out["actions"] = self.actions_in(spec["actions"])
        return out

    # ---- countries a bank can become --------------------------------------

    def requirement_lines(self, prefix: str) -> list[str]:
        trigger_name = f"{prefix}_requirements_met"
        for path in sorted((self.mod_root / COMMON / "scripted_triggers").glob("nd_*.txt")):
            for s in parse(path.read_text(encoding="utf-8-sig")):
                if s[0] == "block" and s[1] == trigger_name:
                    return [
                        line for inner in walk(s[3])
                        if inner[0] == "atom" and inner[1] == "text" and (line := self.text(inner[3]))
                    ]
        self.game.report.unnamed[trigger_name] += 1
        return []

    def bank_named_in(self, action_body: list) -> str | None:
        for s in walk(block(action_body, "potential") or []):
            if s[0] == "atom" and s[1] == "has_or_had_tag":
                return self.country_name(s[3])
        return None

    def countries(self) -> list[dict]:
        out = []
        for road in COUNTRY_ROADS:
            body = dict(self.blocks(road["file"])).get(road["action"])
            if body is None:
                self.game.report.unnamed[road["action"]] += 1
                continue
            formable = self.formables.get(road.get("formable", ""))
            if formable:
                country = self.game.name(road["formable"])
            else:
                effects = (self.mod_root / COMMON / road["effects"]).read_text(encoding="utf-8-sig")
                given = NAME_GIVEN_TO_A_SUBJECT.search(effects)
                country = self.country_name(given.group(1)) if given else self.game.name(road["action"])
            out.append({
                "country": country,
                "bank": self.bank_named_in(body),
                "action": self.game.name(road["action"]),
                "text": self.text(f"{road['action']}_desc"),
                "result": self.text(f"{road['action']}_tt"),
                "requirements": self.requirement_lines(road["prefix"]),
                "atlas": road["formable"] if formable else None,
            })
        return out

    # ---- everything -------------------------------------------------------

    def build(self) -> dict:
        as_country = ContentBuilder(self.game, Country(BANK_FILES_KEY, self.mod_root), [])
        return {
            "rule": self.rule(),
            "banks": self.starting_banks(),
            "laws": self.laws("laws/99_nd_bank.txt"),
            "privileges": self.privileges(),
            "value": self.value(),
            "ages": as_country.ages(),
            "buildings": as_country.building_cards(),
            "action_groups": self.action_groups(),
            "standing": self.standing(),
            "run": self.run(),
            "organisations": [self.organisation(spec) for spec in ORGANISATIONS],
            "countries": self.countries(),
        }


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
    icons_dir = repo_root / config["build"]["dist_dir"] / "icons"

    report = Report()
    game = Game(game_root, mod_root, report)
    formables = json.loads((web_data_dir / "formables.json").read_text())["formables"]
    banks = Banks(game, mod_root, game_root, formables)
    data = banks.build()
    (web_data_dir / "banks.json").write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")))

    new_icons = game.write_icons(icons_dir, repo_root / ICONS_IN_USE_DIR, "banks")
    print(
        f"banks: {len(data['banks'])} at the start, {len(data['laws'])} laws, "
        f"{sum(len(g['actions']) for g in data['action_groups'])} actions in {len(data['action_groups'])} groups, "
        f"{len(data['organisations'])} organisations, {len(data['countries'])} countries, {new_icons} icons converted"
    )
    if banks.unplaced_action_files:
        print("action files with no group on the Banks page (shown under Other): "
              + ", ".join(banks.unplaced_action_files))
    if args.report:
        report.print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
