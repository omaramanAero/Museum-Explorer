"""Renders the maps from the project GeoPackage.

Outputs
  site/data/maps.json   -> {"atlantic": "<svg…>", "europe": "<svg…>"}  theme-aware inline SVG for the web app
  out/map_atlantic.png, out/map_europe.png, out/map_qgis_layout.png   -> raster maps for the slides
"""
import json, math, sys, warnings
from pathlib import Path
warnings.filterwarnings("ignore")
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle
from mpl_toolkits.basemap import Basemap
import geopandas as gpd

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "out"
OUT.mkdir(parents=True, exist_ok=True)
GPKG = ROOT / "gis/museum_gis.gpkg"
museum = gpd.read_file(GPKG, layer="museum").iloc[0]
sites = gpd.read_file(GPKG, layer="discovery_sites")
MUS = (museum.geometry.x, museum.geometry.y)
SITES = {r.exhibit_id: (r.geometry.x, r.geometry.y, r.place, r.distance_to_museum_km) for r in sites.itertuples()}

PAPER, BONE, LINE, INK, MUTED, RUST, BASALT, AMBER, SURFACE = "#f4efe6", "#e7dcc6", "#d9cfbd", "#1d1a15", "#5f5747", "#b4442a", "#2f3b3a", "#d9a23b", "#fbf8f2"
WATER = "#dfe6e4"


def great_circle(a, b, n=120):
    r = math.radians
    lo1, la1, lo2, la2 = r(a[0]), r(a[1]), r(b[0]), r(b[1])
    d = 2 * math.asin(math.sqrt(math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2))
    pts = []
    for i in range(n + 1):
        f = i / n; A = math.sin((1 - f) * d) / math.sin(d); B = math.sin(f * d) / math.sin(d)
        x = A * math.cos(la1) * math.cos(lo1) + B * math.cos(la2) * math.cos(lo2)
        y = A * math.cos(la1) * math.sin(lo1) + B * math.cos(la2) * math.sin(lo2)
        z = A * math.sin(la1) + B * math.sin(la2)
        pts.append((math.degrees(math.atan2(y, x)), math.degrees(math.atan2(z, math.hypot(x, y)))))
    return pts


# ------------------------------------------------------------------ shared basemap builders
def make_map(ax, ll, ur, res):
    m = Basemap(projection="merc", llcrnrlon=ll[0], llcrnrlat=ll[1], urcrnrlon=ur[0], urcrnrlat=ur[1], resolution=res, ax=ax)
    m.drawmapboundary(fill_color=WATER, linewidth=0)
    m.fillcontinents(color=BONE, lake_color=WATER, zorder=1)
    m.drawcoastlines(linewidth=0.5, color=MUTED, zorder=2)
    m.drawcountries(linewidth=0.6, color=MUTED, zorder=2)
    return m


def dot(m, lon, lat, color, label, dx=8, dy=8, size=90, ha="left", fs=10, bold=True):
    x, y = m(lon, lat)
    m.ax.scatter([x], [y], s=size, c=color, edgecolors="white", linewidths=1.5, zorder=6)
    m.ax.annotate(label, (x, y), xytext=(dx, dy), textcoords="offset points", fontsize=fs, ha=ha,
                  fontweight="bold" if bold else "normal", color=INK, zorder=7,
                  bbox=dict(boxstyle="round,pad=0.25", fc=SURFACE, ec=LINE, lw=0.6))


def gc_line(m, a, b, color=AMBER):
    pts = great_circle(a, b); xs, ys = zip(*[m(lo, la) for lo, la in pts])
    m.ax.plot(xs, ys, color=color, lw=2.2, ls=(0, (5, 4)), zorder=5)


def scale_bar(m, ax, lon0, lat0, km, label):
    x0, y0 = m(lon0, lat0); x1, _ = m(lon0 + km / (111.32 * math.cos(math.radians(lat0))), lat0)
    ax.plot([x0, x1], [y0, y0], color=INK, lw=3, solid_capstyle="butt", zorder=8)
    ax.plot([x0, (x0 + x1) / 2], [y0, y0], color=PAPER, lw=1.2, zorder=9)
    ax.text((x0 + x1) / 2, y0, label, ha="center", va="bottom", fontsize=8, color=INK, zorder=9, bbox=dict(fc=SURFACE, ec="none", pad=1.5))


def north(ax, x=0.95, y=0.9):
    ax.annotate("N", xy=(x, y + 0.07), xytext=(x, y), xycoords="axes fraction", textcoords="axes fraction", ha="center", va="center",
                fontsize=11, fontweight="bold", color=INK, arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.5), zorder=9)


