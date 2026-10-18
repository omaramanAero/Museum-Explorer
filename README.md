# Museum Explorer Karlsruhe — project files

AR/VR + GIS assignment, Hochschule Karlsruhe. A QR-to-3D exhibit guide for the Staatliches Museum für Naturkunde Karlsruhe (SMNK).

## What is in this folder

| File / folder | What it is |
|---|---|
| `Museum_Explorer_Karlsruhe.pptx` | The 12-slide presentation (PowerPoint, 16:9) with slide transitions, automatic fade-in builds and embedded clips of the three moving 3D models. Speaker notes on every slide. Play it in Slide Show mode (F5) to see the animations. |
| `clips/` | The model clips (MP4): pterosaur flapping, horse skeleton and whale skeleton turning. |
| `QR_exhibit_cards_A6.pdf` | The three printable A6 exhibit cards with working QR codes (print at 100 %, no margins). |
| `qr/` | The QR codes as PNG (`qr_EX01.png` … , `qr_home.png`) and the links they encode (`urls.json`). |
| `site/` | The complete prototype web app (`index.html` + `models/` + `vendor/`). Works on any https web host. `cards.html` regenerates the cards for a new address. |
| `artifact/` | The same app as published on claude.ai (binaries renamed `.wasm` for that host). |
| `gis/museum_gis.gpkg` | The QGIS GeoPackage: layers `museum`, `exhibits`, `discovery_sites`, `find_to_museum_lines`, table `exhibit_parts` (EPSG:4326). CSV copies next to it. |
| `maps/` | The rendered maps (Atlantic, Baden-Württemberg, QGIS-style print layout). |
| `renders/` | Renders of the three 3D models (transparent PNG). |
| `models/` | The glTF models: `quetzalcoatlus.glb` (rigged, Flap + Glide animations), `hippotherium_skeleton.glb` (mounted three-toed horse), `nordkaper_skeleton.glb`, plus `quetzalcoatlus.blend`. These are the same models the visitor sees after scanning. |
| `tools/` | The build scripts (Blender model builder, GeoPackage export, map renderer, site builder, PowerPoint builder). |

## The live prototype

The QR codes open `https://claude.ai/artifact/DsgFoU4sneqqty2qjDDPUW` (`#EX01`, `#EX02`, `#EX03` open an exhibit directly). It is a private page until it is shared: open it once, use **Share → anyone with the link**, and the codes work for everyone.

To host it anywhere else (for example GitHub Pages), upload the contents of `site/`, then open `cards.html` on that address to print new cards.

## Data honesty

Verified from sources: museum location, the entrance model, the scientific facts (sources on every page), the Höwenegg coordinates and the computed distances. Marked **Illustrative** in the app: indoor gallery positions and the floor-plan sketch, and all 3D models (own reconstructions, not scans). The whale's find site is unknown and deliberately not mapped.

## Rebuilding (optional)

```
tools/bl_quetz.py        # Blender (bpy 4.2): builds and exports the pterosaur, then tools/fix_quat.py
tools/build_horse.py     # the mounted horse skeleton
tools/build_models.py    # the whale skeleton
tools/bl_video.py        # the model clips for the slides
tools/animate_pptx.py    # adds transitions, builds and video autoplay to the deck
tools/build_data.py      # GeoPackage + exhibits.json/.geojson
tools/build_maps.py      # maps (geopandas + basemap)
tools/build_site.py      # site/index.html and artifact/index.html
tools/build_pptx.js      # the PowerPoint (pptxgenjs)
```
