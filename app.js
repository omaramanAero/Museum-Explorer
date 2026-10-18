/* Museum Explorer Karlsruhe — one script for the home page and every exhibit page. */
(() => {
  const BASE = document.documentElement.dataset.base || './';
  const PAGE = document.documentElement.dataset.page;          // "home" | "exhibit"
  const EXHIBIT_ID = document.documentElement.dataset.exhibit; // e.g. "EX01"

  // ------------------------------------------------------------------ i18n
  const UI = {
    en: {
      tagline: 'Naturkundemuseum Karlsruhe', home: 'All exhibits', play: 'Play animation', pause: 'Pause animation',
      anatomy: 'Anatomy', ar: 'View in AR', arNo: 'AR opens on an ARCore Android phone or an iPhone/iPad with AR Quick Look. On this device you can still turn and zoom the model.',
      arYes: 'AR places the model in your camera view at real size. Pinch to scale it down indoors.',
      hint: 'Drag to turn · pinch or scroll to zoom', modelNote: 'Original stylised reconstruction made for this project — not a scan of the museum object.',
      illustrative: 'Illustrative', facts: 'Key facts', story: 'About this exhibit', partsH: 'Anatomy guide',
      partsHint: 'Tap a part, or switch on Anatomy and tap the numbered dots on the model.', fn: 'Function', prev: 'Previous', next: 'Next', close: 'Close',
      mapsH: 'Maps', inMuseum: 'Where it is in the museum', found: 'Where it was found', distance: (km) => `${km.toLocaleString('en')} km from the museum`,
      layout: 'Illustrative layout, not the official floor plan', entrance: 'Main entrance', sources: 'Sources',
      anims: { Flap: 'Flap', Glide: 'Glide' }, zones: { entrance: 'Entrance (outdoor)', geology: 'Geology & palaeontology', whales: 'Whale hall', vivarium: 'Vivarium', minerals: 'Minerals' },
      heroH: 'Scan. Turn. Tap the bones.', heroP: 'A QR code on each exhibit opens its page: a 3D model you can spin, animate and place in your room with AR, numbered anatomy you can tap, and maps of where it is and where it was found.',
      exhibitsH: 'Exhibits', open: 'Open exhibit', howH: 'How it works',
      how: [['Scan the QR code', 'Each exhibit card carries a code that opens that exhibit, in English or German.'], ['Explore in 3D and AR', 'Turn the model, play its animation, or tap “View in AR” to place it in your space.'], ['Tap the anatomy', 'Numbered dots name each part and explain what it was for.']],
      mapH: 'From the find site to Karlsruhe', mapCap: 'Points from the project GeoPackage (QGIS): the museum and the discovery sites, joined by great-circle lines.',
      cards: 'Print the QR exhibit cards', about: 'Student prototype for the AR/VR + GIS course at Hochschule Karlsruhe (HKA). Not an official service of the Staatliches Museum für Naturkunde Karlsruhe.',
      osm: '© OpenStreetMap contributors'
    },
    de: {
      tagline: 'Naturkundemuseum Karlsruhe', home: 'Alle Exponate', play: 'Animation abspielen', pause: 'Animation anhalten',
      anatomy: 'Anatomie', ar: 'In AR ansehen', arNo: 'AR öffnet sich auf Android-Smartphones mit ARCore oder auf iPhone/iPad mit AR Quick Look. Hier können Sie das Modell trotzdem drehen und zoomen.',
      arYes: 'AR stellt das Modell in Originalgröße in Ihr Kamerabild. In Innenräumen mit zwei Fingern verkleinern.',
      hint: 'Ziehen zum Drehen · Finger spreizen oder scrollen zum Zoomen', modelNote: 'Eigene stilisierte Rekonstruktion für dieses Projekt – kein Scan des Museumsobjekts.',
      illustrative: 'Veranschaulichend', facts: 'Steckbrief', story: 'Über dieses Exponat', partsH: 'Anatomie-Führer',
      partsHint: 'Tippen Sie auf einen Teil – oder schalten Sie „Anatomie“ ein und tippen Sie auf die Nummern am Modell.', fn: 'Funktion', prev: 'Zurück', next: 'Weiter', close: 'Schließen',
      mapsH: 'Karten', inMuseum: 'Wo es im Museum steht', found: 'Wo es gefunden wurde', distance: (km) => `${km.toLocaleString('de')} km vom Museum entfernt`,
      layout: 'Veranschaulichender Plan, nicht der offizielle Grundriss', entrance: 'Haupteingang', sources: 'Quellen',
      anims: { Flap: 'Flügelschlag', Glide: 'Gleiten' }, zones: { entrance: 'Eingang (außen)', geology: 'Erdgeschichte & Paläontologie', whales: 'Walsaal', vivarium: 'Vivarium', minerals: 'Mineralien' },
      heroH: 'Scannen. Drehen. Knochen antippen.', heroP: 'Ein QR-Code an jedem Exponat öffnet seine Seite: ein 3D-Modell zum Drehen, Animieren und per AR im eigenen Raum Platzieren, nummerierte Anatomie zum Antippen und Karten zu Standort und Fundort.',
      exhibitsH: 'Exponate', open: 'Exponat öffnen', howH: 'So funktioniert es',
      how: [['QR-Code scannen', 'Jede Exponatkarte trägt einen Code, der genau dieses Exponat öffnet – auf Deutsch oder Englisch.'], ['In 3D und AR entdecken', 'Modell drehen, Animation abspielen oder „In AR ansehen“ antippen, um es in den Raum zu stellen.'], ['Anatomie antippen', 'Nummerierte Punkte benennen jeden Teil und erklären seine Funktion.']],
      mapH: 'Vom Fundort nach Karlsruhe', mapCap: 'Punkte aus dem Projekt-GeoPackage (QGIS): das Museum und die Fundorte, verbunden durch Großkreislinien.',
      cards: 'QR-Exponatkarten drucken', about: 'Studentischer Prototyp für den Kurs AR/VR + GIS an der Hochschule Karlsruhe (HKA). Kein offizielles Angebot des Staatlichen Museums für Naturkunde Karlsruhe.',
      osm: '© OpenStreetMap-Mitwirkende'
    }
  };
  const store = {
    get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
    set(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* storage unavailable */ } }
  };
  let lang = new URLSearchParams(location.search).get('lang') || store.get('mek-lang') || ((navigator.language || 'en').toLowerCase().startsWith('de') ? 'de' : 'en');
  if (!UI[lang]) lang = 'en';
  const t = (k) => UI[lang][k];
  const L = (v) => (v && typeof v === 'object' && !Array.isArray(v)) ? (v[lang] ?? v.en) : v;
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const css = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

  const ICON = {
    play: '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M8 5.5v13l10.5-6.5L8 5.5Z"/></svg>',
    pause: '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M7 5h3.5v14H7zM13.5 5H17v14h-3.5z"/></svg>',
    ar: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3 4 7.5v9L12 21l8-4.5v-9L12 3Z"/><path d="M4 7.5 12 12l8-4.5M12 12v9"/></svg>',
    bone: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="2.5" fill="currentColor"/></svg>',
    close: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6 6 18"/></svg>'
  };

  // ------------------------------------------------------------------ shared header
  function header() {
    const el = document.getElementById('top');
    el.innerHTML = `
      <a class="wordmark" href="${BASE}index.html${lang === 'de' ? '?lang=de' : ''}"><b>Museum Explorer</b><span>${esc(t('tagline'))}</span></a>
      <div class="mek-lang" role="group" aria-label="Language / Sprache">
        <button type="button" data-lang="en" aria-pressed="${lang === 'en'}">EN</button>
        <button type="button" data-lang="de" aria-pressed="${lang === 'de'}">DE</button>
      </div>`;
    el.querySelector('.mek-lang').addEventListener('click', (e) => {
      const b = e.target.closest('button[data-lang]'); if (!b || b.dataset.lang === lang) return;
      lang = b.dataset.lang; store.set('mek-lang', lang); render();
    });
  }

  // ------------------------------------------------------------------ maps (Leaflet)
  const maps = [];
  function clearMaps() { while (maps.length) maps.pop().remove(); }
  function baseMap(el, opts = {}) {
    const m = L$.map(el, { scrollWheelZoom: false, zoomControl: true, attributionControl: true, ...opts });
    L$.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: t('osm') }).addTo(m);
    maps.push(m); return m;
  }
  const L$ = window.L;
  function dot(latlng, color, label, permanent = true) {
    return L$.circleMarker(latlng, { radius: 8, color: '#ffffff', weight: 2, fillColor: color, fillOpacity: 1 })
      .bindTooltip(esc(label), { permanent, direction: 'top', offset: [0, -8], className: 'mek-tip' });
  }
  function greatCircle(a, b, n = 64) { // [lat,lon] pairs
    const r = Math.PI / 180, [la1, lo1, la2, lo2] = [a[0] * r, a[1] * r, b[0] * r, b[1] * r];
    const d = 2 * Math.asin(Math.sqrt(Math.sin((la2 - la1) / 2) ** 2 + Math.cos(la1) * Math.cos(la2) * Math.sin((lo2 - lo1) / 2) ** 2));
    if (d === 0) return [a, b];
    const pts = [];
    for (let i = 0; i <= n; i++) {
      const f = i / n, A = Math.sin((1 - f) * d) / Math.sin(d), B = Math.sin(f * d) / Math.sin(d);
      const x = A * Math.cos(la1) * Math.cos(lo1) + B * Math.cos(la2) * Math.cos(lo2);
      const y = A * Math.cos(la1) * Math.sin(lo1) + B * Math.cos(la2) * Math.sin(lo2);
      const z = A * Math.sin(la1) + B * Math.sin(la2);
      pts.push([Math.atan2(z, Math.hypot(x, y)) / r, Math.atan2(y, x) / r]);
    }
    return pts;
  }

  function floorPlan(zone) {
    const Z = UI[lang].zones;
    const box = (id, x, y, w, h) => {
      const on = id === zone;
      return `<g><rect x="${x}" y="${y}" width="${w}" height="${h}" rx="6" fill="${on ? css('--amber') : 'rgba(244,239,230,0.10)'}" stroke="rgba(244,239,230,0.35)"/>
        <text x="${x + w / 2}" y="${y + h / 2}" text-anchor="middle" dominant-baseline="middle" font-family="${css('--font-sans').replace(/"/g, "'")}" font-size="13" font-weight="600" fill="${on ? css('--on-amber') : '#f4efe6'}">${esc(Z[id])}</text></g>`;
    };
    const pin = zone === 'entrance';
    return `<svg viewBox="0 0 400 260" role="img" aria-label="${esc(t('layout'))}">
      <rect x="20" y="20" width="360" height="180" rx="10" fill="none" stroke="rgba(244,239,230,0.55)" stroke-width="2"/>
      ${box('vivarium', 36, 36, 150, 70)}${box('minerals', 214, 36, 150, 70)}
      ${box('geology', 36, 118, 150, 66)}${box('whales', 214, 118, 150, 66)}
      <rect x="170" y="196" width="60" height="8" fill="#f4efe6"/>
      <circle cx="200" cy="232" r="${pin ? 11 : 7}" fill="${pin ? css('--amber') : 'rgba(244,239,230,0.35)'}" stroke="#fff" stroke-width="2"/>
      <text x="222" y="236" font-family="${css('--font-sans').replace(/"/g, "'")}" font-size="12" font-weight="600" fill="#f4efe6">${esc(t('entrance'))}${pin ? ' · Quetzalcoatlus' : ''}</text>
    </svg>`;
  }

  // ------------------------------------------------------------------ exhibit page
  let DATA, ex, mv, active = -1, anatomyOn = false, playing = true, anim = null;

  function renderExhibit() {
    ex = DATA.exhibits.find((e) => e.id === EXHIBIT_ID) || DATA.exhibits[0];
    document.title = `${L(ex.name)} · Museum Explorer Karlsruhe`;
    const main = document.getElementById('main');
    const hasAnim = ex.animations.length > 0;
    if (anim === null) anim = ex.animations[0] || null;
    const parts = ex.parts;
    main.innerHTML = `
    <div class="wrap">
      <header class="ex-head">
        <div class="tags"><span class="mek-tag mek-tag--era">${esc(L(ex.era))}</span><span class="mek-tag mek-tag--id">${ex.id}</span></div>
        <p class="eyebrow">${esc(L(ex.eyebrow))}</p>
        <h1>${esc(L(ex.name))}</h1>
        <p class="sci">${esc(ex.sci)}</p>
      </header>
      <div class="ex-grid">
        <div>
          <figure class="stage">
            <model-viewer id="mv" src="${BASE}${ex.model}" alt="${esc(L(ex.name))} – 3D" camera-controls touch-action="pan-y"
              ${hasAnim ? `autoplay animation-name="${anim}"` : 'auto-rotate auto-rotate-delay="1500" rotation-per-second="18deg"'}
              max-camera-orbit="auto auto 400%" min-camera-orbit="auto auto 5%" ar ar-modes="webxr scene-viewer quick-look" ar-scale="auto" camera-orbit="${ex.orbit}" shadow-intensity="0.9" shadow-softness="0.8"
              exposure="1.05" interaction-prompt="auto" interpolation-decay="120">
              ${parts.map((p, i) => `<button class="mek-hotspot" slot="hotspot-${p.id}" data-i="${i}" data-position="${p.position.join('m ')}m" data-normal="${p.normal.join('m ')}m" type="button" aria-label="${p.n}: ${esc(L(p.name))}">${p.n}<span class="mek-hotspot__label">${esc(L(p.name))}</span></button>`).join('')}
            </model-viewer>
            <div class="stage-top">
              ${hasAnim ? `<div class="chips" role="group" aria-label="Animation">${ex.animations.map((a) => `<button type="button" data-anim="${a}" aria-pressed="${a === anim}">${esc(UI[lang].anims[a] || a)}</button>`).join('')}</div>` : '<span></span>'}
              <span class="mek-tag mek-tag--illustrative" style="background:color-mix(in srgb, var(--surface) 88%, transparent)">${esc(t('illustrative'))}</span>
            </div>
            <div class="stage-bar">
              ${hasAnim ? `<button class="icon-btn" id="playBtn" type="button" aria-label="${esc(t('pause'))}">${ICON.pause}</button>` : ''}
              <button class="toggle-btn" id="anatomyBtn" type="button" aria-pressed="${anatomyOn}">${ICON.bone}${esc(t('anatomy'))}</button>
              <span class="grow"></span>
              <button class="mek-btn mek-btn--primary" id="arBtn" type="button">${ICON.ar}${esc(t('ar'))}</button>
            </div>
          </figure>
          <div class="stage-note"><span>${esc(t('hint'))}</span><span>${esc(t('modelNote'))}</span></div>
          <p class="ar-note" id="arNote"></p>

          <section aria-labelledby="h-story" class="story">
            <h2 id="h-story">${esc(t('story'))}</h2>
            ${L(ex.story).map((s) => `<p>${esc(s)}</p>`).join('')}
          </section>

          <section aria-labelledby="h-maps">
            <h2 id="h-maps">${esc(t('mapsH'))}</h2>
            <div class="maps">
              <div class="map-card">
                <h3>${esc(t('inMuseum'))}${ex.inMuseum.verified ? '' : `<span class="mek-tag mek-tag--illustrative">${esc(t('illustrative'))}</span>`}</h3>
                ${ex.inMuseum.kind === 'outdoor' ? '<div class="map" id="mapIn"></div>' : `<div class="map floor">${floorPlan(ex.inMuseum.zone)}</div>`}
                <p class="cap">${esc(L(ex.inMuseum.precision))}${ex.inMuseum.kind === 'indoor' ? ' ' + esc(t('layout')) + '.' : ''}</p>
              </div>
              <div class="map-card">
                <h3>${esc(t('found'))}</h3>
                ${ex.found ? '<div class="map" id="mapFound"></div>' : `<div class="map-empty">${esc(L(ex.foundNote))}</div>`}
                ${ex.found ? `<p class="cap"><b>${esc(L(ex.found.place))}</b> · ${esc(t('distance')(ex.found.distanceKm))}. ${esc(L(ex.found.precision))}</p>` : ''}
              </div>
            </div>
          </section>

          <section aria-labelledby="h-src">
            <h2 id="h-src">${esc(t('sources'))}</h2>
            <ol class="sources">${ex.sources.map((s) => `<li><a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.title)}</a></li>`).join('')}</ol>
          </section>
        </div>

        <aside class="ex-side">
          <section style="margin-top:0" aria-labelledby="h-facts">
            <h2 id="h-facts" class="sr-only">${esc(t('facts'))}</h2>
            <dl class="mek-facts">${ex.facts.map((f) => `<div class="mek-fact"><dt>${esc(L(f.label))}</dt><dd>${esc(L(f.value))}<small>${esc(L(f.note))}</small></dd></div>`).join('')}</dl>
          </section>
          <section aria-labelledby="h-parts">
            <h2 id="h-parts">${esc(t('partsH'))}</h2>
            <p class="muted small" style="margin:0 0 var(--space-3)">${esc(t('partsHint'))}</p>
            <ol class="parts">${parts.map((p, i) => `<li><button type="button" data-i="${i}"><span class="num">${p.n}</span><span>${esc(L(p.name))}<small>${esc(L(p.term))}</small></span></button></li>`).join('')}</ol>
          </section>
        </aside>
      </div>
    </div>
    <div class="sheet-wrap" id="sheetWrap" aria-hidden="true">
      <section class="mek-sheet" role="dialog" aria-modal="false" aria-labelledby="sheetTitle">
        <div class="mek-sheet__grip"></div>
        <button class="icon-btn sheet-close" id="sheetClose" type="button" aria-label="${esc(t('close'))}">${ICON.close}</button>
        <div id="sheetBody"></div>
      </section>
    </div>`;

    mv = document.getElementById('mv');
    // controls
    const playBtn = document.getElementById('playBtn');
    const syncPlay = () => { if (!playBtn) return; playBtn.innerHTML = playing ? ICON.pause : ICON.play; playBtn.setAttribute('aria-label', playing ? t('pause') : t('play')); };
    if (playBtn) playBtn.addEventListener('click', () => { playing = !playing; if (playing) { setAnatomy(false); mv.play(); } else mv.pause(); syncPlay(); });
    main.querySelectorAll('[data-anim]').forEach((b) => b.addEventListener('click', () => {
      anim = b.dataset.anim; mv.animationName = anim; playing = true; setAnatomy(false); mv.play(); syncPlay();
      main.querySelectorAll('[data-anim]').forEach((x) => x.setAttribute('aria-pressed', x === b));
    }));
    document.getElementById('anatomyBtn').addEventListener('click', () => setAnatomy(!anatomyOn));
    mv.addEventListener('click', (e) => { const h = e.target.closest('.mek-hotspot'); if (h) openPart(+h.dataset.i); });
    main.querySelectorAll('.parts button').forEach((b) => b.addEventListener('click', () => { setAnatomy(true); openPart(+b.dataset.i); document.querySelector('.stage').scrollIntoView({ behavior: 'smooth', block: 'start' }); }));
    document.getElementById('sheetClose').addEventListener('click', closePart);
    if (!window.__mekKeys) { document.addEventListener('keydown', onKey); window.__mekKeys = true; }

    // AR
    const arBtn = document.getElementById('arBtn'), arNote = document.getElementById('arNote');
    const arState = () => { const ok = mv.canActivateAR; arBtn.disabled = !ok; arNote.textContent = ok ? t('arYes') : t('arNo'); };
    mv.addEventListener('load', () => { arState(); if (anatomyOn) setAnatomy(true); if (playing && ex.animations.length) mv.play(); });
    arBtn.addEventListener('click', () => mv.canActivateAR && mv.activateAR());
    arState();
    syncPlay();

    // maps
    requestAnimationFrame(() => {
      clearMaps();
      const M = DATA.museum;
      if (ex.inMuseum.kind === 'outdoor') {
        const m = baseMap('mapIn').setView([ex.inMuseum.lat, ex.inMuseum.lon], 17);
        dot([ex.inMuseum.lat, ex.inMuseum.lon], css('--rust'), `${L(ex.name)} · ${L(DATA.museum.name)}`).addTo(m);
      }
      if (ex.found) {
        const m = baseMap('mapFound');
        const a = [ex.found.lat, ex.found.lon], b = [M.lat, M.lon];
        L$.polyline(greatCircle(a, b), { color: css('--amber'), weight: 3, dashArray: '6 6' }).addTo(m);
        dot(a, css('--amber'), L(ex.found.place)).addTo(m);
        dot(b, css('--rust'), 'SMNK Karlsruhe', false).addTo(m);
        m.fitBounds(L$.latLngBounds([a, b]).pad(0.35));
      }
    });
    if (active >= 0) openPart(active, true);
  }

  function setAnatomy(on) {
    anatomyOn = on;
    const btn = document.getElementById('anatomyBtn'); if (btn) btn.setAttribute('aria-pressed', on);
    if (!mv) return;
    mv.classList.toggle('anatomy', on);
    if (on) {
      mv.pause(); try { mv.currentTime = 0; } catch (e) { /* not loaded yet */ }
      mv.autoRotate = false;
      if (active < 0) { mv.cameraTarget = 'auto auto auto'; mv.cameraOrbit = ex.anatomyOrbit; }
    }
    else {
      closePart();
      if (ex.animations.length) { if (playing) mv.play(); } else mv.autoRotate = true;
    }
  }

  function openPart(i, silent) {
    const parts = ex.parts; if (i < 0 || i >= parts.length) return;
    if (!anatomyOn) setAnatomy(true);
    active = i;
    const p = parts[i];
    mv.querySelectorAll('.mek-hotspot').forEach((h) => h.classList.toggle('is-active', +h.dataset.i === i));
    document.querySelectorAll('.parts button').forEach((b) => b.setAttribute('aria-current', +b.dataset.i === i));
    mv.cameraTarget = `${p.position[0]}m ${p.position[1]}m ${p.position[2]}m`;
    const [nx, ny, nz] = p.normal;
    mv.cameraOrbit = ny > 0.7 ? `30deg 38deg ${ex.partRadius}`
      : `${Math.round(Math.atan2(nx, nz) * 180 / Math.PI)}deg 78deg ${ex.partRadius}`;
    const prev = parts[i - 1], next = parts[i + 1];
    document.getElementById('sheetBody').innerHTML = `
      <div class="mek-sheet__head"><span class="mek-sheet__num">${p.n}</span><div><h3 class="mek-sheet__title" id="sheetTitle">${esc(L(p.name))}</h3><p class="mek-sheet__sub">${esc(L(p.term))}</p></div></div>
      <p class="mek-sheet__body">${esc(L(p.desc))}</p>
      <dl class="mek-sheet__fn"><dt>${esc(t('fn'))}</dt><dd>${esc(L(p.fn))}</dd></dl>
      <div class="mek-sheet__nav">
        <button class="mek-btn mek-btn--ghost" type="button" data-go="${i - 1}" ${prev ? '' : 'disabled'}>← ${prev ? esc(L(prev.name)) : esc(t('prev'))}</button>
        <button class="mek-btn mek-btn--ghost" type="button" data-go="${i + 1}" ${next ? '' : 'disabled'}>${next ? esc(L(next.name)) : esc(t('next'))} →</button>
      </div>`;
    document.querySelectorAll('#sheetBody [data-go]').forEach((b) => b.addEventListener('click', () => openPart(+b.dataset.go)));
    const w = document.getElementById('sheetWrap'); w.classList.add('open'); w.setAttribute('aria-hidden', 'false');
    if (window.matchMedia('(max-width: 959px)').matches) document.querySelector('.stage').scrollIntoView({ behavior: 'smooth', block: 'start' });
    if (!silent) document.getElementById('sheetTitle').focus?.({ preventScroll: true });
  }

  function closePart() {
    active = -1;
    const w = document.getElementById('sheetWrap'); if (!w) return;
    w.classList.remove('open'); w.setAttribute('aria-hidden', 'true');
    if (mv) {
      mv.querySelectorAll('.mek-hotspot').forEach((h) => h.classList.remove('is-active'));
      mv.cameraTarget = 'auto auto auto'; mv.cameraOrbit = ex.orbit;
    }
    document.querySelectorAll('.parts button').forEach((b) => b.removeAttribute('aria-current'));
  }

  function onKey(e) {
    if (PAGE !== 'exhibit') return;
    if (e.key === 'Escape') closePart();
    if (active >= 0 && e.key === 'ArrowRight') openPart(active + 1);
    if (active >= 0 && e.key === 'ArrowLeft') openPart(active - 1);
  }

  // ------------------------------------------------------------------ home page
  function renderHome() {
    document.title = 'Museum Explorer Karlsruhe';
    const q = lang === 'de' ? '?lang=de' : '';
    document.getElementById('main').innerHTML = `
    <div class="wrap">
      <section class="hero" style="margin-top:0">
        <p class="eyebrow">${esc(L(DATA.museum.name))} · AR / GIS</p>
        <h1>${esc(t('heroH'))}</h1>
        <p>${esc(t('heroP'))}</p>
      </section>
      <section aria-labelledby="h-ex">
        <h2 id="h-ex">${esc(t('exhibitsH'))}</h2>
        <div class="ex-list">${DATA.exhibits.map((e) => `
          <a class="ex-card${e.hero ? ' hero-card' : ''}" href="${BASE}exhibit/${e.id}/${q}">
            <div><p class="eyebrow">${esc(L(e.eyebrow))}</p><h3>${esc(L(e.name))}</h3><p class="sci">${esc(e.sci)}</p></div>
            <div class="foot"><span class="mek-tag mek-tag--era">${esc(L(e.era))}</span><span class="mek-tag mek-tag--id">${e.id}</span></div>
          </a>`).join('')}</div>
      </section>
      <section aria-labelledby="h-how">
        <h2 id="h-how">${esc(t('howH'))}</h2>
        <ol class="steps">${t('how').map(([h, p]) => `<li><b>${esc(h)}</b>${esc(p)}</li>`).join('')}</ol>
      </section>
      <section aria-labelledby="h-map">
        <h2 id="h-map">${esc(t('mapH'))}</h2>
        <div class="overview-map" id="mapAll"></div>
        <p class="muted small">${esc(t('mapCap'))}</p>
      </section>
    </div>`;
    requestAnimationFrame(() => {
      clearMaps();
      const M = DATA.museum, m = baseMap('mapAll'), pts = [[M.lat, M.lon]];
      DATA.exhibits.forEach((e) => {
        if (!e.found) return;
        const a = [e.found.lat, e.found.lon]; pts.push(a);
        L$.polyline(greatCircle(a, [M.lat, M.lon]), { color: css('--amber'), weight: 2.5, dashArray: '6 6' }).addTo(m);
        dot(a, css('--amber'), `${e.id} ${L(e.name)}`).addTo(m).on('click', () => { location.href = `${BASE}exhibit/${e.id}/${q}`; });
      });
      dot([M.lat, M.lon], css('--rust'), 'SMNK Karlsruhe', false).addTo(m);
      m.fitBounds(L$.latLngBounds(pts).pad(0.2));
    });
  }

  // ------------------------------------------------------------------ boot
  function render() {
    document.documentElement.lang = lang;
    header();
    const foot = document.getElementById('foot');
    if (foot) foot.innerHTML = `<div class="wrap"><span>${esc(t('about'))}</span><span><a href="${BASE}cards.html">${esc(t('cards'))}</a> · <a href="${BASE}index.html${lang === 'de' ? '?lang=de' : ''}">${esc(t('home'))}</a></span></div>`;
    if (PAGE === 'exhibit') renderExhibit(); else renderHome();
  }

  fetch(`${BASE}data/exhibits.json`).then((r) => r.json()).then((d) => { DATA = d; render(); })
    .catch((err) => { document.getElementById('main').innerHTML = `<div class="wrap"><p>Could not load exhibit data (${esc(err.message)}). If you opened this file directly, serve the folder over http instead.</p></div>`; });
})();
