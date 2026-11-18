// The Content tab of a formable's panel: everything the mod gives the
// country, drawn from data/content/<key>.json (scripts/build/extract_content.py).

const cache = new Map();

function esc(s) {
  return String(s == null ? "" : s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

function icon(ref, cls) {
  return ref
    ? `<img class="${cls}" src="icons/${esc(ref)}.webp" alt="" loading="lazy">`
    : `<span class="${cls} ct-noicon"></span>`;
}

function effectRows(effects) {
  if (!effects || effects.length === 0) return "";
  const anyIcon = effects.some((e) => e.icon);
  const rows = effects.map((e) => {
    const tone = e.good === true ? "good" : e.good === false ? "bad" : "plain";
    return `<li class="fx fx-${tone}">${anyIcon ? icon(e.icon, "fx-icon") : ""}` +
      `<span class="fx-name">${esc(e.name)}</span>` +
      `<span class="fx-value">${esc(e.value || "")}</span></li>`;
  });
  return `<ul class="fx-list">${rows.join("")}</ul>`;
}

function conditionList(clauses) {
  if (!clauses || clauses.length === 0) return "";
  const item = (c) => {
    const kids = c.children && c.children.length > 0;
    return `<li class="${kids ? `req-group req-${esc(c.kind)}` : ""}">${esc(c.text)}` +
      (kids ? `<ul class="req-list">${c.children.map(item).join("")}</ul>` : "") + "</li>";
  };
  return `<ul class="req-list">${clauses.map(item).join("")}</ul>`;
}

function factLine(facts) {
  return `<div class="facts">${facts.filter(Boolean).map(esc).join('<span class="dot">&middot;</span>')}</div>`;
}

function description(text) {
  return text ? `<p class="ct-desc" title="Show all">${esc(text)}</p>` : "";
}

const UNLOCK_LABELS = {
  building: "Building",
  unit: "Unit",
  levy: "Levy",
  production_method: "Production method",
  policy: "Policy",
  reform: "Reform",
  cabinet_action: "Cabinet action",
  subject_type: "Subject type",
  town_rights: "Town rights",
};
const UNLOCKS_WITH_A_CARD = new Set(["building", "unit", "levy", "production_method"]);

function unlockChips(unlocks) {
  if (!unlocks || unlocks.length === 0) return "";
  const chips = unlocks.map((u) => {
    const label = `<span class="unlock-kind">${UNLOCK_LABELS[u.kind] || "Unlocks"}</span>` +
      esc(u.name) + (u.of ? ` <span class="unlock-of">in ${esc(u.of)}</span>` : "");
    return UNLOCKS_WITH_A_CARD.has(u.kind)
      ? `<button type="button" class="unlock" data-goto="${esc(u.key)}">${label}</button>`
      : `<span class="unlock">${label}</span>`;
  });
  return `<div class="unlocks">${chips.join("")}</div>`;
}

function timedModifier(m) {
  return `<div class="timed">` +
    `<div class="timed-head"><span class="timed-name">${esc(m.name)}</span>` +
    (m.duration ? `<span class="timed-duration">${esc(m.duration)}</span>` : "") + "</div>" +
    effectRows(m.effects) + "</div>";
}

function eventOptions(options) {
  return `<div class="choices">${options.map((o) =>
    `<div class="choice"><div class="choice-text">${esc(o.text)}</div>` +
    o.modifiers.map(timedModifier).join("") + "</div>").join("")}</div>`;
}

function eventFold(event) {
  if (!event) return "";
  return `<details class="ct-event"><summary><span class="unlock-kind">Event</span>${esc(event.title)}</summary>` +
    description(event.text) + eventOptions(event.options) + "</details>";
}

function advanceCard(a, extra = "") {
  return `<article class="card adv" id="ct-${esc(a.key)}">` +
    `<div class="medal">${icon(a.icon, "medal-icon")}</div>` +
    `<div class="card-body"><h4>${esc(a.name)}</h4>` +
    extra + effectRows(a.effects) + unlockChips(a.unlocks) +
    description(a.text) + eventFold(a.event) + "</div></article>";
}

function section(id, title, count, body, note = "") {
  return `<section class="ct-section" id="ct-sec-${id}">` +
    `<h3 class="ct-h"${note ? ` title="${esc(note)}"` : ""}>${esc(title)}` +
    (count === "" ? "" : ` <span class="req-count">${count}</span>`) + "</h3>" +
    body + "</section>";
}

function formationSection(f) {
  if (!f || f.options.length === 0) return "";
  return section("choices", "Formation event", f.options.length,
    `<div class="formation"><h4 class="formation-title">${esc(f.title)}</h4>` +
    description(f.text) + eventOptions(f.options) + "</div>");
}

function advancesSection(ages, total) {
  if (total === 0) return "";
  const body = ages.map((age) =>
    `<div class="age"><div class="age-head">${icon(age.icon, "age-icon")}` +
    `<span class="age-name">Age of ${esc(age.name)}</span>` +
    `<span class="req-count">${age.advances.length}</span></div>` +
    `<div class="card-grid">${age.advances.map((a) => advanceCard(a)).join("")}</div></div>`
  ).join("");
  return section("advances", "Advances", total, body);
}

function destinySection(stages) {
  if (stages.length === 0) return "";
  const children = new Map();
  for (const s of stages) {
    const parent = s.requires || "";
    if (!children.has(parent)) children.set(parent, []);
    children.get(parent).push(s);
  }
  const stageCard = (s) => {
    const needs = s.conditions && s.conditions.length > 0
      ? `<div class="needs"><div class="group-label">Requirements</div>${conditionList(s.conditions)}</div>` : "";
    return advanceCard(s, needs);
  };
  // A stage with one follower continues the same column. Only a fork indents.
  const branch = (parent) => {
    const followers = children.get(parent) || [];
    if (followers.length === 1) {
      return `<li class="stage">${stageCard(followers[0])}</li>` + branch(followers[0].key);
    }
    return followers.map((s) =>
      `<li class="stage fork"><ol class="stages"><li class="stage">${stageCard(s)}</li>${branch(s.key)}</ol></li>`
    ).join("");
  };
  return section("destiny", "Destiny tree", stages.length,
    `<ol class="stages stages-root">${branch("")}</ol>`,
    "Missions for after forming. Each stage requires the one above it.");
}

function unitsSection(units) {
  if (units.length === 0) return "";
  const cards = units.map((u) => {
    const facts = [u.category];
    if (u.levy) {
      const from = u.levy.pops.length > 0 ? ` from ${u.levy.pops.join(", ")}` : "";
      const of = u.levy.cultures.length > 0 ? ` of ${u.levy.cultures.join(", ")} culture` : "";
      facts.push(`Levy${from}${of}`);
    }
    if (u.unlocked_by) facts.push(`Unlocked by ${u.unlocked_by}`);
    if (u.upgrades_to) facts.push(`Upgrades to ${u.upgrades_to}`);
    return `<article class="card" id="ct-${esc(u.key)}">` +
      `<div class="square">${icon(u.icon, "square-icon")}</div>` +
      `<div class="card-body"><h4>${esc(u.name)}</h4>` +
      factLine(facts) +
      effectRows(u.stats) + description(u.text) + "</div></article>";
  });
  return section("units", "Units", units.length, `<div class="card-grid">${cards.join("")}</div>`,
    "Each number is the difference from the standard unit of the same type and age.");
}

function goods(g) {
  return `<span class="goods">${icon(g.icon, "goods-icon")}${g.amount ? esc(g.amount) + " " : ""}${esc(g.name)}</span>`;
}

function methodRow(m) {
  const flow = m.inputs.map(goods).join('<span class="plus">+</span>') +
    (m.output ? `<span class="arrow">&rarr;</span>${goods(m.output)}` : "");
  return `<div class="method"><div class="method-name">${esc(m.name)}` +
    (m.unlocked_by ? ` <span class="unlock-of">requires ${esc(m.unlocked_by)}</span>` : "") +
    `</div><div class="method-flow">${flow}</div>${effectRows(m.effects)}</div>`;
}

function buildingsSection(buildings) {
  if (buildings.length === 0) return "";
  const cards = buildings.map((b) => {
    const facts = [b.category, b.workers];
    if (b.settlements.length > 0) facts.push(b.settlements.join(", "));
    if (b.max_levels) facts.push(b.max_levels === "1" ? "1 level" : `${b.max_levels} levels`);
    if (b.unlocked_by) facts.push(`Unlocked by ${b.unlocked_by}`);
    const groups = b.effect_groups.map((g) =>
      `<div class="group-label">${esc(g.label)}</div>${effectRows(g.effects)}`).join("");
    const where = b.where && b.where.length > 0
      ? `<details class="ct-event"><summary>Where it can be built</summary>${conditionList(b.where)}</details>` : "";
    return `<article class="card" id="ct-${esc(b.key)}">` +
      `<div class="square">${icon(b.icon, "square-icon")}</div>` +
      `<div class="card-body"><h4>${esc(b.name)}</h4>` +
      factLine(facts) +
      groups + b.methods.map(methodRow).join("") + where + description(b.text) + "</div></article>";
  });
  return section("buildings", "Buildings", buildings.length, `<div class="card-grid">${cards.join("")}</div>`);
}

function estates(label, list, tone) {
  if (list.length === 0) return "";
  return `<span class="estates estates-${tone}">${label} ` +
    list.map((e) => `${icon(e.icon, "estate-icon")}${esc(e.name)}`).join(", ") + "</span>";
}

function bureaucraciesSection(b) {
  if (!b || b.list.length === 0) return "";
  const group = (label, effects) =>
    effects.length > 0 ? `<div class="group-label">${label}</div>${effectRows(effects)}` : "";
  const cards = b.list.map((c) =>
    `<article class="card" id="ct-${esc(c.key)}">` +
    `<div class="square">${icon(c.icon, "square-icon")}</div>` +
    `<div class="card-body"><h4>${esc(c.name)}</h4>` +
    `<div class="facts estate-line">${estates("Liked by", c.likes, "like")}${estates("Disliked by", c.dislikes, "dislike")}</div>` +
    group("Always", c.always) + group("Fully funded", c.funded) + group("Unfunded", c.neglected) +
    (c.conditions && c.conditions.length > 0
      ? `<div class="needs"><div class="group-label">Requirements</div>${conditionList(c.conditions)}</div>` : "") +
    description(c.text) + "</div></article>");
  const note = (b.slots ? `${b.slots} of ${b.list.length} can be active at once when the country forms. ` : "") +
    "Effects scale with funding.";
  return section("bureaucracies", "Bureaucracies", b.list.length,
    `<div class="card-grid">${cards.join("")}</div>`, note);
}

const NAV = [
  ["choices", "Formation choices"],
  ["advances", "Advances"],
  ["destiny", "Destiny stages"],
  ["units", "Units"],
  ["buildings", "Buildings"],
  ["bureaucracies", "Bureaucracies"],
];

function nav(counts) {
  const tiles = NAV.filter(([id]) => counts[id] > 0).map(([id, label]) =>
    `<button type="button" class="ct-tile" data-section="${id}">` +
    `<b>${counts[id]}</b><span>${label}</span></button>`);
  return `<nav class="ct-nav">${tiles.join("")}</nav>`;
}

function render(content) {
  return nav(content.counts) +
    formationSection(content.formation) +
    advancesSection(content.ages, content.counts.advances) +
    destinySection(content.destiny) +
    unitsSection(content.units) +
    buildingsSection(content.buildings) +
    bureaucraciesSection(content.bureaucracies);
}

function bind(scope, scroller) {
  const reveal = (el) => {
    if (!el) return;
    scroller.scrollTo({ top: el.offsetTop - scroller.offsetTop - 52, behavior: "smooth" });
    el.classList.add("flash");
    setTimeout(() => el.classList.remove("flash"), 1200);
  };
  scope.addEventListener("click", (ev) => {
    const tile = ev.target.closest("[data-section]");
    if (tile) return reveal(scope.querySelector(`#ct-sec-${tile.dataset.section}`));
    const jump = ev.target.closest("[data-goto]");
    if (jump) return reveal(scope.querySelector(`#ct-${CSS.escape(jump.dataset.goto)}`));
    const text = ev.target.closest(".ct-desc");
    if (text) text.classList.toggle("open");
  });
}

// The Banks page draws the same cards on a page of its own.
export {
  esc, effectRows, conditionList, description, section, advancesSection, buildingsSection, bind,
};

export function hasContent(rec) {
  return Boolean(rec.content && rec.content.key);
}

export function contentTabPlaceholder() {
  return '<div class="ct" data-content><p class="ct-note">Loading.</p></div>';
}

export async function fillContentTab(scope, rec, scroller) {
  const key = rec.content.key;
  const target = scope.querySelector("[data-content]");
  if (!cache.has(key)) {
    cache.set(key, fetch(`data/content/${key}.json`).then((r) => {
      if (!r.ok) throw new Error(`content ${key}: ${r.status}`);
      return r.json();
    }));
  }
  let content;
  try {
    content = await cache.get(key);
  } catch (err) {
    cache.delete(key);
    if (target.isConnected) target.innerHTML = '<p class="ct-note">The content list did not load. Open the tab again to retry.</p>';
    return;
  }
  // The tab may have been left, or opened a second time, while the file loaded.
  if (!target.isConnected || target.dataset.filled) return;
  target.dataset.filled = "yes";
  target.innerHTML = render(content);
  bind(target, scroller);
}
