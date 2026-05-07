// National Destinies, Formables Atlas
//
// Loads the static data layers built by scripts/build/*.py, renders a
// filterable formables list in the sidebar, and on selection drops pins
// for the formable's must-own locations on the map plus a detail panel.

const NATIVE_W = 16384;
const NATIVE_H = 8192;
const PADDED = 16384;
const MAX_ZOOM = 6;
const TILE_SIZE = 256;

// ---- map ----------------------------------------------------------------

const customCRS = L.extend({}, L.CRS.Simple, {
  scale: (z) => Math.pow(2, z - MAX_ZOOM),
  zoom: (s) => Math.log(s) / Math.LN2 + MAX_ZOOM,
});

const map = L.map("map", {
  crs: customCRS,
  minZoom: 0,
  maxZoom: MAX_ZOOM,
  zoomControl: true,
  attributionControl: false,
  zoomSnap: 0.25,
  preferCanvas: true,
});

const visibleBounds = [[-NATIVE_H, 0], [0, NATIVE_W]];

L.tileLayer("tiles/{z}/{x}/{y}.png", {
  tileSize: TILE_SIZE,
  minZoom: 0,
  maxZoom: MAX_ZOOM,
  noWrap: true,
  // Constrain to visible area so Leaflet does not request padding tiles
  // that we never generate.
  bounds: visibleBounds,
}).addTo(map);
map.setMaxBounds(visibleBounds);
map.fitBounds(visibleBounds);

// Layer that holds pins for the currently-selected formable.
const pinLayer = L.layerGroup().addTo(map);

// pixel coords (x, y) -> Leaflet latlng (we use -y for lat).
function px(x, y) {
  return L.latLng(-y, x);
}

// ---- data load ----------------------------------------------------------

const $list = document.getElementById("formables-list");
const $search = document.getElementById("search");
const $sourceFilter = document.getElementById("source-filter");
const $detail = document.getElementById("detail");
const $detailName = document.getElementById("detail-name");
const $detailBody = document.getElementById("detail-body");
const $detailClose = document.getElementById("detail-close");

let formables = [];
let geography = null;
let locIndex = null;
let loc = {};
let selected = null;

async function loadAll() {
  const [f, g, l, lo] = await Promise.all([
    fetch("data/formables.json").then((r) => r.json()),
    fetch("data/geography.json").then((r) => r.json()),
    fetch("data/locations_index.json").then((r) => r.json()),
    fetch("data/loc.json").then((r) => r.json()),
  ]);
  formables = f.formables;
  geography = g;
  locIndex = l.locations;
  loc = lo.strings;

  formables.forEach((rec) => {
    rec._displayName = displayName(rec);
    rec._description = description(rec);
    rec._adjective = lookupLoc(rec.adjective);
    rec._haystack = (
      (rec._displayName || "") + " " + (rec.tag || "") + " " + rec.block_key
    ).toLowerCase();
  });
  formables.sort((a, b) => a._displayName.localeCompare(b._displayName));
  renderList();
}

// EU5 loc values can redirect with $KEY$ and embed scripted helpers like
// [ShowAreaName('foo_area')]. Resolve both so display strings are clean.
const REF_RE = /\$([A-Za-z_][A-Za-z0-9_]*)\$/g;
const SHOW_RE = /\[Show(?:Area|Region|Subregion|Continent|Province|Country|Estate(?:Type)?)?Name(?:WithNoTooltip)?\(\s*'([^']+)'\s*\)\]/g;

function resolveLoc(value, depth = 0) {
  if (!value || depth > 5) return value || "";
  // $REF$ placeholders
  let out = value.replace(REF_RE, (whole, key) => {
    const v = loc[key];
    return v ? resolveLoc(v, depth + 1) : whole;
  });
  // Scripted name helpers
  out = out.replace(SHOW_RE, (whole, key) => {
    const v = loc[key];
    return v ? resolveLoc(v, depth + 1) : prettifyName(key);
  });
  return out;
}

function lookupLoc(key) {
  if (!key) return null;
  const v = loc[key];
  if (v == null) return null;
  return resolveLoc(v);
}

