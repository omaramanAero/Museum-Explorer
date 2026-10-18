/* Builds the 12-slide PowerPoint for the HKA AR/VR + GIS assignment. */
const pptxgen = require("pptxgenjs");
const fs = require("fs");
const path = require("path");
const { applyTheme } = require(process.env.PPTX_SKILL + "/scripts/apply_theme.js");

const ROOT = path.resolve(__dirname, "..");
const IMG = (n) => path.join(ROOT, "out/img", n);
const OUTF = path.join(ROOT, "out/Museum_Explorer_Karlsruhe.pptx");
const URLS = JSON.parse(fs.readFileSync(path.join(ROOT, "out/qr/urls.json")));

const THEME = {
  name: "Museum Explorer Karlsruhe",
  headFontFace: "Cambria", bodyFontFace: "Calibri",
  colors: { dk1: "1D1A15", lt1: "FBF8F2", dk2: "2F3B3A", lt2: "E7DCC6", accent1: "B4442A", accent2: "D9A23B", accent3: "5F5747",
            accent4: "8A7360", accent5: "3D4E4C", accent6: "C9BBA3", hlink: "B4442A", folHlink: "8A7360" },
};
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "Museum Explorer Karlsruhe"; pres.author = "HKA AR/VR + GIS project team"; pres.subject = "AR/VR + GIS prototype for the Naturkundemuseum Karlsruhe";
const C = pres.SchemeColor;
const W = 13.33, H = 7.5, M = 0.6;
const T = THEME.colors;

// ---------------------------------------------------------------- layouts
pres.defineSlideMaster({
  title: "TITLE", background: { color: T.dk2 },
  objects: [
    { placeholder: { options: { name: "eyebrow", type: "body", x: M, y: 0.7, w: 7.6, h: 0.4, fontSize: 14, color: T.accent2, bold: true, charSpacing: 3, margin: 0 }, text: "" } },
    { placeholder: { options: { name: "title", type: "title", x: M, y: 1.2, w: 7.6, h: 2.3, fontSize: 54, color: T.lt1, bold: true, valign: "top", align: "left", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: M, y: 3.7, w: 6.3, h: 2.2, fontSize: 18, color: "DCE3DF", valign: "top", margin: 0 }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "CONTENT", background: { color: T.lt1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: M, y: 0.45, w: 12.1, h: 0.9, fontSize: 30, color: T.dk1, bold: true, valign: "middle", align: "left", margin: 0 }, text: "" } },
    { text: { text: "Museum Explorer Karlsruhe · AR/VR + GIS · HKA", options: { x: M, y: 7.02, w: 8, h: 0.3, fontSize: 10, color: T.accent3, margin: 0 } } },
  ],
  slideNumber: { x: 12.3, y: 7.02, w: 0.6, h: 0.3, fontSize: 10, color: T.accent3, align: "right" },
});
pres.defineSlideMaster({
  title: "STATEMENT", background: { color: T.accent1 },
  objects: [
    { placeholder: { options: { name: "eyebrow", type: "body", x: M, y: 0.8, w: 12, h: 0.4, fontSize: 14, color: "F4E3D8", bold: true, charSpacing: 3, margin: 0 }, text: "" } },
    { placeholder: { options: { name: "title", type: "title", x: M, y: 1.4, w: 12.1, h: 3.4, fontSize: 40, color: T.lt1, bold: true, valign: "top", align: "left", margin: 0 }, text: "" } },
  ],
});

