"""Adds slide transitions and entrance animations to a pptxgenjs deck.

Shapes whose name is  anim-<order>[-<effect>]  (set via pptxgenjs objectName) are animated in <order>,
automatically after the slide appears (no clicks needed). effect: fade (default) | flyup | zoom.
Slide transitions come from the TRANSITIONS map (slide number -> xml), default fade.
usage: animate_pptx.py in.pptx out.pptx
"""
import re, sys, zipfile, shutil, os
from defusedxml import minidom

src, dst = sys.argv[1], sys.argv[2]
TRANSITIONS = {
    1: '<p:transition spd="slow"><p:fade/></p:transition>',
    3: '<p:transition spd="med"><p:push dir="l"/></p:transition>',
    5: '<p:transition spd="med"><p:push dir="l"/></p:transition>',
    8: '<p:transition spd="med"><p:push dir="l"/></p:transition>',
    10: '<p:transition spd="med"><p:push dir="l"/></p:transition>',
    12: '<p:transition spd="slow"><p:fade/></p:transition>',
}
DEFAULT_TRANSITION = '<p:transition spd="med"><p:fade/></p:transition>'


class Ids:
    def __init__(self): self.n = 0
    def next(self): self.n += 1; return self.n


def effect_xml(ids, spid, delay, effect, first):
    node_type = "afterEffect" if first else "withEffect"
    set_vis = (f'<p:set><p:cBhvr><p:cTn id="{ids.next()}" dur="1" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst></p:cTn>'
               f'<p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl><p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst></p:cBhvr>'
               f'<p:to><p:strVal val="visible"/></p:to></p:set>')
    if effect == "flyup":   # Fly In from bottom (preset 2 / subtype 4)
        preset = 'presetID="2" presetClass="entr" presetSubtype="4"'
        body = (set_vis +
                f'<p:anim calcmode="lin" valueType="num"><p:cBhvr additive="base"><p:cTn id="{ids.next()}" dur="600" fill="hold"/><p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl>'
                f'<p:attrNameLst><p:attrName>ppt_x</p:attrName></p:attrNameLst></p:cBhvr><p:tavLst><p:tav tm="0"><p:val><p:strVal val="#ppt_x"/></p:val></p:tav>'
                f'<p:tav tm="100000"><p:val><p:strVal val="#ppt_x"/></p:val></p:tav></p:tavLst></p:anim>'
                f'<p:anim calcmode="lin" valueType="num"><p:cBhvr additive="base"><p:cTn id="{ids.next()}" dur="600" fill="hold"/><p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl>'
                f'<p:attrNameLst><p:attrName>ppt_y</p:attrName></p:attrNameLst></p:cBhvr><p:tavLst><p:tav tm="0"><p:val><p:strVal val="1+#ppt_h/2"/></p:val></p:tav>'
                f'<p:tav tm="100000"><p:val><p:strVal val="#ppt_y"/></p:val></p:tav></p:tavLst></p:anim>')
    elif effect == "zoom":  # Zoom in (preset 23 / subtype 16)
        preset = 'presetID="23" presetClass="entr" presetSubtype="16"'
        body = (set_vis +
                f'<p:anim calcmode="lin" valueType="num"><p:cBhvr><p:cTn id="{ids.next()}" dur="500" fill="hold"/><p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl>'
                f'<p:attrNameLst><p:attrName>ppt_w</p:attrName></p:attrNameLst></p:cBhvr><p:tavLst><p:tav tm="0"><p:val><p:fltVal val="0"/></p:val></p:tav>'
                f'<p:tav tm="100000"><p:val><p:strVal val="#ppt_w"/></p:val></p:tav></p:tavLst></p:anim>'
                f'<p:anim calcmode="lin" valueType="num"><p:cBhvr><p:cTn id="{ids.next()}" dur="500" fill="hold"/><p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl>'
                f'<p:attrNameLst><p:attrName>ppt_h</p:attrName></p:attrNameLst></p:cBhvr><p:tavLst><p:tav tm="0"><p:val><p:fltVal val="0"/></p:val></p:tav>'
                f'<p:tav tm="100000"><p:val><p:strVal val="#ppt_h"/></p:val></p:tav></p:tavLst></p:anim>'
                f'<p:animEffect transition="in" filter="fade"><p:cBhvr><p:cTn id="{ids.next()}" dur="500"/><p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl></p:cBhvr></p:animEffect>')
    else:                   # Fade (preset 10)
        preset = 'presetID="10" presetClass="entr" presetSubtype="0"'
        body = set_vis + f'<p:animEffect transition="in" filter="fade"><p:cBhvr><p:cTn id="{ids.next()}" dur="500"/><p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl></p:cBhvr></p:animEffect>'
    return (f'<p:par><p:cTn id="{ids.next()}" {preset} fill="hold" grpId="0" nodeType="{node_type}">'
            f'<p:stCondLst><p:cond delay="{delay}"/></p:stCondLst><p:childTnLst>{body}</p:childTnLst></p:cTn></p:par>')


