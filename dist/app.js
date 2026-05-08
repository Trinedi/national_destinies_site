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

// CRS with x-wrap so panning east past the antimeridian wraps around (EU5
// has wrap_x = yes in default.map). wrapLng tells Leaflet "lng = a is the
// same as lng = b" for the projection.
const customCRS = L.extend({}, L.CRS.Simple, {
  scale: (z) => Math.pow(2, z - MAX_ZOOM),
  zoom: (s) => Math.log(s) / Math.LN2 + MAX_ZOOM,
  wrapLng: [0, NATIVE_W],
});

// minZoom is computed dynamically: it is the smallest zoom at which the map
// width is at least the viewport width, so the user can never zoom out into
// black emptiness.
function computeMinZoom() {
  const mapEl = document.getElementById("map");
  const vw = mapEl.clientWidth || window.innerWidth;
  // At zoom z, world is NATIVE_W * 2^(z-MAX_ZOOM) pixels wide.
  // We want world_px >= vw, so z >= log2(vw / NATIVE_W) + MAX_ZOOM
  const minZ = Math.log2(vw / NATIVE_W) + MAX_ZOOM;
  return Math.max(0, Math.min(MAX_ZOOM, minZ));
}

const map = L.map("map", {
  crs: customCRS,
  minZoom: computeMinZoom(),
  maxZoom: MAX_ZOOM,
  zoomControl: false,
  attributionControl: false,
  zoomSnap: 0.25,
  preferCanvas: true,
  worldCopyJump: false,
  // Firm vertical clamp so the user cannot pan into the black void.
  // Setting this on map.options after construction silently no-ops, so
  // it must live in the constructor.
  maxBoundsViscosity: 1.0,
});
L.control.zoom({ position: "bottomright" }).addTo(map);

const visibleBounds = [[-NATIVE_H, 0], [0, NATIVE_W]];

L.tileLayer("tiles/{z}/{x}/{y}.png", {
  tileSize: TILE_SIZE,
  minZoom: 0,
  maxZoom: MAX_ZOOM,
  noWrap: false,        // allow tile layer to repeat horizontally
  bounds: visibleBounds,
}).addTo(map);
// Constrain vertical pan to map bounds; horizontal wraps freely.
map.setMaxBounds([
  [-NATIVE_H, -Infinity],
  [0, Infinity],
]);
map.fitBounds(visibleBounds);

// Recompute minZoom on viewport resize so the world always fills the screen.
window.addEventListener("resize", () => {
  const z = computeMinZoom();
  map.setMinZoom(z);
  if (map.getZoom() < z) map.setZoom(z);
});

// Vector overlays do not auto-wrap with CRS.Simple, so we manage one set
// of copies per visible world index. As the user pans east or west we add
// copies for newly-visible worlds and drop ones that have left the
// viewport (with a 1-world buffer so it stays seamless during drag).
const areaLayers = new Map();   // worldIndex -> L.GeoJSON
const pinLayers = new Map();    // worldIndex -> L.LayerGroup

// pixel coords (x, y) -> Leaflet latlng (we use -y for lat).
function px(x, y) {
  return L.latLng(-y, x);
}

// Convert GeoJSON's [x, y] (pixel space) into Leaflet's flipped CRS.Simple.
// Leaflet's GeoJSON layer interprets coords as [lng, lat]; we want lat = -y.
// Optional xShift adds an offset for wrap copies.
function flipGeoJson(gj, xShift = 0) {
  function flipCoords(c) {
    if (typeof c[0] === "number") return [c[0] + xShift, -c[1]];
    return c.map(flipCoords);
  }
  const out = {
    type: gj.type,
    features: gj.features.map((f) => ({
      ...f,
      geometry: { ...f.geometry, coordinates: flipCoords(f.geometry.coordinates) },
    })),
  };
  return out;
}

// ---- data load ----------------------------------------------------------

const $list = document.getElementById("formables-list");
const $search = document.getElementById("search");
const $detail = document.getElementById("detail");
const $detailName = document.getElementById("detail-name");
const $detailBody = document.getElementById("detail-body");
const $detailClose = document.getElementById("detail-close");

let formables = [];
let formablesByKey = {};
let geography = null;
let locIndex = null;
let loc = {};
let areasGeoJson = null;
let areaToFormables = {};   // area_name -> [formable rec, ...] primary first
let formableTerritory = {}; // block_key -> Set<area_name>
let selected = null;