// ---------------------------------------------------------------- helpers
const txt = (s, text, o) => s.addText(text, { isTextBox: true, margin: 0, fontSize: 14, color: T.dk1, ...o });
const img = (s, file, o) => s.addImage({ path: IMG(file), ...o });
const fit = (file, w, h) => { // image size fitting a w x h box (inches), keeps aspect
  const sz = require("child_process").execSync(`python3 -c "from PIL import Image; im=Image.open('${IMG(file)}'); print(im.width, im.height)"`).toString().trim().split(" ").map(Number);
  const r = Math.min(w / sz[0], h / sz[1]); return { w: sz[0] * r, h: sz[1] * r };
};
function tile(s, x, y, w, h, label, value, note, opts = {}) {
  const an = opts.anim ? { objectName: opts.anim } : {};
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: opts.fill || T.lt2 }, line: { color: opts.fill || T.lt2 }, rectRadius: 0.08, ...an });
  txt(s, label.toUpperCase(), { x: x + 0.18, y: y + 0.14, w: w - 0.36, h: 0.25, fontSize: 9.5, bold: true, color: opts.muted || T.accent3, charSpacing: 2, ...an });
  txt(s, value, { x: x + 0.18, y: y + 0.4, w: w - 0.36, h: 0.5, fontSize: opts.valueSize || 22, bold: true, color: opts.ink || T.dk1, fontFace: "Courier New", ...an });
  if (note) txt(s, note, { x: x + 0.18, y: y + 0.9, w: w - 0.36, h: h - 1.0, fontSize: 10.5, color: opts.muted || T.accent3, valign: "top", ...an });
}
function numDot(s, x, y, n, d = 0.36, fill = T.accent2, ink = T.dk1, anim) {
  const an = anim ? { objectName: anim } : {};
  s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: fill }, line: { color: fill }, ...an });
  txt(s, String(n), { x, y, w: d, h: d, align: "center", valign: "middle", fontSize: 12, bold: true, color: ink, fontFace: "Courier New", ...an });
}
function card(s, x, y, w, h, fill = T.lt1, line = "D9CFBD", anim) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: fill }, line: { color: line, width: 0.75 }, rectRadius: 0.1, ...(anim ? { objectName: anim } : {}) });
}
const A = (n, eff) => ({ objectName: `anim-${n}${eff ? "-" + eff : ""}` });
function arrow(s, x1, y1, x2, y2, color = T.accent2) {
  s.addShape(pres.shapes.LINE, { x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.abs(x2 - x1) || 0.01, h: Math.abs(y2 - y1) || 0.01, flipH: x2 < x1, flipV: y2 < y1, line: { color, width: 2, endArrowType: "triangle" } });
}
const S = (name, section) => pres.addSlide({ masterName: name, sectionTitle: section });

// ================================================================ 1 TITLE
pres.addSection({ title: "Introduction" });
{
  const s = S("TITLE", "Introduction");
  s.addText("AR/VR + GIS · Hochschule Karlsruhe (HKA)", { placeholder: "eyebrow" });
  s.addText("Museum Explorer Karlsruhe", { placeholder: "title" });
  s.addText("A GIS-based augmented-reality guide for the Staatliches Museum für Naturkunde Karlsruhe. Scan a QR code at the exhibit, turn the 3D model, tap its anatomy, place it in AR and see where it was found.", { placeholder: "body", objectName: "anim-2" });
  txt(s, "Working prototype · 3 exhibits · English / German", { x: M, y: 6.2, w: 7, h: 0.4, fontSize: 13, color: T.accent2, bold: true, objectName: "anim-3" });
  txt(s, "Add the team names here · October 2026", { x: M, y: 6.6, w: 7, h: 0.35, fontSize: 12, color: "B3BDB9" });
  img(s, "quetz_dark.gif", { x: 13.33 - M - 5.6, y: 0.75, w: 5.6, h: 3.5, objectName: "anim-1-zoom" });
  const q = 1.3; img(s, "../qr/qr_EX01.png", { x: W - M - q, y: H - 0.55 - q, w: q, h: q, objectName: "anim-4-flyup" });
  txt(s, "Scan to open the prototype", { x: W - M - 3.4, y: H - 0.55 - q + 0.35, w: 2.0, h: 0.6, fontSize: 11, color: "DCE3DF", align: "right" });
  s.addNotes("Introduce the team. One sentence: we built a working QR-to-3D guide for the State Museum of Natural History Karlsruhe with a GIS database behind it. The QR code on this slide opens the live prototype.");
}

// ================================================================ 2 THE MUSEUM
{
  const s = S("CONTENT", "Introduction");
  s.addText("The museum: Naturkundemuseum Karlsruhe (SMNK)", { placeholder: "title" });
  const f = fit("map_europe.png", 5.6, 4.6);
  img(s, "map_europe.png", { x: W - M - f.w, y: 1.5, w: f.w, h: f.h, ...A(5, "zoom") });
  txt(s, "Location of the museum (red) and the Höwenegg fossil site (amber), rendered from the project GeoPackage.", { x: W - M - f.w, y: 1.5 + f.h + 0.08, w: f.w, h: 0.5, fontSize: 10.5, color: T.accent3, italic: true });
  const x = M, tw = 3.1, th = 1.55, g = 0.2;
  tile(s, x, 1.5, tw, th, "Founded", "1785", "one of Germany's oldest scientifically run natural-history museums", { anim: "anim-1" });
  tile(s, x + tw + g, 1.5, tw, th, "Visitors 2025", "≈250,000", "a new record (museum press release, March 2026)", { anim: "anim-2" });
  tile(s, x, 1.5 + th + g, tw, th, "Address", "Erbprinzenstr. 13", "76133 Karlsruhe · 49.0073° N, 8.4003° E", { valueSize: 18, anim: "anim-3" });
  tile(s, x + tw + g, 1.5 + th + g, tw, th, "At the entrance", "13 m pterosaur", "life-size Quetzalcoatlus model, inspiration for the museum's 2026 mascot", { valueSize: 18, anim: "anim-4" });
  txt(s, [
    { text: "Collections & galleries", options: { bold: true, breakLine: true, fontSize: 14 } },
    { text: "Geology and mineralogy of the Upper Rhine; palaeontology with the famous Höwenegg and Öhningen fossil sites; zoology and entomology; a Vivarium with Germany's largest living coral reef; the ~13 m skeleton of a North Atlantic right whale as the largest object on show.", options: { fontSize: 12.5, color: T.accent3 } },
  ], { x: M, y: 5.1, w: 6.4, h: 1.5, valign: "top", paraSpaceAfter: 4, ...A(6) });
  txt(s, "Sources: smnk.de press release 13 Mar 2026; service-bw museum entry; CETAF member profile.", { x: M, y: 6.65, w: 7, h: 0.3, fontSize: 9, color: T.accent3 });
  s.addNotes("Give the museum context: founded 1785 from the natural-history cabinet of Margravine Caroline Louise; today one of the two state natural-history museums of Baden-Württemberg, about 250,000 visitors in 2025. The Quetzalcoatlus model in front of the entrance is why we chose a pterosaur as the hero exhibit.");
}

