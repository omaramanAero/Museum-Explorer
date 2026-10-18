"""Merges content + model hotspots into the site data, and writes the GIS package.

Outputs
  site/data/exhibits.json      everything the web app needs (bilingual)
  site/data/exhibits.geojson   exhibit + discovery-site points (EPSG:4326) for the web maps
  gis/museum_gis.gpkg          GeoPackage for QGIS: layers museum, exhibits, discovery_sites, exhibit_parts (table)
  gis/*.csv                    the same tables as CSV
"""
import json, math
from pathlib import Path
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, LineString

ROOT = Path(__file__).resolve().parent.parent
content = json.loads((ROOT / "tools/content.json").read_text())
hot = json.loads((ROOT / "site/models/hotspots.json").read_text())


def haversine_km(a, b):
    R = 6371.0
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


M = content["museum"]
for ex in content["exhibits"]:
    pos = {h["id"]: h for h in hot[ex["id"]]}
    for i, p in enumerate(ex["parts"], 1):
        h = pos[p["id"]]
        p["n"] = i
        p["position"] = h["pos"]
        p["normal"] = h["normal"]
    if ex.get("found"):
        ex["found"]["distanceKm"] = round(haversine_km((ex["found"]["lat"], ex["found"]["lon"]), (M["lat"], M["lon"])))

(ROOT / "site/data").mkdir(parents=True, exist_ok=True)
(ROOT / "site/data/exhibits.json").write_text(json.dumps(content, ensure_ascii=False, indent=1))

# ------------------------------------------------------------------ GIS layers
museum = gpd.GeoDataFrame([{"name": M["name"]["de"], "name_en": M["name"]["en"], "address": M["address"],
                            "source": M["coordSource"]}], geometry=[Point(M["lon"], M["lat"])], crs="EPSG:4326")

rows, geoms = [], []
for ex in content["exhibits"]:
    im = ex["inMuseum"]
    rows.append({
        "exhibit_id": ex["id"], "qr_code": ex["id"], "name": ex["name"]["en"], "name_de": ex["name"]["de"],
        "scientific_name": ex["sci"], "category": ex["eyebrow"]["en"], "era": ex["era"]["en"],
        "location_kind": im["kind"], "zone": im.get("zone", "entrance"),
        "position_verified": int(im["verified"]), "position_note": im["precision"]["en"],
        "description": ex["story"]["en"][0], "model_url": ex["model"],
        "page_url": f"exhibit/{ex['id']}/",
        "source": "; ".join(s["url"] for s in ex["sources"]),
    })
    geoms.append(Point(im["lon"], im["lat"]))
exhibits = gpd.GeoDataFrame(rows, geometry=geoms, crs="EPSG:4326")

srows, sgeoms, links, lgeoms = [], [], [], []
for ex in content["exhibits"]:
    f = ex.get("found")
    if not f:
        continue
    srows.append({"exhibit_id": ex["id"], "place": f["place"]["en"], "place_de": f["place"]["de"],
                  "precision": f["precision"]["en"], "distance_to_museum_km": f["distanceKm"]})
    sgeoms.append(Point(f["lon"], f["lat"]))
    links.append({"exhibit_id": ex["id"], "distance_km": f["distanceKm"]})
    lgeoms.append(LineString([(f["lon"], f["lat"]), (M["lon"], M["lat"])]))
sites = gpd.GeoDataFrame(srows, geometry=sgeoms, crs="EPSG:4326")
journeys = gpd.GeoDataFrame(links, geometry=lgeoms, crs="EPSG:4326")

parts = pd.DataFrame([{"exhibit_id": ex["id"], "part_no": p["n"], "part_id": p["id"],
                       "name": p["name"]["en"], "name_de": p["name"]["de"], "term": p["term"]["en"],
                       "function": p["fn"]["en"],
                       "model_x": p["position"][0], "model_y": p["position"][1], "model_z": p["position"][2]}
                      for ex in content["exhibits"] for p in ex["parts"]])

gis = ROOT / "gis"; gis.mkdir(exist_ok=True)
gpkg = gis / "museum_gis.gpkg"
if gpkg.exists():
    gpkg.unlink()
museum.to_file(gpkg, layer="museum", driver="GPKG")
exhibits.to_file(gpkg, layer="exhibits", driver="GPKG")
sites.to_file(gpkg, layer="discovery_sites", driver="GPKG")
journeys.to_file(gpkg, layer="find_to_museum_lines", driver="GPKG")
import pyogrio
pyogrio.write_dataframe(parts, gpkg, layer="exhibit_parts", driver="GPKG")
exhibits.drop(columns="geometry").assign(lon=exhibits.geometry.x, lat=exhibits.geometry.y).to_csv(gis / "exhibits.csv", index=False)
sites.drop(columns="geometry").assign(lon=sites.geometry.x, lat=sites.geometry.y).to_csv(gis / "discovery_sites.csv", index=False)
parts.to_csv(gis / "exhibit_parts.csv", index=False)

# web GeoJSON (one collection, `layer` property)
fc = {"type": "FeatureCollection", "features": []}
fc["features"].append({"type": "Feature", "properties": {"layer": "museum", "name": M["name"]["en"]},
                       "geometry": {"type": "Point", "coordinates": [M["lon"], M["lat"]]}})
for ex in content["exhibits"]:
    if ex.get("found"):
        fc["features"].append({"type": "Feature", "properties": {"layer": "discovery_site", "exhibit_id": ex["id"],
                               "name": ex["name"]["en"], "name_de": ex["name"]["de"], "place": ex["found"]["place"]["en"],
                               "distance_km": ex["found"]["distanceKm"]},
                               "geometry": {"type": "Point", "coordinates": [ex["found"]["lon"], ex["found"]["lat"]]}})
(ROOT / "site/data/exhibits.geojson").write_text(json.dumps(fc, ensure_ascii=False, indent=1))
print("exhibits", len(exhibits), "sites", len(sites), "parts", len(parts))
print({ex["id"]: ex.get("found", {}) and ex["found"]["distanceKm"] for ex in content["exhibits"]})
