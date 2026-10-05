// Leaflet risk map of Uzbekistan with theme-aware tiles.
window.createRiskMap = function (el, regions, opts = {}) {
  const T = window.T || ((k) => k);
  const map = L.map(el, { zoomControl: true, scrollWheelZoom: false, attributionControl: true }).setView([41.2, 64.2], 6);
  const esri = (path) => `https://server.arcgisonline.com/ArcGIS/rest/services/${path}/MapServer/tile/{z}/{y}/{x}`;
  const attribution = "Tiles &copy; Esri — Maxar, Earthstar Geographics";
  const satellite = L.layerGroup([
    L.tileLayer(esri("World_Imagery"), { attribution, maxZoom: 17 }),
    L.tileLayer(esri("Reference/World_Boundaries_and_Places"), { maxZoom: 17, opacity: 0.9 }),
  ]);
  function canvasLayer() {
    const dark = document.documentElement.dataset.theme !== "light";
    return L.tileLayer(esri(dark ? "Canvas/World_Dark_Gray_Base" : "Canvas/World_Light_Gray_Base"), { attribution, maxZoom: 16 });
  }
  const scheme = L.layerGroup();
  function refreshScheme() {
    scheme.clearLayers();
    scheme.addLayer(canvasLayer());
  }
  refreshScheme();
  window.addEventListener("themechange", refreshScheme);
  satellite.addTo(map);
  L.control.layers({ [T("layer_sat")]: satellite, [T("layer_map")]: scheme }, null, { position: "topright" }).addTo(map);
  map.on("click", () => map.scrollWheelZoom.enable());
  map.on("mouseout", () => map.scrollWheelZoom.disable());

  const markers = {};
  regions.forEach((r) => {
    const size = 14 + Math.round(Math.sqrt(r.population / 1e6) * 8);
    const icon = L.divIcon({
      className: "",
      html: `<div class="pulse-marker" style="--c:${r.color};width:${size}px;height:${size}px"></div>`,
      iconSize: [size, size],
      iconAnchor: [size / 2, size / 2],
    });
    const m = L.marker([r.lat, r.lng], { icon, title: r.name }).addTo(map);
    const action = opts.onSelect
      ? `<button class="btn btn-primary btn-sm mt-1" data-pick="${r.slug}">${T("map_pick")}</button>`
      : `<a class="btn btn-primary btn-sm mt-1" href="${opts.predictUrl || "/predict/"}?region=${r.slug}">${T("map_forecast")}</a>`;
    m.bindPopup(
      `<div style="min-width:190px"><b style="font-family:'Space Grotesk';font-size:1.05rem">${r.name}</b>
       <div style="margin:6px 0"><span class="badge" style="--c:${r.color}">${T("map_baseline")} ${r.score}/100</span></div>
       <div class="muted small">${T("map_main")}: ${r.top.join(", ")}</div>
       <div class="muted small">${T("map_population")}: ${(r.population / 1e6).toFixed(2)} ${T("mln")}</div>${action}</div>`
    );
    if (opts.onSelect) m.on("click", () => opts.onSelect(r.slug));
    markers[r.slug] = m;
  });
  if (opts.onSelect) {
    el.addEventListener("click", (e) => {
      const b = e.target.closest("[data-pick]");
      if (b) { opts.onSelect(b.dataset.pick); map.closePopup(); }
    });
  }
  return {
    map,
    focus(slug) {
      const m = markers[slug];
      if (m) { map.flyTo(m.getLatLng(), 7, { duration: 1.2 }); setTimeout(() => m.openPopup(), 1250); }
    },
  };
};