// ================================================================ 3 CONCEPT
pres.addSection({ title: "Concept" });
{
  const s = S("STATEMENT", "Concept");
  s.addText("The idea", { placeholder: "eyebrow" });
  s.addText("A museum label gives you a name. A QR code can show you how the animal moved, what each bone did and where it was found.", { placeholder: "title" });
  const steps = [["Scan", "the QR code on the exhibit card – no app to install"], ["Explore", "turn, animate and place the 3D model in AR; tap numbered anatomy"], ["Locate", "see where it stands in the museum and where it was discovered – from GIS data"]];
  steps.forEach(([h, p], i) => {
    const x = M + i * 4.1;
    numDot(s, x, 4.95, i + 1, 0.42, T.accent2, T.dk1, `anim-${i + 1}`);
    txt(s, h, { x: x + 0.55, y: 4.93, w: 3.3, h: 0.45, fontSize: 20, bold: true, color: T.lt1, ...A(i + 1) });
    txt(s, p, { x: x + 0.55, y: 5.4, w: 3.3, h: 0.9, fontSize: 13, color: "F4E3D8", valign: "top", ...A(i + 1) });
  });
  s.addNotes("Problem: static labels, short attention spans, a bilingual audience. Solution: one QR code per exhibit that opens a complete digital guide in the phone browser. Stress: no app install.");
}

// ================================================================ 4 ARCHITECTURE
{
  const s = S("CONTENT", "Concept");
  s.addText("System architecture: from QR code to 3D, AR and GIS", { placeholder: "title" });
  const bx = (x, y, w, h, title, body, fill, ink, sub, an) => {
    card(s, x, y, w, h, fill, fill, an);
    txt(s, title, { x: x + 0.2, y: y + 0.15, w: w - 0.4, h: 0.4, fontSize: 15, bold: true, color: ink, objectName: an });
    if (body) txt(s, body, { x: x + 0.2, y: y + 0.55, w: w - 0.4, h: h - 0.65, fontSize: 11.5, color: sub || ink, valign: "top", objectName: an });
  };
  bx(M, 1.7, 2.5, 1.5, "QR exhibit card", "printed A6 card next to the object; the code holds only the page address + exhibit ID", T.lt2, T.dk1, T.accent3, "anim-1");
  bx(M + 3.1, 1.7, 2.5, 1.5, "Phone browser", "camera scan opens the link; works on Android and iPhone, no app install", T.lt2, T.dk1, T.accent3, "anim-2");
  bx(M + 6.2, 1.7, 6.0, 2.55, "Exhibit page (web app)", "", T.dk2, T.lt1, null, "anim-3");
  const feats = [["3D viewer", "turn, zoom, animate"], ["AR", "WebXR · Scene Viewer · Quick Look"], ["Anatomy", "numbered hotspots + sheet"], ["Maps", "museum position · find site"]];
  feats.forEach(([h, p], i) => {
    const fx = M + 6.2 + 0.2 + (i % 2) * 2.85, fy = 2.3 + Math.floor(i / 2) * 0.9;
    card(s, fx, fy, 2.65, 0.75, "3D4E4C", "3D4E4C", `anim-${4 + i}`);
    txt(s, h, { x: fx + 0.15, y: fy + 0.08, w: 2.4, h: 0.3, fontSize: 12.5, bold: true, color: T.accent2, ...A(4 + i) });
    txt(s, p, { x: fx + 0.15, y: fy + 0.38, w: 2.4, h: 0.3, fontSize: 10.5, color: "DCE3DF", ...A(4 + i) });
  });
  arrow(s, M + 2.5, 2.45, M + 3.1, 2.45); arrow(s, M + 5.6, 2.45, M + 6.2, 2.45);
  // data layer
  bx(M, 4.8, 3.6, 1.7, "QGIS · GeoPackage", "museum_gis.gpkg: museum, exhibits, discovery_sites, find_to_museum_lines, exhibit_parts (EPSG:4326)", "E7DCC6", T.dk1, T.accent3, "anim-8");
  bx(M + 4.2, 4.8, 3.6, 1.7, "Build scripts (Python)", "export exhibits.json + GeoJSON, great-circle distances, SVG maps, hotspot anchors", "E7DCC6", T.dk1, T.accent3, "anim-9");
  bx(M + 8.4, 4.8, 3.8, 1.7, "3D models (Blender → glTF)", "rigged pterosaur with Flap/Glide animations; horse skeleton; whale skeleton", "E7DCC6", T.dk1, T.accent3, "anim-10");
  arrow(s, M + 3.6, 5.65, M + 4.2, 5.65); arrow(s, M + 7.8, 5.65, M + 8.4, 5.65);
  arrow(s, M + 6.0, 4.8, M + 7.6, 4.25); arrow(s, M + 10.3, 4.8, M + 10.3, 4.25);
  txt(s, "One spatial record per exhibit feeds the text, the maps and the 3D anchor points – the GIS database is the single source of truth.", { x: M, y: 6.6, w: 12, h: 0.35, fontSize: 12, italic: true, color: T.accent3 });
  s.addNotes("Walk left to right. The QR code encodes a page address, not the model, so content can change without reprinting. The data layer is the GIS link: the same GeoPackage records drive both the QGIS maps and the web pages.");
}