plt.rcParams["font.family"] = "DejaVu Sans"

# ------------------------------------------------------------------ 1. Atlantic map (PNG)
fig, ax = plt.subplots(figsize=(11, 6.2), dpi=160); fig.patch.set_facecolor(PAPER)
m = make_map(ax, (-115, 12), (25, 62), "l")
bb = SITES["EX01"]
gc_line(m, (bb[0], bb[1]), MUS)
dot(m, bb[0], bb[1], AMBER, "EX01  Big Bend National Park, Texas\nQuetzalcoatlus find site (1971)", dx=10, dy=-26)
dot(m, MUS[0], MUS[1], RUST, "Naturkundemuseum Karlsruhe", dx=-10, dy=12, ha="right")
mx, my = m(-50, 44)
ax.text(mx, my, f"{bb[3]:,.0f} km great-circle", fontsize=9, color=INK, ha="center", bbox=dict(boxstyle="round,pad=0.3", fc=SURFACE, ec=AMBER))
scale_bar(m, ax, -108, 16, 1000, "1 000 km")
north(ax)
ax.set_title("Where the exhibit was found → where it is shown", loc="left", fontsize=12, color=INK, pad=8)
plt.tight_layout(); fig.savefig(OUT / "map_atlantic.png", facecolor=PAPER); plt.close(fig)

# ------------------------------------------------------------------ 2. Europe / Hegau map (PNG)
fig, ax = plt.subplots(figsize=(8.5, 6.6), dpi=160); fig.patch.set_facecolor(PAPER)
m = make_map(ax, (5.6, 46.6), (11.4, 50.6), "h")
hw = SITES["EX02"]
gc_line(m, (hw[0], hw[1]), MUS)
dot(m, MUS[0], MUS[1], RUST, "Naturkundemuseum Karlsruhe\n49.0073° N, 8.4003° E", dx=10, dy=10)
dot(m, hw[0], hw[1], AMBER, f"EX02  Höwenegg, Immendingen (Hegau)\nHippotherium find site · 10.3 Ma · {hw[3]:.0f} km", dx=10, dy=-30)
for name, lo, la in [("Stuttgart", 9.18, 48.78), ("Freiburg", 7.85, 47.99), ("Zürich", 8.54, 47.37), ("Strasbourg", 7.75, 48.57), ("Konstanz", 9.17, 47.66), ("Basel", 7.59, 47.56)]:
    x, y = m(lo, la); ax.scatter([x], [y], s=12, c=MUTED, zorder=4); ax.text(x, y, "  " + name, fontsize=7.5, color=MUTED, va="center", zorder=4)
scale_bar(m, ax, 5.9, 46.8, 50, "50 km")
north(ax)
ax.set_title("Baden-Württemberg: fossil site and museum (EPSG:4326, Mercator)", loc="left", fontsize=11, color=INK, pad=8)
plt.tight_layout(); fig.savefig(OUT / "map_europe.png", facecolor=PAPER); plt.close(fig)

# ------------------------------------------------------------------ 3. QGIS-style print layout (PNG)
fig = plt.figure(figsize=(13.3, 7.5), dpi=150); fig.patch.set_facecolor(SURFACE)
ax = fig.add_axes([0.03, 0.08, 0.66, 0.84])
m = make_map(ax, (-115, 12), (25, 62), "l")
gc_line(m, (bb[0], bb[1]), MUS); gc_line(m, (hw[0], hw[1]), MUS)
dot(m, bb[0], bb[1], AMBER, "EX01 Big Bend NP", dx=10, dy=-18)
dot(m, hw[0], hw[1], AMBER, "EX02 Höwenegg", dx=-10, dy=-22, ha="right")
dot(m, MUS[0], MUS[1], RUST, "SMNK Karlsruhe", dx=10, dy=10)
scale_bar(m, ax, -108, 16, 1000, "1 000 km"); north(ax)
for s in ax.spines.values(): s.set_edgecolor(LINE)
# side panel
px = fig.add_axes([0.715, 0.08, 0.265, 0.84]); px.set_axis_off()
px.add_patch(Rectangle((0, 0), 1, 1, fc=PAPER, ec=LINE, transform=px.transAxes))
px.text(0.06, 0.95, "Museum Explorer Karlsruhe", fontsize=14, fontweight="bold", color=INK, va="top", transform=px.transAxes)
px.text(0.06, 0.885, "Exhibit discovery sites → museum\nmuseum_gis.gpkg · EPSG:4326", fontsize=9, color=MUTED, va="top", transform=px.transAxes)
px.text(0.06, 0.78, "Legend", fontsize=10, fontweight="bold", color=INK, va="top", transform=px.transAxes)
items = [(RUST, "museum  (point, 1)"), (AMBER, "discovery_sites  (point, 2)"), (None, "find_to_museum_lines  (line, 2)")]
for i, (c, t) in enumerate(items):
    y = 0.72 - i * 0.065
    if c: px.scatter([0.1], [y], s=70, c=c, edgecolors="white", linewidths=1.2, transform=px.transAxes, clip_on=False)
    else: px.plot([0.06, 0.14], [y, y], color=AMBER, lw=2.2, ls=(0, (5, 4)), transform=px.transAxes)
    px.text(0.19, y, t, fontsize=9, color=INK, va="center", transform=px.transAxes)
