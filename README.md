# National Destinies — Site

Interactive map and database for the [National Destinies](https://github.com/) EU5 mod.

## Build

```bash
.venv/bin/python scripts/build/build_site.py
```

Reads from `../national_destinies/` (mod files) and the EU5 install (map data),
outputs a static site to `dist/` for GitHub Pages.

## Development

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Configuration in `build.config.yaml`.