// ================================================================ 5 EXHIBITS
pres.addSection({ title: "Exhibits" });
{
  const s = S("CONTENT", "Exhibits");
  s.addText("Three real exhibits of the museum, as moving 3D models", { placeholder: "title" });
  const cols = [
    ["clip_quetz.gif", "EX01 · Hero", "Quetzalcoatlus northropi", "Giant pterosaur · Late Cretaceous, ~68 Ma", "Found 1971, Big Bend National Park, Texas", "Real object: life-size standing model at the main entrance", "Flying, animated model · 7 anatomy parts"],
    ["clip_horse.gif", "EX02", "Hippotherium primigenium", "Three-toed horse · Late Miocene, 10.3 Ma", "Höwenegg volcano lake, Hegau (124 km away)", "Real object: mounted skeletons in the geology galleries", "Mounted skeleton model · 6 anatomy parts"],
    ["clip_whale.gif", "EX03", "Eubalaena glacialis", "North Atlantic right whale · living species, critically endangered", "Specimen origin not verified – not mapped", "Real object: ~13 m skeleton, the museum's largest exhibit", "Skeleton model · 6 anatomy parts"],
  ];
  const cw = 3.9, gap = 0.2;
  cols.forEach(([clip, id, sci, line1, line2, line3, line4], i) => {
    const x = M + i * (cw + gap), y = 1.5, h = 5.0, an = `anim-${i + 1}`;
    card(s, x, y, cw, h, T.lt1, i === 0 ? T.accent1 : "D9CFBD", an);
    const f = fit(clip, cw - 0.3, 2.0);
    img(s, clip, { x: x + (cw - f.w) / 2, y: y + 0.15 + (2.0 - f.h) / 2, w: f.w, h: f.h, objectName: an });
    txt(s, id.toUpperCase(), { x: x + 0.25, y: y + 2.3, w: cw - 0.5, h: 0.3, fontSize: 10, bold: true, color: T.accent1, charSpacing: 2, objectName: an });
    txt(s, sci, { x: x + 0.25, y: y + 2.58, w: cw - 0.5, h: 0.45, fontSize: 18, bold: true, italic: true, color: T.dk1, fontFace: "Cambria", objectName: an });
    txt(s, [{ text: line1, options: { breakLine: true } }, { text: line2, options: { breakLine: true } }, { text: line3, options: { bold: true, color: T.dk1 } }], { x: x + 0.25, y: y + 3.05, w: cw - 0.5, h: 1.45, fontSize: 11.5, color: T.accent3, valign: "top", paraSpaceAfter: 4, objectName: an });
    txt(s, line4, { x: x + 0.25, y: y + 4.5, w: cw - 0.5, h: 0.4, fontSize: 11.5, bold: true, color: T.accent1, objectName: an });
  });
  txt(s, "Each model is a simplified reconstruction of the museum's own object, and it is the same model the visitor gets after scanning the QR code. The clips play by themselves in the slide show.", { x: M, y: 6.6, w: 12.1, h: 0.4, fontSize: 11.5, italic: true, color: T.accent3, ...A(4) });
  s.addNotes("The museum has no famous dinosaur skeleton on display, so the hero is its signature pterosaur – a flying reptile, not a dinosaur. Each card names the real object in the museum so nobody confuses the simplified 3D model with the exhibit. All three are real SMNK objects, and the QR code opens exactly these models.");
}