px.text(0.06, 0.49, "Attribute table · exhibits", fontsize=10, fontweight="bold", color=INK, va="top", transform=px.transAxes)
rows = [("EX01", "Quetzalcoatlus", "entrance", "1"), ("EX02", "Three-toed horse", "geology", "0"), ("EX03", "N. Atl. right whale", "whales", "0")]
px.text(0.06, 0.44, "id      name                     zone        verified", fontsize=7.6, family="DejaVu Sans Mono", color=MUTED, va="top", transform=px.transAxes)
for i, r in enumerate(rows):
    px.text(0.06, 0.40 - i * 0.045, f"{r[0]:<7}{r[1]:<24}{r[2]:<11}{r[3]}", fontsize=7.6, family="DejaVu Sans Mono", color=INK, va="top", transform=px.transAxes)
px.text(0.06, 0.22, "Distances (great circle)", fontsize=10, fontweight="bold", color=INK, va="top", transform=px.transAxes)
px.text(0.06, 0.17, f"Big Bend NP → SMNK   {bb[3]:,.0f} km\nHöwenegg → SMNK      {hw[3]:,.0f} km", fontsize=8.5, family="DejaVu Sans Mono", color=INK, va="top", transform=px.transAxes)
px.text(0.06, 0.05, "Data: project GeoPackage; basemap Natural Earth / GSHHG.\nIndoor positions flagged illustrative (verified = 0).", fontsize=7, color=MUTED, va="bottom", transform=px.transAxes)
fig.savefig(OUT / "map_qgis_layout.png", facecolor=SURFACE); plt.close(fig)

# ------------------------------------------------------------------ 4. inline SVG maps for the web app (theme-aware via CSS vars)
def svg_map(ll, ur, res, W, H, features, simplify=0.0):
    """Mercator SVG of coastlines/countries with CSS-token styling."""
    m = Basemap(projection="merc", llcrnrlon=ll[0], llcrnrlat=ll[1], urcrnrlon=ur[0], urcrnrlat=ur[1], resolution=res)
    X, Y = m.xmax - m.xmin, m.ymax - m.ymin
    sx, sy = W / X, H / Y
    def tr(x, y): return (round((x - m.xmin) * sx, 1), round(H - (y - m.ymin) * sy, 1))
    def path(segs, close=False):
        d = []
        for seg in segs:
            pts = [tr(x, y) for x, y in seg]
            if len(pts) < 2: continue
            d.append("M" + " L".join(f"{x},{y}" for x, y in pts) + ("Z" if close else ""))
        return " ".join(d)
    land = path([np.asarray(p) for p in m.landpolygons and [lp.get_coords() for lp in m.landpolygons]], close=True)
    lakes = path([lp.get_coords() for lp in m.lakepolygons], close=True) if getattr(m, "lakepolygons", None) else ""
    fig = plt.figure(); ax = fig.add_subplot(111); m.ax = ax
    cl = m.drawcountries(ax=ax); borders = path(cl.get_segments())
    plt.close(fig)
    body = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="Map">',
            f'<rect width="{W}" height="{H}" fill="var(--map-water)"/>',
            f'<path d="{land}" fill="var(--map-land)" stroke="var(--map-coast)" stroke-width="0.8" fill-rule="evenodd"/>']
    if lakes: body.append(f'<path d="{lakes}" fill="var(--map-water)" stroke="none"/>')
    body.append(f'<path d="{borders}" fill="none" stroke="var(--map-coast)" stroke-width="0.7" stroke-dasharray="3 2"/>')
    for f in features:
        if f["type"] == "gc":
            pts = [tr(*m(lo, la)) for lo, la in great_circle(f["a"], f["b"])]
            body.append('<polyline points="' + " ".join(f"{x},{y}" for x, y in pts) + '" fill="none" stroke="var(--amber)" stroke-width="2.5" stroke-dasharray="7 5" stroke-linecap="round"/>')
        elif f["type"] == "dot":
            x, y = tr(*m(f["lon"], f["lat"]))
            body.append(f'<circle cx="{x}" cy="{y}" r="7" fill="{f["color"]}" stroke="var(--surface)" stroke-width="2.5"/>')
            tx = x + f.get("dx", 12); anchor = f.get("anchor", "start")
            body.append(f'<text x="{tx}" y="{y + f.get("dy", 5)}" text-anchor="{anchor}" font-family="var(--font-sans)" font-size="13" font-weight="600" fill="var(--ink)" stroke="var(--surface)" stroke-width="4" paint-order="stroke" stroke-linejoin="round">{f["label"]}</text>')
        elif f["type"] == "city":
            x, y = tr(*m(f["lon"], f["lat"]))
            body.append(f'<circle cx="{x}" cy="{y}" r="2.5" fill="var(--ink-muted)"/><text x="{x + 6}" y="{y + 4}" font-family="var(--font-sans)" font-size="11" fill="var(--ink-muted)">{f["label"]}</text>')
        elif f["type"] == "scale":
            x0, y0 = tr(*m(f["lon"], f["lat"])); x1, _ = tr(*m(f["lon"] + f["km"] / (111.32 * math.cos(math.radians(f["lat"]))), f["lat"]))
            body.append(f'<line x1="{x0}" y1="{y0}" x2="{x1}" y2="{y0}" stroke="var(--ink)" stroke-width="3"/><text x="{(x0 + x1) / 2}" y="{y0 - 6}" text-anchor="middle" font-family="var(--font-mono)" font-size="11" fill="var(--ink)">{f["label"]}</text>')
    body.append(f'<text x="{W - 10}" y="{H - 8}" text-anchor="end" font-family="var(--font-sans)" font-size="10" fill="var(--ink-muted)">Mercator · EPSG:4326 · Natural Earth / GSHHG</text>')
    body.append("</svg>")
    return "".join(body)