function displayName(rec) {
  // Prefer the formable's loc'd full name, falling back to tag-based variants.
  // Order: tag (most reliably localized like "Sweden"), then derived keys.
  const candidates = [
    rec.tag,                              // SWE -> "Sweden"
    rec.name,                              // explicit name field
    rec.block_key,                         // sweden_f
    rec.tag && rec.tag + "_f",             // BOH_f redirects to $BOH$
  ].filter(Boolean);
  for (const k of candidates) {
    const v = lookupLoc(k);
    if (v) return v;
  }
  return rec.block_key.replace(/_f$/, "").replace(/_/g, " ");
}

function description(rec) {
  const candidates = [
    rec.block_key + "_desc",
    rec.tag && rec.tag + "_f_desc",
    rec.name && rec.name + "_f_desc",
  ].filter(Boolean);
  for (const k of candidates) {
    const v = lookupLoc(k);
    if (v) return v;
  }
  return null;
}

// ---- list rendering -----------------------------------------------------

function renderList() {
  const term = $search.value.trim().toLowerCase();
  const sourceFilter = $sourceFilter.value;
  const filtered = formables.filter((f) => {
    if (term && !f._haystack.includes(term)) return false;
    if (sourceFilter === "mod" && !f.mod_overrides) return false;
    if (sourceFilter === "vanilla" && f.source !== "vanilla") return false;
    return true;
  });
  $list.replaceChildren();
  for (const rec of filtered) {
    $list.appendChild(makeRow(rec));
  }
  if (filtered.length === 0) {
    const empty = document.createElement("div");
    empty.style.padding = "16px";
    empty.style.color = "var(--fg-2)";
    empty.style.fontSize = "12px";
    empty.textContent = "No matches.";
    $list.appendChild(empty);
  }
}

function makeRow(rec) {
  const row = document.createElement("div");
  row.className = "formable-row";
  if (selected && selected.block_key === rec.block_key) {
    row.classList.add("selected");
  }
  row.dataset.key = rec.block_key;

  const left = document.createElement("div");
  left.className = "name";
  left.textContent = rec._displayName;
  if (rec.tag && rec.tag !== rec._displayName) {
    const tagSpan = document.createElement("span");
    tagSpan.className = "tag";
    tagSpan.textContent = " " + rec.tag;
    left.appendChild(tagSpan);
  }
  row.appendChild(left);

  const badges = document.createElement("div");
  badges.className = "badges";
  if (rec.level != null) {
    const b = document.createElement("span");
    b.className = "badge lvl";
    b.textContent = "L" + rec.level;
    badges.appendChild(b);
  }
  if (rec.source === "mod_new") {
    const b = document.createElement("span");
    b.className = "badge new";
    b.textContent = "new";
    badges.appendChild(b);
  } else if (rec.mod_overrides) {
    const b = document.createElement("span");
    b.className = "badge mod";
    b.textContent = "mod";
    badges.appendChild(b);
  }
  row.appendChild(badges);

  row.addEventListener("click", () => selectFormable(rec));
  return row;
}

// ---- selection / detail panel ------------------------------------------

function selectFormable(rec) {
  selected = rec;
  // update list selection highlight
  $list.querySelectorAll(".formable-row").forEach((r) => {
    r.classList.toggle("selected", r.dataset.key === rec.block_key);
  });
  showPins(rec);
  showDetail(rec);
  const tb = territoryBounds(rec);
  if (tb) {
    map.fitBounds(tb.pad(0.15), { maxZoom: 5, animate: true });
  }
}

function showPins(rec) {
  pinLayer.clearLayers();
  for (const locName of rec.must_own) {
    const info = locIndex[locName];
    if (!info) {
      console.warn("must_own location not in index:", locName);
      continue;
    }
    const [cx, cy] = info.centroid;
    const labelText = lookupLoc(locName) || prettifyName(locName);
    const marker = L.marker(px(cx, cy), {
      icon: L.divIcon({
        className: "must-own-marker",
        html: `<div class="must-own-pin"></div><div class="must-own-label">${escapeHtml(labelText)}</div>`,
        iconSize: [14, 14],
        iconAnchor: [7, 7],
      }),
      keyboard: false,
    });
    marker.addTo(pinLayer);
  }
}