// ================================================================ 6 HERO MODEL
{
  const s = S("CONTENT", "Exhibits");
  s.addText("Hero exhibit: Quetzalcoatlus northropi in 3D", { placeholder: "title" });
  const f = { w: 7.1, h: 7.1 * 9 / 16 };
  img(s, "clip_quetz.gif", { x: M, y: 1.5, w: f.w, h: f.h, ...A(1, "zoom") });
  const f2 = fit("q_top.png", 2.4, 1.4);
  img(s, "q_top.png", { x: M + 4.7, y: 5.45, w: f2.w, h: f2.h, ...A(2) });
  txt(s, "The Flap animation of the rigged model (plays by itself in the slide show) and the planform seen from above. Wingspan 10 m in the model.", { x: M, y: 5.6, w: 4.4, h: 1.0, fontSize: 10.5, italic: true, color: T.accent3, ...A(2) });
  const tx = 8.1, tw = 2.3, th = 1.3, g = 0.2;
  tile(s, tx, 1.5, tw, th, "Age", "~68 Ma", "Maastrichtian, Late Cretaceous", { anim: "anim-3" });
  tile(s, tx + tw + g, 1.5, tw, th, "Wingspan", "10–11 m", "estimate; among the largest flyers ever", { anim: "anim-4" });
  tile(s, tx, 1.5 + th + g, tw, th, "Found", "1971", "Big Bend NP, Texas (D. Lawson)", { anim: "anim-5" });
  tile(s, tx + tw + g, 1.5 + th + g, tw, th, "In the museum", "Entrance", "life-size standing model outdoors", { anim: "anim-6" });
  txt(s, [
    { text: "How the model was made", options: { bold: true, fontSize: 14, breakLine: true } },
    { text: "Built in Blender from a skeleton of 42 joints with the skin modifier, subdivision and procedural displacement", options: { bullet: true, breakLine: true } },
    { text: "Rigged with 29 bones; two glTF animations – Flap (1.3 s) and Glide (6 s)", options: { bullet: true, breakLine: true } },
    { text: "Vertex-coloured skin and fibre-striped wing membranes; 48,800 triangles, 1.8 MB, validated with the Khronos glTF validator", options: { bullet: true, breakLine: true } },
    { text: "A reconstruction, not a scan: only fragments of Q. northropi exist, so the head crest follows its smaller relative Q. lawsoni", options: { bullet: true } },
  ], { x: tx, y: 4.6, w: 4.8, h: 2.3, fontSize: 11.5, color: T.dk1, valign: "top", paraSpaceAfter: 4, ...A(7) });
  s.addNotes("The 3D model is our own rigged reconstruction built in Blender and exported as glTF, so there are no licence issues. Wingspan is an estimate and is shown as a range. The Flap animation moves the whole skinned mesh, membranes included. In the museum the visitor sees the standing model; in the app the same animal flies.");
}

// ================================================================ 7 ANATOMY
{
  const s = S("CONTENT", "Exhibits");
  s.addText("Anatomy mode: tap a bone, learn what it did", { placeholder: "title" });
  const f = fit("p_ex1_anat.png", 3.0, 5.4);
  img(s, "p_ex1_anat.png", { x: M + 0.2, y: 1.5, w: f.w, h: f.h, ...A(1, "flyup") });
  const f2 = fit("d_ex1_anat.png", 5.1, 3.2);
  img(s, "d_ex1_anat.png", { x: M + 3.6, y: 1.5, w: f2.w, h: f2.h, ...A(2) });
  txt(s, "Anatomy mode pauses the animation and shows numbered hotspots anchored to the mesh. A tap flies the camera to the part and opens a sheet with name, scientific term, description and function – in English or German.", { x: M + 3.6, y: 1.55 + f2.h + 0.1, w: 5.0, h: 1.0, fontSize: 11.5, color: T.accent3, valign: "top" });
  const parts = ["Head crest", "Toothless beak", "Long neck", "Pteroid bone", "Wing finger (digit IV)", "Wing membrane", "Hind limb"];
  txt(s, "7 parts on the pterosaur", { x: 9.2, y: 1.5, w: 3.6, h: 0.4, fontSize: 14, bold: true });
  parts.forEach((p, i) => { numDot(s, 9.2, 2.0 + i * 0.52, i + 1, 0.34, T.accent2, T.dk1, `anim-${3 + i}`); txt(s, p, { x: 9.65, y: 2.0 + i * 0.52, w: 3.2, h: 0.34, fontSize: 13, valign: "middle", ...A(3 + i) }); });
  txt(s, "19 parts across the three exhibits; anchor points are stored in the GeoPackage table exhibit_parts (model x/y/z).", { x: 9.2, y: 5.75, w: 3.6, h: 0.9, fontSize: 11, color: T.accent3, valign: "top" });
  s.addNotes("Demo this live if possible. The hotspot positions come from the same script that builds the model, so they always sit on the right bone. Dots and sheet share the same number so visitors can match them.");
}

