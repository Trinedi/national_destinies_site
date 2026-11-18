// The Banks page: what the mod's bank system holds, drawn from
// data/banks.json (scripts/build/extract_banks.py) with the Content tab's cards.

import {
  esc, effectRows, conditionList, description, section, advancesSection, buildingsSection, bind,
} from "./content.js";

const ATLAS = "index.html";

function plainCard(item, extra = "") {
  return `<article class="card"><div class="card-body"><h4>${esc(item.name)}</h4>` +
    extra + effectRows(item.effects) + description(item.text) + "</div></article>";
}

function cardGrid(items, extra) {
  return `<div class="card-grid">${items.map((i) => plainCard(i, extra ? extra(i) : "")).join("")}</div>`;
}

function lines(list) {
  return `<ul class="req-list">${list.map((l) => `<li>${esc(l)}</li>`).join("")}</ul>`;
}

function group(label, body) {
  return body ? `<div class="group-label">${esc(label)}</div>${body}` : "";
}

function ruleSection(rule) {
  const settings = rule.settings.map((s) =>
    `<div class="choice"><div class="choice-text">${esc(s.name)}` +
    (s.default ? ' <span class="bk-chip">Default</span>' : "") + "</div>" +
    `<p class="bk-text">${esc(s.text)}</p></div>`).join("");
  return section("rule", "Game rule", rule.settings.length,
    `<div class="formation"><h4 class="formation-title">${esc(rule.name)}</h4>` +
    `<div class="choices">${settings}</div></div>`);
}

function banksSection(banks) {
  const chips = banks.map((b) =>
    `<span class="bk-bank"><b>${esc(b.name)}</b>${b.home ? ` ${esc(b.home)}` : ""}</span>`).join("");
  return section("banks", "Banks in 1337", banks.length, `<div class="bk-banks">${chips}</div>`);
}

function lawBlock(law) {
  const policies = law.policies.map((p) =>
    `<div class="choice"><div class="choice-text">${esc(p.name)}</div>` +
    effectRows(p.effects) + (p.text ? `<p class="bk-text">${esc(p.text)}</p>` : "") + "</div>").join("");
  return `<div class="formation bk-law"><h4 class="formation-title">${esc(law.name)}</h4>` +
    (law.text ? `<p class="bk-text">${esc(law.text)}</p>` : "") +
    `<div class="choices">${policies}</div></div>`;
}

function lawsSection(id, title, laws) {
  return laws.length === 0 ? "" : section(id, title, laws.length, laws.map(lawBlock).join(""));
}

function valueSection(value) {
  if (!value) return "";
  const sides = value.sides.map((s) =>
    `<div class="choice"><div class="choice-text">${esc(s.name)}</div>${effectRows(s.effects)}</div>`).join("");
  return section("value", `${value.sides[0].name} and ${value.sides[1].name}`, value.sides.length,
    `<div class="formation">${value.text ? `<p class="bk-text">${esc(value.text)}</p>` : ""}` +
    `<div class="choices">${sides}</div></div>`);
}

function actionsSection(groups) {
  const total = groups.reduce((n, g) => n + g.actions.length, 0);
  const body = groups.map((g) =>
    `<div class="age"><div class="age-head"><span class="age-name">${esc(g.title)}</span>` +
    `<span class="req-count">${g.actions.length}</span></div>${cardGrid(g.actions)}</div>`).join("");
  return section("actions", "Actions", total, body);
}

function standingSection(standing) {
  const steps = standing.steps.map((s, i) => {
    const until = i + 1 < standing.steps.length ? standing.steps[i + 1].from : standing.max;
    return `<div class="bk-step" style="flex-grow:${until - s.from}">` +
      `<span class="bk-step-from">${s.from}</span><span class="bk-step-name">${esc(s.name)}</span></div>`;
  }).join("");
  const concepts = standing.concepts.map((c) =>
    `<details class="ct-event"><summary>${esc(c.name)}</summary><p class="bk-text bk-long">${esc(c.text)}</p></details>`).join("");
  return section("standing", "Standing", standing.steps.length,
    `<div class="formation"><div class="bk-bar">${steps}</div>${concepts}</div>`);
}

