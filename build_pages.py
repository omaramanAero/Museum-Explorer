"""Writes index.html, one page per exhibit (exhibit/<ID>/index.html) and cards.html."""
import json, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
data = json.loads((SITE / "data/exhibits.json").read_text())

# design-system component CSS is the single source for components
DS = Path("/tmp/claude-0/-home-claude/898a7bc2-c318-5fd4-a86f-114cc663fbd0/scratchpad/ds/project/components/bundle.css")
if DS.exists():
    shutil.copy(DS, SITE / "assets/mek.css")

HEAD = """<!doctype html>
<html lang="en" data-page="{page}" data-base="{base}"{extra}>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="theme-color" content="#14130f" media="(prefers-color-scheme: dark)">
<meta name="theme-color" content="#f4efe6" media="(prefers-color-scheme: light)">
<link rel="icon" href="{base}assets/icon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{base}assets/tokens.css">
<link rel="stylesheet" href="{base}assets/mek.css">
<link rel="stylesheet" href="{base}vendor/leaflet/leaflet.css">
<link rel="stylesheet" href="{base}assets/app.css">
{mv}<script src="{base}vendor/leaflet/leaflet.js" defer></script>
<script src="{base}assets/app.js" defer></script>
</head>
<body class="mek-root">
<a class="sr-only" href="#main">Skip to content</a>
<header class="top" id="top"></header>
<main id="main"><div class="wrap"><p class="muted" style="padding:32px 0">Loading…</p></div></main>
<footer id="foot"></footer>
</body>
</html>
"""
MV = '<script type="module" src="{base}vendor/model-viewer.min.js"></script>\n'

(SITE / "index.html").write_text(HEAD.format(page="home", base="./", extra="", title="Museum Explorer Karlsruhe",
                                             desc="QR-to-3D exhibit guide for the Naturkundemuseum Karlsruhe: 3D models, AR, anatomy and maps.", mv=""))
for ex in data["exhibits"]:
    d = SITE / "exhibit" / ex["id"]; d.mkdir(parents=True, exist_ok=True)
    (d / "index.html").write_text(HEAD.format(page="exhibit", base="../../", extra=f' data-exhibit="{ex["id"]}"',
                                              title=f'{ex["name"]["en"]} · Museum Explorer Karlsruhe',
                                              desc=f'{ex["name"]["en"]} ({ex["sci"]}): 3D model, AR view, anatomy guide and maps.',
                                              mv=MV.format(base="../../")))

(SITE / "assets/icon.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="7" fill="#2f3b3a"/><rect y="17" width="32" height="6" fill="#b4442a"/><rect y="23" width="32" height="2" fill="#d9a23b"/><circle cx="16" cy="10" r="4" fill="#d9a23b"/></svg>')
print("pages written:", 1 + len(data["exhibits"]))