// ================================================================ 8 GIS
pres.addSection({ title: "GIS" });
{
  const s = S("CONTENT", "GIS");
  s.addText("GIS integration: one GeoPackage drives every page", { placeholder: "title" });
  const f = fit("map_qgis_layout.png", 8.1, 4.6);
  img(s, "map_qgis_layout.png", { x: M, y: 1.5, w: f.w, h: f.h, ...A(1, "zoom") });
  txt(s, "Print layout rendered from museum_gis.gpkg: discovery sites, museum, great-circle lines, legend, scale bar, attribute table.", { x: M, y: 1.55 + f.h, w: f.w, h: 0.5, fontSize: 10.5, italic: true, color: T.accent3 });
  const rows = [
    [{ text: "Layer", options: { bold: true, color: T.lt1, fill: { color: T.dk2 } } }, { text: "Type", options: { bold: true, color: T.lt1, fill: { color: T.dk2 } } }, { text: "Content", options: { bold: true, color: T.lt1, fill: { color: T.dk2 } } }],
    ["museum", "Point", "SMNK building, 49.0073 N 8.4003 E"],
    ["exhibits", "Point", "ID, QR code, names EN/DE, era, zone, verified flag, page URL, sources"],
    ["discovery_sites", "Point", "Big Bend NP (park level), Höwenegg (summit); distance to museum"],
    ["find_to_museum_lines", "Line", "find site → museum"],
    ["exhibit_parts", "Table", "19 anatomy parts with 3D anchor x/y/z"],
  ];
  s.addTable(rows, { x: 9.0, y: 1.5, w: 3.75, colW: [1.35, 0.6, 1.8], fontSize: 9.5, color: T.dk1, border: { type: "solid", color: "D9CFBD", pt: 0.5 }, fill: { color: T.lt1 }, valign: "middle", margin: 0.05 });
  txt(s, [
    { text: "CRS EPSG:4326 · distances by haversine great circle", options: { breakLine: true } },
    { text: "Big Bend NP → Karlsruhe: 8,999 km", options: { bold: true, breakLine: true } },
    { text: "Höwenegg → Karlsruhe: 124 km", options: { bold: true, breakLine: true } },
    { text: "Indoor exhibit positions carry verified = 0 and are flagged “Illustrative” in the app until checked against the official floor plan.", options: {} },
  ], { x: 9.0, y: 5.0, w: 3.75, h: 1.9, fontSize: 11, color: T.dk1, valign: "top", paraSpaceAfter: 4, ...A(2) });
  s.addNotes("Open the GeoPackage in QGIS during the talk if there is time: drag museum_gis.gpkg into QGIS and add all layers. Explain the verified flag: honest data – indoor positions are illustrative until the museum confirms them.");
}

// ================================================================ 9 GEOPACKAGE -> PAGE
{
  const s = S("CONTENT", "GIS");
  s.addText("From the GeoPackage to the visitor's phone", { placeholder: "title" });
  const f = fit("d_ex1_maps.png", 6.4, 3.2);
  img(s, "d_ex1_maps.png", { x: M, y: 1.5, w: f.w, h: f.h, ...A(1, "zoom") });
  txt(s, "The maps section of the Quetzalcoatlus page: museum floor plan (left) and the find site with the great-circle line to Karlsruhe (right), both generated from the GeoPackage.", { x: M, y: 1.55 + f.h, w: f.w, h: 0.6, fontSize: 10.5, italic: true, color: T.accent3 });
  const steps = [
    ["1", "Edit in QGIS", "exhibit attributes and positions live in museum_gis.gpkg"],
    ["2", "Export", "build_data.py writes exhibits.json and exhibits.geojson; build_maps.py renders the maps"],
    ["3", "Render", "the web page reads one record per exhibit: facts, maps, anatomy anchors"],
    ["4", "Verify", "verified = 0 → the page shows the amber “Illustrative” tag automatically"],
  ];
  steps.forEach(([n, h, p], i) => {
    const y = 1.5 + i * 1.25;
    numDot(s, 8.1, y + 0.05, n, 0.4, T.accent2, T.dk1, `anim-${2 + i}`);
    txt(s, h, { x: 8.65, y, w: 4.1, h: 0.4, fontSize: 15, bold: true, ...A(2 + i) });
    txt(s, p, { x: 8.65, y: y + 0.42, w: 4.1, h: 0.7, fontSize: 11.5, color: T.accent3, valign: "top", ...A(2 + i) });
  });
  const f2 = fit("map_europe.png", 2.0, 1.4);
  img(s, "map_europe.png", { x: M, y: 5.45, w: f2.w, h: f2.h });
  txt(s, "Regional map (Höwenegg → Karlsruhe, 124 km) used on the three-toed-horse page.", { x: M + f2.w + 0.2, y: 5.5, w: 4.1, h: 1.0, fontSize: 10.5, color: T.accent3, valign: "top" });
  s.addNotes("This is the GIS integration in practice: the same record edited in QGIS ends up as the map, the facts and the anatomy anchors on the phone. Nothing is typed twice.");
}