function runSection(run) {
  if (!run) return "";
  return section("run", run.name, run.actions.length,
    `<div class="formation bk-law"><p class="bk-text">${esc(run.text)}</p>` +
    `<div class="choices"><div class="choice">${group("Starts", conditionList(run.starts))}</div>` +
    `<div class="choice">${group("Ends", conditionList(run.ends))}</div></div></div>` +
    cardGrid(run.actions));
}

function organisationSection(org, index) {
  const part = (label, items) => (items && items.length > 0
    ? `<div class="age"><div class="age-head"><span class="age-name">${label}</span>` +
      `<span class="req-count">${items.length}</span></div>${cardGrid(items)}</div>` : "");
  const laws = org.laws.length > 0
    ? `<div class="age"><div class="age-head"><span class="age-name">Laws</span>` +
      `<span class="req-count">${org.laws.length}</span></div>${org.laws.map(lawBlock).join("")}</div>` : "";
  return section(`org${index}`, org.name, org.laws.length,
    `<p class="bk-text bk-lead">${esc(org.text)}</p>` +
    part("Members", org.statuses) + part("Subjects", org.subjects) +
    part("Payments", org.payments) + part("Actions", org.actions) + laws);
}

function countriesSection(countries) {
  const cards = countries.map((c) =>
    `<article class="card"><div class="card-body"><h4>${esc(c.country)}</h4>` +
    `<div class="facts">${esc(c.bank || "")}<span class="dot">&middot;</span>${esc(c.action)}</div>` +
    group("Requirements", lines(c.requirements)) +
    (c.result ? `<details class="ct-event"><summary>What happens</summary><p class="bk-text bk-long">${esc(c.result)}</p></details>` : "") +
    description(c.text) +
    (c.atlas ? `<a class="bk-atlas" href="${ATLAS}#${encodeURIComponent(c.atlas)}">Open on the Atlas</a>` : "") +
    "</div></article>").join("");
  return section("countries", "Countries a bank can become", countries.length,
    `<div class="card-grid">${cards}</div>`);
}

function render(data) {
  const advances = data.ages.reduce((n, age) => n + age.advances.length, 0);
  const usual = data.rule.settings.find((s) => s.default);
  return `<header class="bk-head"><h2>Banks</h2>` +
    `<p>The banks of the base game get laws, buildings, actions and two organisations of their own. ` +
    `The game rule ${esc(data.rule.name)} sets how much of it is in play.` +
    (usual ? ` Its default is ${esc(usual.name)}.` : "") + `</p></header>` +
    ruleSection(data.rule) +
    banksSection(data.banks) +
    lawsSection("laws", "Laws", data.laws) +
    (data.privileges.length > 0
      ? section("privileges", "Burgher privileges", data.privileges.length, cardGrid(data.privileges)) : "") +
    valueSection(data.value) +
    advancesSection(data.ages, advances) +
    buildingsSection(data.buildings) +
    actionsSection(data.action_groups) +
    standingSection(data.standing) +
    runSection(data.run) +
    data.organisations.map(organisationSection).join("") +
    countriesSection(data.countries);
}

function sectionLinks(page) {
  return [...page.querySelectorAll(".ct-section")].map((s) => {
    const title = s.querySelector(".ct-h").firstChild.textContent.trim();
    return `<a class="formable-row" href="#${s.id}">${esc(title)}</a>`;
  }).join("");
}

async function main() {
  const page = document.getElementById("banks");
  const response = await fetch("data/banks.json");
  if (!response.ok) {
    page.innerHTML = '<p class="ct-note">The page did not load. Reload to retry.</p>';
    return;
  }
  page.innerHTML = render(await response.json());
  document.getElementById("page-sections").innerHTML = sectionLinks(page);
  bind(page, document.getElementById("page-pane"));
  if (location.hash) document.getElementById(location.hash.slice(1))?.scrollIntoView();
}

main();
