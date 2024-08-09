STATUS_TYPES = {
  NA: "null",
  OK: "ok",
  ER: "error",
  OU: "outdated",
  ST: "stale",
  OF: "offline",
};

function style(feature, latlng) {
  return L.circleMarker(latlng, {
    radius: 8,
    className:
      "usa-icon " +
      (feature.properties.status_type === "OK" ? "text-green" : "text-red"),
    stroke: false,
    fillOpacity: 0.8,
    alt: feature.properties.issuingorganization,
  });
}

async function map_init(map, options) {
  const layerGroup = L.featureGroup().addTo(map);
  const points_url = "/api/points/";

  fetch(points_url)
    .then(function (resp) {
      return resp.json();
    })
    .then(function (data) {
      L.geoJSON(data, {
        pointToLayer: style,
      })
        .bindPopup(
          (layer) =>
            `${layer.feature.properties.issuingorganization}: <span class="${layer.feature.properties.status_type == "OK" ? 'text-green' : 'text-red'}">${STATUS_TYPES[layer.feature.properties.status_type].toUpperCase()}</span>`
        )
        .addTo(layerGroup);

      map.fitBounds(layerGroup.getBounds());
    });
}