// ================================================================ 10 PROTOTYPE
pres.addSection({ title: "Prototype" });
{
  const s = S("CONTENT", "Prototype");
  s.addText("The prototype: a web app, English and German, no install", { placeholder: "title" });
  const shots = ["p_home.png", "p_ex1.png", "p_ex1_de2.png"];
  shots.forEach((f, i) => { const z = fit(f, 2.45, 5.3); img(s, f, { x: M + i * 2.65, y: 1.5, w: z.w, h: z.h, ...A(i + 1, "flyup") }); });
  txt(s, "Home · exhibit page · German version", { x: M, y: 6.85, w: 7.8, h: 0.3, fontSize: 10.5, italic: true, color: T.accent3 });
  const stack = [
    ["3D + AR", "Google model-viewer 4.0 (WebGL); AR via WebXR on Android, Scene Viewer, AR Quick Look on iPhone"],
    ["Models", "Blender → glTF 2.0 binaries, rigged and animated; vertex colours, no textures to download"],
    ["Data", "QGIS GeoPackage → JSON/GeoJSON → inline SVG maps (Mercator, EPSG:4326)"],
    ["App", "Single static page, hash routes #EX01…#EX03, light/dark theme, EN/DE toggle"],
    ["Hosting", "Published as a shareable web page; QR codes point to page#EX01. Deployable to any https host (e.g. GitHub Pages)"],
  ];
  stack.forEach(([h, p], i) => {
    const y = 1.5 + i * 1.05;
    card(s, 8.7, y, 4.05, 0.92, T.lt2, T.lt2, `anim-${4 + i}`);
    txt(s, h, { x: 8.9, y: y + 0.1, w: 3.7, h: 0.3, fontSize: 12.5, bold: true, color: T.accent1, ...A(4 + i) });
    txt(s, p, { x: 8.9, y: y + 0.4, w: 3.7, h: 0.5, fontSize: 10, color: T.dk1, valign: "top", ...A(4 + i) });
  });
  s.addNotes("Everything is a static website: cheap to run and easy to hand over to the museum. The language toggle re-renders every string; the choice is remembered on the phone.");
}

// ================================================================ 11 SCAN & TRY
{
  const s = S("CONTENT", "Prototype");
  s.addText("Try it now: scan with your phone", { placeholder: "title" });
  const big = 3.6;
  card(s, M, 1.5, big + 0.5, big + 1.15, "FFFFFF", "D9CFBD");
  img(s, "../qr/qr_EX01.png", { x: M + 0.25, y: 1.75, w: big, h: big, ...A(1, "zoom") });
  txt(s, "EX01 · Quetzalcoatlus", { x: M, y: 1.75 + big + 0.1, w: big + 0.5, h: 0.4, fontSize: 14, bold: true, align: "center" });
  txt(s, "animated 3D model · 7 anatomy parts · AR", { x: M, y: 1.75 + big + 0.5, w: big + 0.5, h: 0.3, fontSize: 10.5, align: "center", color: T.accent3 });
  const sm = 1.75;
  [["qr_EX02.png", "EX02 · Three-toed horse"], ["qr_EX03.png", "EX03 · Right whale"]].forEach(([f, l], i) => {
    const x = M + big + 0.8 + i * (sm + 0.55);
    card(s, x, 1.5, sm + 0.5, sm + 0.9, "FFFFFF", "D9CFBD");
    img(s, "../qr/" + f, { x: x + 0.25, y: 1.7, w: sm, h: sm });
    txt(s, l, { x: x, y: 1.7 + sm + 0.1, w: sm + 0.5, h: 0.55, fontSize: 10.5, bold: true, align: "center" });
  });
  txt(s, [
    { text: "What happens", options: { bold: true, fontSize: 14, breakLine: true } },
    { text: "The camera reads the link and opens the exhibit page in the browser.", options: { bullet: true, breakLine: true } },
    { text: "Turn and zoom the model; switch Flap / Glide; tap Anatomy and the numbered dots.", options: { bullet: true, breakLine: true } },
    { text: "Tap “View in AR” to place the model in your room at life size (Android with ARCore, iPhone/iPad).", options: { bullet: true, breakLine: true } },
    { text: "Switch EN / DE at the top right.", options: { bullet: true } },
  ], { x: M + big + 0.8, y: 4.4, w: 4.9, h: 2.4, fontSize: 12, color: T.dk1, valign: "top", paraSpaceAfter: 4, ...A(2) });
  card(s, 10.0, 1.5, 2.75, 5.2, T.dk2, T.dk2, "anim-3");
  txt(s, "LINK", { x: 10.2, y: 1.65, w: 2.4, h: 0.3, fontSize: 10, bold: true, color: T.accent2, charSpacing: 2 });
  txt(s, URLS.home, { x: 10.2, y: 1.95, w: 2.4, h: 1.3, fontSize: 10.5, color: T.lt1, fontFace: "Courier New", valign: "top" });
  txt(s, "Add #EX01, #EX02 or #EX03 to open an exhibit directly.", { x: 10.2, y: 3.3, w: 2.4, h: 0.7, fontSize: 11, color: "DCE3DF", valign: "top" });
  txt(s, "Printed A6 exhibit cards with these codes are in the project files (cards.html).", { x: 10.2, y: 4.1, w: 2.4, h: 0.9, fontSize: 11, color: "DCE3DF", valign: "top" });
  txt(s, "AR note: the model appears in the camera view but is not locked to the physical exhibit; indoors, pinch to shrink it.", { x: 10.2, y: 5.2, w: 2.4, h: 1.4, fontSize: 10.5, color: T.accent2, valign: "top" });
  s.addNotes("Let the audience scan the big code. Pre-open the page on your own phone in case scanning is slow. Have AR permission already granted. Keep the live demo under three minutes.");
}