def timing_xml(items):
    """items: list of (spid, effect, has_text)."""
    ids = Ids()
    root_id, seq_id, click_id, grp_id = ids.next(), ids.next(), ids.next(), ids.next()
    effects = "".join(effect_xml(ids, spid, i * 350, eff, i == 0) for i, (spid, eff, _) in enumerate(items))
    bld = "".join(f'<p:bldP spid="{spid}" grpId="0"/>' for spid, _, has_text in items if has_text)
    return (f'<p:timing><p:tnLst><p:par><p:cTn id="{root_id}" dur="indefinite" restart="never" nodeType="tmRoot"><p:childTnLst>'
            f'<p:seq concurrent="1" nextAc="seek"><p:cTn id="{seq_id}" dur="indefinite" nodeType="mainSeq"><p:childTnLst>'
            f'<p:par><p:cTn id="{click_id}" fill="hold"><p:stCondLst><p:cond delay="indefinite"/><p:cond evt="onBegin" delay="0"><p:tn val="{seq_id}"/></p:cond></p:stCondLst>'
            f'<p:childTnLst><p:par><p:cTn id="{grp_id}" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>{effects}</p:childTnLst></p:cTn></p:par>'
            f'</p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn>'
            f'<p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst>'
            f'<p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst></p:seq>'
            f'</p:childTnLst></p:cTn></p:par></p:tnLst>' + (f'<p:bldLst>{bld}</p:bldLst>' if bld else '') + '</p:timing>')


tmp = dst + ".tmpdir"
shutil.rmtree(tmp, ignore_errors=True)
with zipfile.ZipFile(src) as z: z.extractall(tmp)
slides = sorted([f for f in os.listdir(os.path.join(tmp, "ppt/slides")) if re.fullmatch(r"slide\d+\.xml", f)], key=lambda f: int(re.findall(r"\d+", f)[0]))
report = []
for f in slides:
    n = int(re.findall(r"\d+", f)[0]); path = os.path.join(tmp, "ppt/slides", f)
    xml = open(path, encoding="utf-8").read()
    # animated shapes: find cNvPr with name anim-<k>[-<effect>]; detect whether the parent is a p:sp (text) or p:pic
    items = []
    for m in re.finditer(r'<p:(sp|pic)>\s*<p:nv(?:Sp|Pic)Pr>\s*<p:cNvPr id="(\d+)" name="(anim-(\d+)(?:-([a-z]+))?)"', xml):
        kind, spid, _, order, eff = m.groups()
        items.append((int(order), int(spid), eff or "fade", kind == "sp"))
    items.sort()
    timing = timing_xml([(spid, eff, has_text) for _, spid, eff, has_text in items]) if items else ""
    trans = TRANSITIONS.get(n, DEFAULT_TRANSITION)
    xml = re.sub(r"<p:transition.*?</p:transition>|<p:timing>.*?</p:timing>", "", xml, flags=re.S)
    anchor = "</p:clrMapOvr>" if "</p:clrMapOvr>" in xml else "</p:cSld>"
    xml = xml.replace(anchor, anchor + trans + timing, 1)
    minidom.parseString(xml.encode("utf-8"))  # well-formedness check
    open(path, "w", encoding="utf-8").write(xml)
    report.append((n, len(items)))
if os.path.exists(dst): os.remove(dst)
with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as z:
    for root, _, files in os.walk(tmp):
        for name in files:
            full = os.path.join(root, name); z.write(full, os.path.relpath(full, tmp))
shutil.rmtree(tmp)
print("animated:", report)