maps = {
    "atlantic": svg_map((-115, 12), (25, 62), "c", 640, 360, [
        {"type": "gc", "a": (bb[0], bb[1]), "b": MUS},
        {"type": "dot", "lon": bb[0], "lat": bb[1], "color": "var(--amber)", "label": "Big Bend NP, Texas", "dy": -12},
        {"type": "dot", "lon": MUS[0], "lat": MUS[1], "color": "var(--rust)", "label": "Karlsruhe", "dx": -12, "anchor": "end"},
        {"type": "scale", "lon": -108, "lat": 16, "km": 1000, "label": "1 000 km"}]),
    "europe": svg_map((5.6, 46.6), (11.4, 50.6), "h", 640, 480, [
        {"type": "gc", "a": (hw[0], hw[1]), "b": MUS},
        {"type": "city", "lon": 9.18, "lat": 48.78, "label": "Stuttgart"}, {"type": "city", "lon": 7.85, "lat": 47.99, "label": "Freiburg"},
        {"type": "city", "lon": 8.54, "lat": 47.37, "label": "Zürich"}, {"type": "city", "lon": 7.75, "lat": 48.57, "label": "Strasbourg"},
        {"type": "city", "lon": 9.17, "lat": 47.66, "label": "Konstanz"},
        {"type": "dot", "lon": MUS[0], "lat": MUS[1], "color": "var(--rust)", "label": "Naturkundemuseum Karlsruhe", "dy": -12},
        {"type": "dot", "lon": hw[0], "lat": hw[1], "color": "var(--amber)", "label": "Höwenegg (Hegau)", "dy": 22, "dx": -10, "anchor": "end"},
        {"type": "scale", "lon": 5.9, "lat": 46.8, "km": 50, "label": "50 km"}]),
    "_karlsruhe_unused": svg_map((7.9, 48.85), (8.9, 49.2), "f", 640, 300, [
        {"type": "dot", "lon": MUS[0], "lat": MUS[1], "color": "var(--rust)", "label": "Naturkundemuseum · Erbprinzenstraße 13", "dy": -12},
        {"type": "city", "lon": 8.4044, "lat": 49.0094, "label": "Karlsruhe Schloss"}, {"type": "city", "lon": 8.4, "lat": 48.9936, "label": "Hauptbahnhof"},
        {"type": "scale", "lon": 7.95, "lat": 48.87, "km": 10, "label": "10 km"}]),
}
(ROOT / "site/data").mkdir(exist_ok=True)
(ROOT / "site/data/maps.json").write_text(json.dumps(maps, ensure_ascii=False))
print({k: len(v) // 1024 for k, v in maps.items()}, "KB")