let starters = {};

async function loadAll() {
  const [f, g, l, lo, ag, st] = await Promise.all([
    fetch("data/formables.json").then((r) => r.json()),
    fetch("data/geography.json").then((r) => r.json()),
    fetch("data/locations_index.json").then((r) => r.json()),
    fetch("data/loc.json").then((r) => r.json()),
    fetch("data/areas.geojson").then((r) => r.json()),
    fetch("data/starters.json").then((r) => r.json()).catch(() => ({ guides: {} })),
  ]);
  starters = st.guides || {};
  // Hide vanilla-untouched formables: the mod does not enhance them and
  // they would just clutter the list and tint the map without any reward.
  formables = f.formables.filter(
    (r) => r.mod_overrides || r.source === "mod_new"
  );
  geography = g;
  locIndex = l.locations;
  loc = lo.strings;
  areasGeoJson = ag;

  formables.forEach((rec) => {
    rec._displayName = displayName(rec);
    rec._description = description(rec);
    rec._adjective = lookupLoc(rec.adjective);
    rec._color = rec.color_rgb || colorForTag(rec.tag || rec.block_key);
    rec._haystack = (
      (rec._displayName || "") + " " + (rec.tag || "") + " " + rec.block_key
    ).toLowerCase();
    formablesByKey[rec.block_key] = rec;
  });
  formables.sort((a, b) => a._displayName.localeCompare(b._displayName));

  buildTerritoryIndex();
  renderList();
  renderAreaLayer();
}

// ---- formable -> territory areas ---------------------------------------

function expandToAreas(rec) {
  const out = new Set();
  // continent -> all areas under it
  for (const c of rec.continents || []) {
    const cont = geography.continents[c];
    if (!cont) continue;
    for (const sub of cont.subregions) {
      const subInfo = geography.subregions[sub];
      if (!subInfo) continue;
      for (const reg of subInfo.regions) {
        const r = geography.regions[reg];
        if (r) r.areas.forEach((a) => out.add(a));
      }
    }
  }
  // sub_continents in formable files == subregions in our geography tree
  for (const sub of rec.sub_continents || []) {
    const subInfo = geography.subregions[sub];
    if (!subInfo) continue;
    for (const reg of subInfo.regions) {
      const r = geography.regions[reg];
      if (r) r.areas.forEach((a) => out.add(a));
    }
  }
  for (const r of rec.regions || []) {
    const region = geography.regions[r];
    if (region) region.areas.forEach((a) => out.add(a));
  }
  for (const a of rec.areas || []) out.add(a);
  // Province entries: bubble up to parent area for tinting.
  for (const p of rec.provinces || []) {
    const pInfo = geography.provinces[p];
    if (pInfo && pInfo.area) out.add(pInfo.area);
  }
  // Direct location entries: include their parent area too so they get tinted.
  for (const l of [...(rec.locations || []), ...(rec.must_own || [])]) {
    const info = geography.locations[l];
    if (info && info.area) out.add(info.area);
  }
  return out;
}

function buildTerritoryIndex() {
  // formable -> areas
  for (const rec of formables) {
    formableTerritory[rec.block_key] = expandToAreas(rec);
  }
  // area -> formables (sorted by primacy)
  const tmp = {};
  for (const rec of formables) {
    for (const area of formableTerritory[rec.block_key]) {
      (tmp[area] = tmp[area] || []).push(rec);
    }
  }
  for (const area in tmp) {
    tmp[area].sort(primacyCompare);
  }
  areaToFormables = tmp;
}

const SOURCE_RANK = {
  mod_new: 0,
  "vanilla+mod_replace": 1,
  "vanilla+mod_inject": 2,
  vanilla: 3,
};

function primacyCompare(a, b) {
  const sa = SOURCE_RANK[a.source] ?? 4;
  const sb = SOURCE_RANK[b.source] ?? 4;
  if (sa !== sb) return sa - sb;
  // Smaller territory = more specific
  const ta = formableTerritory[a.block_key].size;
  const tb = formableTerritory[b.block_key].size;
  if (ta !== tb) return ta - tb;
  return (a.tag || a.block_key).localeCompare(b.tag || b.block_key);
}

// ---- color hashing ------------------------------------------------------

