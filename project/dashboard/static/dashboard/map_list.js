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

async function map_init_points(map, options) {
  const layerGroup = L.featureGroup().addTo(map);
  const points_url = "/api/points/";

  L.control.fullscreen().addTo(map);

  const resp = await fetch(points_url);
  const data = await resp.json();

  L.geoJSON(data, {
    pointToLayer: style,
  })
    .bindPopup(
      (layer) =>
        `${layer.feature.properties.issuingorganization}: <span class="${
          layer.feature.properties.status_type == "OK"
            ? "text-green"
            : "text-red"
        }">${STATUS_TYPES[
          layer.feature.properties.status_type
        ].toUpperCase()}</span>`
    )
    .addTo(layerGroup);

  map.fitBounds(layerGroup.getBounds());
}

async function map_events(map, options, feeds) {
  console.log(feeds);

  const layerGroup = L.featureGroup().addTo(map);

  L.setOptions(map, { preferCanvas: true });

  L.control.fullscreen().addTo(map);

  for await (const feed of feeds) {
    const points_url = `/api/feeds/${feed}`;
    const resp = await fetch(points_url);
    const data = await resp.json();

    const feed_data = data["feed_data"];

    if (Object.keys(feed_data).length === 0) {
      continue;
    }

    L.geoJSON(feed_data, {
      onEachFeature: (feature, layer) => {
        layer.bindPopup(
          feed_data["feed_info"] ||
            (feed_data["road_event_feed_info"] &&
              feed_data["road_event_feed_info"]["version"].startsWith("4"))
            ? `<ul class="usa-list usa-list--unstyled">
                <li>Event Type: ${feature.properties.core_details.event_type}</li>
                <li>Roads: ${feature.properties.core_details.road_names}</li>
                <li>Direction: ${feature.properties.core_details.direction}</li>
                <li>Start Date: ${feature.properties.start_date}</li>
                <li>End Date: ${feature.properties.end_date}</li>
                <li>Vehicle Impact: ${feature.properties.vehicle_impact}</li>
                </ul>
                `
            : `<ul class="usa-list usa-list--unstyled">
                <li>Event Type: ${feature.properties.event_type}</li>
                <li>Roads: ${feature.properties.road_names}</li>
                <li>Direction: ${feature.properties.direction}</li>
                <li>Start Date: ${feature.properties.start_date}</li>
                <li>End Date: ${feature.properties.end_date}</li>
                <li>Vehicle Impact: ${feature.properties.vehicle_impact}</li>
                </ul>
                `
        );
      },
    }).addTo(layerGroup);
  }

  map.fitBounds(layerGroup.getBounds());
}