// ================================================================ 12 LIMITS, NEXT, THANKS
pres.addSection({ title: "Conclusion" });
{
  const s = S("CONTENT", "Conclusion");
  s.addText("Data honesty, limitations and next steps", { placeholder: "title" });
  let colN = 0;
  const col = (x, title, items, fill, ink, sub) => {
    colN += 1; const an = `anim-${colN}`;
    card(s, x, 1.5, 3.9, 3.9, fill, fill === T.lt1 ? "D9CFBD" : fill, an);
    txt(s, title, { x: x + 0.25, y: 1.65, w: 3.4, h: 0.4, fontSize: 15, bold: true, color: ink, objectName: an });
    txt(s, items.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < items.length - 1 } })), { x: x + 0.25, y: 2.1, w: 3.45, h: 3.2, fontSize: 11.5, color: sub, valign: "top", paraSpaceAfter: 5, objectName: an });
  };
  col(M, "Verified", ["Museum location and the entrance model (SMNK press release)", "Scientific facts, with sources listed on every page", "Höwenegg site coordinates (summit point)", "Great-circle distances computed from the GeoPackage"], T.lt1, T.dk1, T.accent3);
  col(M + 4.1, "Illustrative (tagged in the app)", ["Indoor gallery positions and the floor-plan sketch – no official plan was available", "All 3D models are reconstructions, not scans", "The Q. northropi crest follows Q. lawsoni", "Whale find site unknown – deliberately not mapped"], "FBF0D9", T.dk1, T.accent3);
  col(M + 8.2, "Limitations", ["AR places the model in the camera view; it is not anchored to the real object", "iPhone AR Quick Look shows the model without animation", "Web page needs internet; the maps themselves are embedded and work offline", "Prototype, not an official SMNK service"], T.dk2, T.lt1, "DCE3DF");
  txt(s, [
    { text: "Next steps: ", options: { bold: true } },
    { text: "official floor plan with verified exhibit points · image-target AR anchoring on the exhibit · photogrammetry scans of the real specimens with museum permission · visitor test with a short survey." },
  ], { x: M, y: 5.65, w: 12.1, h: 0.6, fontSize: 12.5, color: T.dk1, valign: "top", ...A(4) });
  txt(s, "Danke · Thank you", { x: M, y: 6.3, w: 6, h: 0.6, fontSize: 28, bold: true, color: T.accent1, fontFace: "Cambria", ...A(5, "zoom") });
  const q = 0.9; img(s, "../qr/qr_home.png", { x: W - M - q, y: 6.15, w: q, h: q });
  txt(s, "Questions? Scan to explore the prototype", { x: W - M - q - 3.2, y: 6.45, w: 3.1, h: 0.35, fontSize: 11, color: T.accent3, align: "right" });
  s.addNotes("Close with the honest picture: what is verified, what is illustrative and what the prototype cannot do yet. Then the concrete next steps. Leave the QR code on screen for questions.");
}

(async () => {
  await pres.writeFile({ fileName: OUTF });
  await applyTheme(OUTF, THEME);
  console.log("wrote", OUTF);
})();