function colorForTag(s) {
  if (!s) return "#888";
  // FNV-ish hash
  let h = 0x811c9dc5;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = (h * 0x01000193) >>> 0;
  }
  const hue = h % 360;
  // Skewed sat/lightness to avoid neon while staying distinguishable.
  const sat = 55 + (h % 25);
  const lit = 50 + ((h >> 8) % 12);
  return `hsl(${hue}, ${sat}%, ${lit}%)`;
}

// EU5 loc values redirect with $KEY$ and embed scripted helpers like
// [ShowAreaName('foo_area')] or [ShowReligionAdjective('catholic')].
// Resolve all of these so display strings render cleanly.
const REF_RE = /\$([A-Za-z_][A-Za-z0-9_]*)\$/g;
// Generic [ShowFooName(...)] / [ShowFooNameWithNoTooltip(...)] -> loc[X]
const SHOW_NAME_RE = /\[Show\w*Name(?:WithNoTooltip)?\(\s*'([^']+)'\s*\)\]/g;
// Generic [ShowFooAdjective(...)] / [ShowFooAdjectiveWithNoTooltip(...)] -> loc[X_ADJ] || loc[X]
const SHOW_ADJ_RE = /\[Show\w*Adjective(?:WithNoTooltip)?\(\s*'([^']+)'\s*\)\]/g;
// Anything else like [GetThing] or [SomeFunc.foo] gets stripped as a fallback.
const SHOW_FALLBACK_RE = /\[[^\]]*\]/g;

function resolveLoc(value, depth = 0) {
  if (!value || depth > 5) return value || "";
  let out = value.replace(REF_RE, (whole, key) => {
    const v = loc[key];
    return v ? resolveLoc(v, depth + 1) : whole;
  });
  out = out.replace(SHOW_NAME_RE, (whole, key) => {
    const v = loc[key];
    return v ? resolveLoc(v, depth + 1) : prettifyName(key);
  });
  out = out.replace(SHOW_ADJ_RE, (whole, key) => {
    const v = loc[key + "_ADJ"] || loc[key];
    return v ? resolveLoc(v, depth + 1) : prettifyName(key);
  });
  // Strip any remaining unhandled [...] markup so users do not see raw
  // game-code helpers.
  out = out.replace(SHOW_FALLBACK_RE, "");
  return out;
}

function lookupLoc(key) {
  if (!key) return null;
  const v = loc[key];
  if (v == null) return null;
  return resolveLoc(v);
}

