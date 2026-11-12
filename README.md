# National Destinies, Site

Interactive map and database for the **National Destinies** mod for *Europa Universalis V*.

The mod adds unique formation events, advance trees, units, buildings, and post-formation destiny missions to every formable country in EU5. This site lets you browse those formables visually: where they sit on the map, what they require, and what content they unlock.

> Live site: https://trinedi.github.io/national_destinies_site/

> Mod on Steam Workshop: https://steamcommunity.com/sharedfiles/filedetails/?id=3668193813

## Build (maintainers only)

The build reads from a local clone of the mod and from the EU5 game install. Both paths are configured in `build.config.yaml`. Adjust those if your setup differs.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# Daily: refresh formables / loc / requirements after mod changes (~1s)
.venv/bin/python scripts/build/build_site.py

# Less common: refresh everything including tiles & polygons (~5 min)
.venv/bin/python scripts/build/build_site.py --full
```

`dist/` is the deployable output. After running the build, commit and
push; the GitHub Pages workflow uploads `dist/` automatically.

## What gets generated

- `data/locations_index.json`, per-location centroid, bounding box, pixel count.
- `dist/tiles/{z}/{x}/{y}.png`, base map tile pyramid for Leaflet.
- `dist/data/*.json`, the formables, their requirements in English, their guides and the geography.
- `dist/<name>.html`, one text page per `data/pages/<name>.md` (`features.html` explains each part of the mod). The Workshop description links to their sections, and the build fails when such a link has no section to land on.

## License

The site code is MIT. Map assets and game data are property of Paradox Interactive.