function showDetail(rec) {
  $detail.hidden = false;
  $detailName.textContent = rec._displayName;
  const body = [];

  if (rec._description) {
    body.push(`<p style="margin:0 0 12px;color:var(--fg-1);font-size:12px;line-height:1.5;">${escapeHtml(rec._description)}</p>`);
  }

  // top-line stats
  body.push('<div class="stat-grid">');
  if (rec.level != null) body.push(`<dt>Level</dt><dd>${rec.level}</dd>`);
  if (rec.fraction != null) body.push(`<dt>Required</dt><dd>${Math.round(rec.fraction * 100)}% of territory</dd>`);
  if (rec.rule) body.push(`<dt>Rule</dt><dd>${escapeHtml(rec.rule)}</dd>`);
  if (rec.tag) body.push(`<dt>Tag</dt><dd><code>${escapeHtml(rec.tag)}</code></dd>`);
  if (rec._adjective) body.push(`<dt>Adjective</dt><dd>${escapeHtml(rec._adjective)}</dd>`);
  body.push(`<dt>Source</dt><dd>${formatSource(rec)}</dd>`);
  if (rec.formation_event) body.push(`<dt>Formation event</dt><dd><code>${escapeHtml(rec.formation_event)}</code></dd>`);
  body.push("</div>");

  if (rec.must_own && rec.must_own.length > 0) {
    body.push("<h3>Must Own</h3>");
    body.push('<div class="req-badges">');
    for (const locName of rec.must_own) {
      const info = locIndex[locName];
      const label = lookupLoc(locName) || prettifyName(locName);
      const note = info ? "" : " (unknown location)";
      body.push(`<span class="req-badge required">${escapeHtml(label)}${note}</span>`);
    }
    body.push("</div>");
  }

  if (rec.regions && rec.regions.length > 0) {
    body.push("<h3>Regions in territory pool</h3>");
    body.push("<ul>");
    for (const r of rec.regions) body.push(`<li>${escapeHtml(lookupLoc(r) || prettifyName(r))}</li>`);
    body.push("</ul>");
  }
  if (rec.areas && rec.areas.length > 0) {
    body.push("<h3>Areas in territory pool</h3>");
    body.push("<ul>");
    for (const a of rec.areas) body.push(`<li>${escapeHtml(lookupLoc(a) || prettifyName(a))}</li>`);
    body.push("</ul>");
  }

  if (rec.potential_raw) {
    body.push("<h3>Potential (raw)</h3>");
    body.push(`<pre style="white-space:pre-wrap;font-size:11px;background:var(--bg-2);padding:8px;border-radius:3px;">${escapeHtml(rec.potential_raw)}</pre>`);
  }
  if (rec.allow_raw) {
    body.push("<h3>Allow (raw)</h3>");
    body.push(`<pre style="white-space:pre-wrap;font-size:11px;background:var(--bg-2);padding:8px;border-radius:3px;">${escapeHtml(rec.allow_raw)}</pre>`);
  }

  $detailBody.innerHTML = body.join("");
}

function formatSource(rec) {
  switch (rec.source) {
    case "vanilla": return "Vanilla (untouched)";
    case "vanilla+mod_inject": return "Vanilla + mod additions";
    case "vanilla+mod_replace": return "Mod replaces vanilla";
    case "mod_new": return "New formable (mod-added)";
    default: return rec.source;
  }
}

function prettifyName(s) {
  return escapeHtml(
    s.replace(/_(area|region|subregion|continent|province)$/, "")
     .replace(/_/g, " ")
     .replace(/\b\w/g, (c) => c.toUpperCase())
  );
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  }[c]));
}

function clearSelection() {
  selected = null;
  pinLayer.clearLayers();
  $detail.hidden = true;
  $list.querySelectorAll(".formable-row.selected").forEach((r) => r.classList.remove("selected"));
}

$detailClose.addEventListener("click", clearSelection);
$search.addEventListener("input", renderList);
$sourceFilter.addEventListener("change", renderList);

loadAll().catch((err) => {
  console.error("data load failed:", err);
  $list.innerHTML = `<div style="padding:16px;color:#ff8080;">Failed to load data: ${escapeHtml(err.message)}</div>`;
});
