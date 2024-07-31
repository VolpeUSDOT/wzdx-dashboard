const osm = "https://www.openstreetmap.org/copyright";
const copy = `© <a href='${osm}'>OpenStreetMap</a>`;
const url = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png";
const layer = L.tileLayer(url, { attribution: copy });
const map = L.map("map", { layers: [layer] });

map.fitWorld();
const layerGroup = L.layerGroup().addTo(map);

async function load_points() {
  const points_url = `/api/feedpoints/?in_bbox=${map
    .getBounds()
    .toBBoxString()}`;
  const response = await fetch(points_url);
  const geojson = await response.json();
  return geojson;
}

async function render_points() {
  const points = await load_points();
  layerGroup.clearLayers();
  L.geoJSON(points)
    .bindPopup((layer) => layer.feature.properties.issuingorganization)
    .addTo(layerGroup);
}

map.on("moveend", render_points);
