#!/usr/bin/env python3
"""Screenshot the Atlas with headless Firefox, to look at a change before pushing.

    screenshot.py page '#MEX_f/content' out.png     the page as a visitor sees it
    screenshot.py tab mex out.png                   one country's whole Content tab, full length

Firefox takes its screenshot at the page's load event, which comes before the
Atlas has fetched its data. So `page` serves the real index.html with one
extra image that answers late, holding the load event back until the page has
drawn, and `tab` renders the Content tab with synchronous requests on a page
with no map. A long `tab` picture is also cut into pieces of --piece pixels
(out_0.png, out_1.png ...), a size that can be read comfortably.
"""

from __future__ import annotations

import argparse
import http.server
import socketserver
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

from PIL import Image, ImageChops

DIST = Path(__file__).resolve().parents[2] / "dist"
SECONDS_FOR_THE_PAGE_TO_DRAW = 6
PANEL_WIDTH = 820

TAB_PAGE = """<!DOCTYPE html>
<html><head><meta charset="utf-8">
<link rel="stylesheet" href="app.css"><link rel="stylesheet" href="content.css">
<style>html,body{overflow:visible;height:auto} #detail{position:static;max-height:none;margin:12px;width:%(width)dpx}
#detail-body{overflow:visible} .ct-nav{position:static}</style></head>
<body><section id="detail"><header><h2>%(key)s</h2></header>
<div id="detail-body"><div class="tab-panels"><div class="ct" id="target"></div></div></div></section>
<script>
function get(url) { const x = new XMLHttpRequest(); x.open("GET", url, false); x.send(); return x.responseText; }
const source = get("content.js").replace(/^export /gm, "");
const html = new Function(source + "\\nreturn render;")()(JSON.parse(get("data/content/%(key)s.json")));
document.getElementById("target").innerHTML = html.replace(/loading="lazy"/g, "");
if (%(unfold)s) {
  for (const d of document.querySelectorAll("details")) d.open = true;
  for (const d of document.querySelectorAll(".ct-desc")) d.classList.add("open");
}
</script></body></html>
"""


class Handler(http.server.SimpleHTTPRequestHandler):
    tab_page = ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIST), **kwargs)

    def _send_html(self, text: str) -> None:
        body = text.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith("/__late.png"):
            time.sleep(SECONDS_FOR_THE_PAGE_TO_DRAW)
            self.send_response(204)
            self.end_headers()
        elif self.path.startswith("/__page.html"):
            page = (DIST / "index.html").read_text()
            self._send_html(page.replace("</body>", '<img src="/__late.png" alt=""></body>'))
        elif self.path.startswith("/__tab.html"):
            self._send_html(self.tab_page)
        else:
            super().do_GET()

    def log_message(self, *args):
        pass


class Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True


def firefox_screenshot(url: str, out: Path, width: int, height: int) -> None:
    with tempfile.TemporaryDirectory() as profile:
        subprocess.run(
            ["firefox", "--headless", "--profile", profile,
             f"--window-size={width},{height}", "--screenshot", str(out), url],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120,
        )


def trim_and_cut(out: Path, piece: int) -> int:
    image = Image.open(out).convert("RGB")
    background = Image.new("RGB", image.size, image.getpixel((2, image.size[1] - 2)))
    drawn = ImageChops.difference(image, background).getbbox()
    image = image.crop((0, 0, image.size[0], min(image.size[1], drawn[3] + 12)))
    image.save(out)
    pieces = 0
    for top in range(0, image.size[1], piece):
        image.crop((0, top, image.size[0], min(image.size[1], top + piece))).save(
            out.with_name(f"{out.stem}_{pieces}{out.suffix}"))
        pieces += 1
    return pieces


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("mode", choices=["page", "tab"])
    parser.add_argument("target", help="page: the address hash, '#MEX_f/content'. tab: a content key, 'mex'")
    parser.add_argument("out", type=Path)
    parser.add_argument("--size", default="1700x1050", help="page: window size")
    parser.add_argument("--unfold", action="store_true", help="tab: open every fold and full description")
    parser.add_argument("--piece", type=int, default=1300, help="tab: height of each piece")
    args = parser.parse_args()

    server = Server(("127.0.0.1", 0), Handler)
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        if args.mode == "page":
            width, height = (int(n) for n in args.size.split("x"))
            firefox_screenshot(f"http://127.0.0.1:{port}/__page.html{args.target}", args.out, width, height)
            print(args.out)
        else:
            if not (DIST / "data/content" / f"{args.target}.json").exists():
                print(f"no content file for '{args.target}' in dist/data/content", file=sys.stderr)
                return 1
            Handler.tab_page = TAB_PAGE % {
                "key": args.target, "width": PANEL_WIDTH, "unfold": "true" if args.unfold else "false"}
            # The window is far taller than any tab, and the empty rest is trimmed off.
            firefox_screenshot(f"http://127.0.0.1:{port}/__tab.html", args.out, PANEL_WIDTH + 40, 16000)
            pieces = trim_and_cut(args.out, args.piece)
            print(f"{args.out} and {pieces} pieces")
    finally:
        server.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
