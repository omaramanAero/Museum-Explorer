"""Assembles the single-page app.
  site/index.html      standalone page (GitHub Pages etc.)
  artifact/index.html  the same page without the document skeleton, for publishing as a claude.ai artifact
Both share site/models, site/vendor.
"""
import json, re, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE, ART, TOOLS = ROOT / "site", ROOT / "artifact", ROOT / "tools"
data = json.loads((SITE / "data/exhibits.json").read_text())
maps = json.loads((SITE / "data/maps.json").read_text())
DS = Path("/tmp/claude-0/-home-claude/898a7bc2-c318-5fd4-a86f-114cc663fbd0/scratchpad/ds/project/components/bundle.css")
mek = DS.read_text() if DS.exists() else (SITE / "assets/mek.css").read_text()
mek = re.sub(r'@import url\([^)]*\);\n', '', mek)
tokens = (SITE / "assets/tokens.css").read_text()
app_css = (SITE / "assets/app.css").read_text()
app_css = re.sub(r'/\* ---------- maps ---------- \*/.*?/\* ---------- anatomy sheet', '/* ---------- anatomy sheet', app_css, flags=re.S)
app_js = (TOOLS / "app_src.js").read_text()

EXTRA_CSS = """
:root { --map-water: #dfe6e4; --map-land: #e7dcc6; --map-coast: #8a8172; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { --map-water: #1f2a2a; --map-land: #3a352c; --map-coast: #8a8172; color-scheme: dark; } }
:root[data-theme="dark"] { --map-water: #1f2a2a; --map-land: #3a352c; --map-coast: #8a8172; color-scheme: dark; }
html, body { overflow-x: hidden; }
.wrap { max-width: 1120px; margin: 0 auto; padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); }
.top { top: env(safe-area-inset-top, 0px); padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); }
body::before { content: ""; position: fixed; inset: 0 0 auto; height: env(safe-area-inset-top, 0px); z-index: 10; background: var(--paper); }
.stage-tag { background: color-mix(in srgb, var(--surface) 88%, transparent); }
.maps { display: grid; gap: var(--space-4); }
@media (min-width: 760px) { .maps { grid-template-columns: 1fr 1fr; } }
.map-card { background: var(--basalt); color: var(--on-basalt); border-radius: var(--radius-md); padding: var(--space-2); min-width: 0; }
.map-card h3 { font: 600 16px/22px var(--font-sans); margin: var(--space-1) var(--space-2) var(--space-2); display: flex; justify-content: space-between; gap: var(--space-2); align-items: center; flex-wrap: wrap; }
.map-card .map { border-radius: var(--radius-sm); overflow: hidden; background: var(--map-water); }
.map-card .map svg { width: 100%; height: auto; display: block; }
.map-card .map.floor, .map-card .map.empty { background: color-mix(in srgb, var(--on-basalt) 8%, transparent); }
.stage-top { flex-wrap: wrap; }
.real-object { margin: var(--space-3) 0 0; padding: var(--space-3) var(--space-4); border-radius: var(--radius-md); background: var(--bone); font-size: 14px; line-height: 20px; color: var(--ink); }
.map-card .cap { margin: var(--space-2) var(--space-2) var(--space-1); font-size: 13px; line-height: 18px; color: color-mix(in srgb, var(--on-basalt) 85%, transparent); }
.map-card .cap a { color: var(--amber); }
.map-card .mek-tag--illustrative { color: var(--on-basalt); }
.map-empty { min-height: 200px; display: grid; place-items: center; padding: var(--space-6); text-align: center; background: color-mix(in srgb, var(--on-basalt) 8%, transparent); font-size: 15px; }
.hero-card .eyebrow { color: color-mix(in srgb, var(--on-basalt) 80%, transparent); }
model-viewer::part(default-progress-bar) { background-color: var(--rust); height: 3px; }
model-viewer::part(default-ar-button) { display: none; }
@media (prefers-reduced-motion: reduce) { .sheet-wrap, .mek-btn { transition: none; } }
"""

DATA_SCRIPTS = f'<script type="application/json" id="mek-data">{json.dumps(data, ensure_ascii=False).replace("</", "<\\/")}</script>\n' \
               f'<script type="application/json" id="mek-maps">{json.dumps(maps, ensure_ascii=False).replace("</", "<\\/")}</script>\n'
LOADER = """<script>
(function(){var s=document.createElement('script');s.type='module';s.src='vendor/model-viewer.min.js';
s.onerror=function(){var c=document.createElement('script');c.type='module';c.src='https://cdn.jsdelivr.net/npm/@google/model-viewer@4.0.0/dist/model-viewer.min.js';document.head.appendChild(c);};
document.head.appendChild(s);})();
</script>
"""
FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&family=IBM+Plex+Mono:wght@500&family=Instrument+Sans:wght@400;600&display=swap">\n'

STYLE = f"<style>\n/* layout: sticky header, one column on phones, 1.6:1 stage/side grid on desktop; tokens from the Museum Explorer design system */\n{tokens}\n{mek}\n{app_css}\n{EXTRA_CSS}</style>\n"
BODY = """<a class="sr-only" href="#main">Skip to content</a>
<header class="top" id="top"></header>
<main id="main"><div class="wrap"><p class="muted" style="padding:32px 0">Loading…</p></div></main>
<footer id="foot"></footer>
"""
HEAD_META = '<title>Museum Explorer Karlsruhe</title>\n<meta name="claude:viewport-fit-sides" content="cover">\n'

# the artifact host serves no .glb, so the same binaries ship there under a served extension
ART_DATA_SCRIPTS = DATA_SCRIPTS.replace(".glb", ".wasm")
artifact_page = HEAD_META + FONTS + STYLE + BODY + ART_DATA_SCRIPTS + LOADER + "<script>\n" + app_js + "\n</script>\n"
standalone = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="QR-to-3D exhibit guide for the Naturkundemuseum Karlsruhe: 3D models, AR, anatomy and maps.">
<meta name="theme-color" content="#f4efe6">
<link rel="icon" href="assets/icon.svg" type="image/svg+xml">
{HEAD_META}{FONTS}{STYLE}</head>
<body class="mek-root">
{BODY}{DATA_SCRIPTS}{LOADER}<script>
{app_js}
</script>
</body>
</html>
"""
(SITE / "index.html").write_text(standalone)
ART.mkdir(exist_ok=True)
(ART / "index.html").write_text(artifact_page)
for sub in ("models", "vendor"):
    if (ART / sub).exists(): shutil.rmtree(ART / sub)
    shutil.copytree(SITE / sub, ART / sub, ignore=shutil.ignore_patterns("leaflet", "qrcode.js", "*hotspots.json"))
for g in (ART / "models").glob("*.glb"):
    g.rename(g.with_suffix(".wasm"))
shutil.rmtree(SITE / "exhibit", ignore_errors=True)
print("standalone", len(standalone) // 1024, "KB; artifact page", len(artifact_page) // 1024, "KB")
