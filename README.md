# National Destinies, Site

Interactive map and database for the **National Destinies** mod for *Europa Universalis V*.

The mod adds unique formation events, advance trees, units, buildings, and post-formation destiny missions to every formable country in EU5. This site lets you browse those formables visually: where they sit on the map, what they require, and what content they unlock.

> Live site: *(coming soon)*

> Mod on Steam Workshop: *(link pending)*

## Build (maintainers only)

The build reads from a local clone of the mod and from the EU5 game install. Both paths are configured in `build.config.yaml`. Adjust those if your setup differs.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/build/extract_map.py   # ~6s, parses 28k locations
.venv/bin/python scripts/build/tile_map.py      # ~20s, 2700 tiles
# more steps land as the pipeline grows
```

## What gets generated

- `data/locations_index.json`, per-location centroid, bounding box, pixel count.
- `dist/tiles/{z}/{x}/{y}.png`, base map tile pyramid for Leaflet.
- More to come, geography tree, formable index, requirements, destiny graphs.

## License

The site code is MIT. Map assets and game data are property of Paradox Interactive.