function displayName(rec) {
  const candidates = [
    rec.tag,                              // SWE -> "Sweden"
    rec.name,                              // explicit name field
    rec.block_key,                         // sweden_f
    rec.tag && rec.tag + "_f",             // BOH_f redirects to $BOH$
  ].filter(Boolean);
  let base = null;
  for (const k of candidates) {
    const v = lookupLoc(k);
    if (v) { base = v; break; }
  }
  if (!base) base = rec.block_key.replace(/_f$/, "").replace(/_/g, " ");
  if (rec.variant_label) {
    return `${base} (${rec.variant_label})`;
  }
  return base;
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
  const allowedLevels = currentAllowedLevels();
  const allowedSources = currentAllowedSources();
  const filtered = formables.filter((f) => {
    if (term && !f._haystack.includes(term)) return false;
    if (f.level != null && !allowedLevels.has(f.level)) return false;
    if (!isSourceAllowed(f, allowedSources)) return false;
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
  row.addEventListener("mouseenter", (ev) => showHoverCard(rec, ev, null));
  row.addEventListener("mousemove", (ev) => positionHoverCard(ev));
  row.addEventListener("mouseleave", hideHoverCard);
  return row;
}

// ---- selection / detail panel ------------------------------------------

function selectFormable(rec, opts = {}) {
  selected = rec;
  $list.querySelectorAll(".formable-row").forEach((r) => {
    r.classList.toggle("selected", r.dataset.key === rec.block_key);
  });
  showPins(rec);
  showDetail(rec);
  restyleAreaLayer();
  if (opts.skipFit) return;
  const tb = territoryBounds(rec);
  if (tb) {
    map.fitBounds(tb.pad(0.15), { maxZoom: 5, animate: true });
  }
}

// Track the area whose claimants we are cycling through so repeated
// clicks on the same area advance to the next visible claimant.
let lastClickedArea = null;
// Last mouse event over a polygon, kept so we can re-render the hover
// card after a selection cycle without waiting for another mousemove.
let lastHoverEvent = null;

function cycleSelectionForArea(areaName) {
  const claimants = visibleClaimantsFor(areaName);
  if (claimants.length === 0) {
    if (selected) clearSelectionAndRestyle();
    lastClickedArea = null;
    return;
  }
  let next;
  if (lastClickedArea !== areaName || !selected) {
    lastClickedArea = areaName;
    next = claimants[0];
    selectFormable(next);
  } else {
    const idx = claimants.findIndex((c) => c.block_key === selected.block_key);
    next = claimants[(idx + 1) % claimants.length];
    selectFormable(next, { skipFit: true });
  }
  // Re-render the hover card so the just-selected claimant becomes the
  // main entry instead of the area's primary.
  if (lastHoverEvent && !$hoverCard.hidden) {
    showHoverCard(next, lastHoverEvent, areaName);
  }
}

// ---- area polygon rendering --------------------------------------------

function renderAreaLayer() {
  // Initial set: the worlds visible in the current viewport plus one
  // buffer copy on each side. After this initial render, updateWraps
  // takes over on every map move.
  updateWraps();
}

function createAreaCopy(worldIndex) {
  const shifted = flipGeoJson(areasGeoJson, worldIndex * NATIVE_W);
  return L.geoJSON(shifted, {
    style: areaStyle,
    interactive: true,
    onEachFeature: (feature, layer) => {
      const areaName = feature.properties.name;
      layer.on("click", (e) => {
        L.DomEvent.stopPropagation(e);
        cycleSelectionForArea(areaName);
      });
      layer.on("mouseover", (e) => {
        lastHoverEvent = e;
        const claimants = visibleClaimantsFor(areaName);
        if (claimants.length === 0) return;
        // If the user has cycled to a specific claimant of this area,
        // show that one as the main entry; otherwise the primary.
        let main = claimants[0];
        if (selected && claimants.some((c) => c.block_key === selected.block_key)) {
          main = selected;
        }
        showHoverCard(main, e, areaName);
      });
      layer.on("mousemove", (e) => {
        lastHoverEvent = e;
        positionHoverCard(e);
      });
      layer.on("mouseout", () => {
        lastHoverEvent = null;
        hideHoverCard();
      });
    },
  }).addTo(map);
}

function createPinCopy(worldIndex) {
  const grp = L.layerGroup().addTo(map);
  if (!selected) return grp;
  const dx = worldIndex * NATIVE_W;
  for (const locName of selected.must_own) {
    const info = locIndex[locName];
    if (!info) continue;
    const [cx, cy] = info.centroid;
    const labelText = lookupLoc(locName) || prettifyName(locName);
    L.marker(L.latLng(-cy, cx + dx), {
      icon: L.divIcon({
        className: "must-own-marker",
        html: `<div class="must-own-pin"></div><div class="must-own-label">${escapeHtml(labelText)}</div>`,
        iconSize: [14, 14],
        iconAnchor: [7, 7],
      }),
      keyboard: false,
    }).addTo(grp);
  }
  return grp;
}

function visibleWorldRange() {
  const b = map.getBounds();
  // Keep a 1-world buffer on each side so the user doesn't see polygons
  // pop in mid-drag.
  const lo = Math.floor(b.getWest() / NATIVE_W) - 1;
  const hi = Math.ceil(b.getEast() / NATIVE_W) + 1;
  return [lo, hi];
}

function updateWraps() {
  const [lo, hi] = visibleWorldRange();
  const needed = new Set();
  for (let k = lo; k <= hi; k++) needed.add(k);

  // Remove copies that have left the buffered range.
  for (const k of [...areaLayers.keys()]) {
    if (!needed.has(k)) {
      map.removeLayer(areaLayers.get(k));
      areaLayers.delete(k);
    }
  }
  for (const k of [...pinLayers.keys()]) {
    if (!needed.has(k)) {
      map.removeLayer(pinLayers.get(k));
      pinLayers.delete(k);
    }
  }
  // Add copies for newly-visible worlds.
  for (const k of needed) {
    if (!areaLayers.has(k)) {
      areaLayers.set(k, createAreaCopy(k));
    }
    if (!pinLayers.has(k)) {
      pinLayers.set(k, createPinCopy(k));
    }
  }
}

function visibleClaimantsFor(areaName) {
  const claimants = areaToFormables[areaName];
  if (!claimants) return [];
  const allowedLevels = currentAllowedLevels();
  const allowedSources = currentAllowedSources();
  return claimants.filter(
    (c) => (c.level == null || allowedLevels.has(c.level)) &&
           isSourceAllowed(c, allowedSources)
  );
}

function visiblePrimaryFor(areaName) {
  const list = visibleClaimantsFor(areaName);
  return list.length > 0 ? list[0] : null;
}

function areaStyle(feature) {
  const areaName = feature.properties.name;
  const primary = visiblePrimaryFor(areaName);

  if (!primary) {
    // No visible claimant: hide entirely.
    return { stroke: false, fill: false, fillOpacity: 0, opacity: 0 };
  }

  const primaryColor = primary._color;

  if (!selected) {
    return {
      stroke: false,
      fill: true,
      fillColor: primaryColor,
      fillOpacity: 0.32,
    };
  }
  const isInSelected = formableTerritory[selected.block_key].has(areaName);
  if (isInSelected) {
    return {
      stroke: true,
      color: selected._color,
      weight: 1.5,
      opacity: 0.9,
      fill: true,
      fillColor: selected._color,
      fillOpacity: 0.55,
    };
  }
  return {
    stroke: false,
    fill: true,
    fillColor: primaryColor,
    fillOpacity: 0.06,
  };
}

function restyleAreaLayer() {
  for (const layer of areaLayers.values()) {
    layer.setStyle(areaStyle);
  }
}

function rebuildPinCopies() {
  for (const [k, grp] of pinLayers) {
    map.removeLayer(grp);
    pinLayers.set(k, createPinCopy(k));
  }
}

function clearSelectionAndRestyle() {
  clearSelection();
  restyleAreaLayer();
}

function showPins(rec) {
  // Pins live inside per-world layer groups managed by updateWraps.
  // Rebuild them so all currently-live copies reflect the new selection.
  rebuildPinCopies();
}

function clearPins() {
  for (const [k, grp] of pinLayers) {
    map.removeLayer(grp);
    pinLayers.set(k, L.layerGroup().addTo(map));
  }
}

function renderRequirementsTab(rec) {
  const body = [];

  if (rec._description) {
    body.push(`<p style="margin:0 0 12px;color:var(--fg-1);font-size:12px;line-height:1.5;">${escapeHtml(rec._description)}</p>`);
  }

  body.push('<div class="stat-grid">');
  if (rec.level != null) body.push(`<dt>Level</dt><dd>${rec.level}</dd>`);
  if (rec.fraction != null) body.push(`<dt>Required</dt><dd>${Math.round(rec.fraction * 100)}% of territory</dd>`);
  if (rec.rule) body.push(`<dt>Rule</dt><dd>${escapeHtml(rec.rule)}</dd>`);
  if (rec.tag) body.push(`<dt>Tag</dt><dd><code>${escapeHtml(rec.tag)}</code></dd>`);
  if (rec._adjective) body.push(`<dt>Adjective</dt><dd>${escapeHtml(rec._adjective)}</dd>`);
  body.push(`<dt>Source</dt><dd>${formatSource(rec)}</dd>`);
  if (rec.formation_event) body.push(`<dt>Formation event</dt><dd>Triggered on formation</dd>`);
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

  if (rec.english_potential && rec.english_potential.length > 0) {
    body.push("<h3>Required to enable</h3>");
    body.push(renderRequirementList(rec.english_potential));
  }
  if (rec.english_allow && rec.english_allow.length > 0) {
    body.push("<h3>Required to form</h3>");
    body.push(renderRequirementList(rec.english_allow));
  }

  // Surface any other formables that share areas with this one, so users
  // can pivot quickly between competing claims.
  const otherClaimants = collectOtherClaimants(rec);
  if (otherClaimants.length > 0) {
    body.push("<h3>Also claimed in this territory</h3>");
    body.push('<div class="claimants-list">');
    for (const o of otherClaimants) {
      body.push(
        `<button class="claimant-row" data-key="${escapeHtml(o.block_key)}">` +
        `<span class="claimant-swatch" style="background:${o._color}"></span>` +
        `<span class="claimant-name">${escapeHtml(o._displayName)}</span>` +
        `<span class="claimant-tag">${escapeHtml(o.tag || "")}</span>` +
        `</button>`
      );
    }
    body.push("</div>");
  }

  // Hint that a strategy guide is available; clicking it switches tabs.
  if (starters[rec.block_key]) {
    body.push(
      '<div class="guide-hint"><button type="button" data-switch-tab="guide">' +
      'Strategy guide available &rarr;</button></div>'
    );
  }

  return body.join("");
}

function titleCase(s) {
  return s.replace(/\b\w/g, (c) => c.toUpperCase());
}

function prettifyCulture(s) {
  if (!s) return "";
  const cleaned = s.replace(/_culture$/, "").replace(/_group$/, "").replace(/_/g, " ");
  return titleCase(cleaned);
}

function prettifyReligion(s) {
  if (!s) return "";
  return titleCase(s.replace(/_/g, " "));
}

function renderGuideTab(rec) {
  const guide = starters[rec.block_key];
  const body = [];

  body.push(
    '<p class="guide-intro">Tags ranked by how well they match the formation gates ' +
    '(culture / religion if required) and how much of the required territory ' +
    'they already control at game start.</p>'
  );

  if (!guide || !guide.candidates || guide.candidates.length === 0) {
    body.push(
      '<p class="guide-empty">No automatic recommendation. This formable either has ' +
      'no culture / religion / territory gates we can match against, or requires ' +
      'an event chain rather than playing as a specific tag.</p>'
    );
    return body.join("");
  }

  // Show the matched gates so the player understands the constraint.
  // Dedupe across culture / culture_group and religion / religion_group
  // because the parser captures the same scoped value into both buckets.
  const gateBits = [];
  const seenC = new Set();
  const cul = [...(guide.culture_gates || []), ...(guide.culture_group_gates || [])]
    .map(prettifyCulture)
    .filter((c) => c && !seenC.has(c.toLowerCase()) && seenC.add(c.toLowerCase()));
  const seenR = new Set();
  const rel = [...(guide.religion_gates || []), ...(guide.religion_group_gates || [])]
    .map(prettifyReligion)
    .filter((r) => r && !seenR.has(r.toLowerCase()) && seenR.add(r.toLowerCase()));
  if (cul.length) gateBits.push(`<dt>Culture gate</dt><dd>${cul.map((c) => escapeHtml(c)).join(", ")}</dd>`);
  if (rel.length) gateBits.push(`<dt>Religion gate</dt><dd>${rel.map((r) => escapeHtml(r)).join(", ")}</dd>`);
  if (gateBits.length) {
    body.push('<div class="stat-grid">');
    body.push(gateBits.join(""));
    body.push("</div>");
  }

  body.push("<h3>Recommended starting tags</h3>");
  body.push('<div class="starter-list">');
  for (const c of guide.candidates) {
    const resolved = lookupLoc(c.tag);
    const hasName = resolved && resolved !== c.tag;
    const head = hasName
      ? `<strong>${escapeHtml(resolved)}</strong> <code>${escapeHtml(c.tag)}</code>`
      : `<strong>${escapeHtml(c.tag)}</strong>`;
    const culture = c.culture ? `<span class="starter-meta">${escapeHtml(prettifyCulture(c.culture))}</span>` : "";
    const religion = c.religion ? `<span class="starter-meta">${escapeHtml(prettifyReligion(c.religion))}</span>` : "";
    const geo = c.owned_in_target > 0
      ? `<span class="starter-meta">${c.owned_in_target} starting location${c.owned_in_target === 1 ? "" : "s"} in target</span>`
      : "";
    body.push(
      `<div class="starter-row">` +
      `<div class="starter-head">${head}</div>` +
      `<div class="starter-meta-row">${culture}${religion}${geo}</div>` +
      `</div>`
    );
  }
  body.push("</div>");

  body.push(
    '<p class="guide-footnote">Heuristic: tags whose culture / religion satisfy the ' +
    'gate, ranked by overlap between their starting territory and the formable’s ' +
    'required regions / areas / locations. The list is auto-derived; nuance like ' +
    'event chains or vassal-release paths is not yet captured.</p>'
  );

  return body.join("");
}

function showDetail(rec) {
  $detail.hidden = false;
  $detailName.textContent = rec._displayName;

  const tabs = [
    { id: "requirements", label: "Requirements", render: renderRequirementsTab },
    { id: "guide", label: "Guide", render: renderGuideTab },
  ];
  const initial = "requirements";

  const headerHtml =
    '<div class="tabs" role="tablist">' +
    tabs.map((t) =>
      `<button type="button" role="tab" class="tab" data-tab="${t.id}"` +
      `${t.id === initial ? ' aria-selected="true"' : ''}>${escapeHtml(t.label)}</button>`
    ).join("") +
    '</div>' +
    '<div class="tab-panels"></div>';
  $detailBody.innerHTML = headerHtml;

  const $panels = $detailBody.querySelector(".tab-panels");
  const $tabs = $detailBody.querySelectorAll(".tab");

  function activate(tabId) {
    const t = tabs.find((x) => x.id === tabId) || tabs[0];
    $tabs.forEach((b) => {
      const sel = b.dataset.tab === t.id;
      b.toggleAttribute("aria-selected", sel);
      b.classList.toggle("active", sel);
    });
    $panels.innerHTML = t.render(rec);
    bindPanel($panels);
  }

  function bindPanel(scope) {
    scope.querySelectorAll(".claimant-row").forEach((btn) => {
      btn.addEventListener("click", () => {
        const r = formablesByKey[btn.dataset.key];
        if (r) selectFormable(r);
      });
    });
    scope.querySelectorAll("[data-switch-tab]").forEach((btn) => {
      btn.addEventListener("click", () => activate(btn.dataset.switchTab));
    });
  }

  $tabs.forEach((b) => b.addEventListener("click", () => activate(b.dataset.tab)));
  activate(initial);
}

function renderRequirementList(clauses) {
  const parts = ["<ul class=\"req-list\">"];
  for (const c of clauses) {
    parts.push(renderRequirementItem(c));
  }
  parts.push("</ul>");
  return parts.join("");
}

function renderRequirementItem(c) {
  const cls = c.kind === "or" || c.kind === "not" || c.kind === "and"
    ? `req-${c.kind}` : "";
  const out = [`<li class="${cls}">`, escapeHtml(c.text)];
  if (c.children && c.children.length > 0) {
    out.push("<ul class=\"req-list\">");
    for (const cc of c.children) out.push(renderRequirementItem(cc));
    out.push("</ul>");
  }
  out.push("</li>");
  return out.join("");
}

function collectOtherClaimants(rec) {
  const otherSet = new Map();
  for (const area of formableTerritory[rec.block_key] || []) {
    const claimants = areaToFormables[area] || [];
    for (const c of claimants) {
      if (c.block_key === rec.block_key) continue;
      if (!otherSet.has(c.block_key)) otherSet.set(c.block_key, c);
    }
  }
  return [...otherSet.values()].sort(primacyCompare);
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
  lastClickedArea = null;
  clearPins();
  $detail.hidden = true;
  $list.querySelectorAll(".formable-row.selected").forEach((r) => r.classList.remove("selected"));
}

// X button just hides the detail panel; the selection (and its territory
// tint on the map) persists. Re-open by clicking the formable in the
// list or any of its claimed areas on the map.
$detailClose.addEventListener("click", () => {
  $detail.hidden = true;
});
$search.addEventListener("input", renderList);

function currentAllowedLevels() {
  const set = new Set();
  document.querySelectorAll('#level-filter input[type="checkbox"]').forEach((b) => {
    if (b.checked) set.add(parseInt(b.dataset.lvl, 10));
  });
  return set;
}
function currentAllowedSources() {
  const set = new Set();
  document.querySelectorAll('#source-filter input[type="checkbox"]').forEach((b) => {
    if (b.checked) set.add(b.dataset.src);
  });
  return set;
}
function isSourceAllowed(rec, allowed) {
  if (rec.source === "mod_new") return allowed.has("mod_new");
  if (rec.mod_overrides) return allowed.has("enhanced");
  return false;  // pure vanilla is excluded entirely (filtered earlier)
}

function onFiltersChanged() {
  renderList();
  restyleAreaLayer();
  if (selected && !isFormableVisible(selected)) {
    clearSelectionAndRestyle();
  }
}
function isFormableVisible(rec) {
  if (rec.level != null && !currentAllowedLevels().has(rec.level)) return false;
  if (!isSourceAllowed(rec, currentAllowedSources())) return false;
  return true;
}
document.querySelectorAll(
  '#level-filter input[type="checkbox"], #source-filter input[type="checkbox"]'
).forEach((b) => b.addEventListener("change", onFiltersChanged));

// Click anywhere on the map that is NOT a claimed area polygon: deselect.
// (Polygon click handlers stop propagation, so this only fires for empty
// space and unclaimed areas.)
map.on("click", () => {
  if (selected) clearSelectionAndRestyle();
  lastClickedArea = null;
});

// Maintain wrap copies as the viewport moves.
map.on("moveend", updateWraps);

// ---- hover card --------------------------------------------------------

const $hoverCard = document.getElementById("hover-card");
const $mapPane = document.getElementById("map-pane");

function showHoverCard(rec, ev, areaName) {
  const claimants = areaName ? visibleClaimantsFor(areaName) : [];
  const fields = [];
  fields.push(
    `<div class="hc-title">` +
    `<span class="hc-swatch" style="background:${rec._color}"></span>` +
    `${escapeHtml(rec._displayName)}` +
    (rec.tag ? `<span class="hc-tag">${escapeHtml(rec.tag)}</span>` : "") +
    `</div>`
  );
  const meta = [];
  if (rec.level != null) meta.push(`Level ${rec.level}`);
  if (rec.fraction != null) meta.push(`${Math.round(rec.fraction * 100)}% required`);
  meta.push(formatSourceShort(rec));
  fields.push(`<div class="hc-meta">${escapeHtml(meta.join(" · "))}</div>`);
  if (rec.must_own && rec.must_own.length > 0) {
    const labels = rec.must_own.map((l) => lookupLoc(l) || prettifyName(l));
    fields.push(`<div class="hc-meta">Must own: ${escapeHtml(labels.join(", "))}</div>`);
  }
  // List every claimant with its color swatch when more than one applies
  // to this hovered area, plus a cycle hint.
  if (claimants.length > 1) {
    const items = claimants.map((c, i) => {
      const isCurrent = selected && c.block_key === selected.block_key;
      const cls = isCurrent ? "hc-claimant hc-claimant-current" : "hc-claimant";
      return (
        `<li class="${cls}">` +
        `<span class="hc-swatch" style="background:${c._color}"></span>` +
        `<span class="hc-claimant-name">${escapeHtml(c._displayName)}</span>` +
        `<span class="hc-tag">${escapeHtml(c.tag || "")}</span>` +
        `</li>`
      );
    }).join("");
    fields.push(
      `<div class="hc-claimants-label">Claimed by ${claimants.length} formables</div>` +
      `<ul class="hc-claimants">${items}</ul>` +
      `<div class="hc-claim-hint">Click to select. Click again to cycle through claimants.</div>`
    );
  }
  $hoverCard.innerHTML = fields.join("");
  $hoverCard.hidden = false;
  positionHoverCard(ev);
}

function hideHoverCard() {
  $hoverCard.hidden = true;
}

function positionHoverCard(ev) {
  // Use clientX/Y minus the map-pane offset since the card is absolutely
  // positioned within #map-pane.
  const rect = $mapPane.getBoundingClientRect();
  const x = (ev.clientX ?? ev.originalEvent?.clientX ?? 0) - rect.left;
  const y = (ev.clientY ?? ev.originalEvent?.clientY ?? 0) - rect.top;
  // Offset so cursor does not cover the card; flip if hitting right edge.
  const padding = 14;
  const cardRect = $hoverCard.getBoundingClientRect();
  let cx = x + padding;
  let cy = y + padding;
  if (cx + cardRect.width > rect.width) cx = x - padding - cardRect.width;
  if (cy + cardRect.height > rect.height) cy = y - padding - cardRect.height;
  $hoverCard.style.left = Math.max(0, cx) + "px";
  $hoverCard.style.top = Math.max(0, cy) + "px";
}

function formatSourceShort(rec) {
  switch (rec.source) {
    case "vanilla+mod_inject": return "Vanilla + mod additions";
    case "vanilla+mod_replace": return "Mod replaces vanilla";
    case "mod_new": return "New (mod-added)";
    case "vanilla": return "Vanilla";
    default: return rec.source || "";
  }
}

loadAll().catch((err) => {
  console.error("data load failed:", err);
  $list.innerHTML = `<div style="padding:16px;color:#ff8080;">Failed to load data: ${escapeHtml(err.message)}</div>`;
});
