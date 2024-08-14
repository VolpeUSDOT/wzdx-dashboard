function map_details(map, options, feedname, version) {
  const layerGroup = L.featureGroup().addTo(map);

  const points_url = `/api/feeds/${feedname}`;
  fetch(points_url)
    .then(function (resp) {
      return resp.json();
    })
    .then(function (data) {
      const feed_data = data["feed_data"];

      L.geoJSON(feed_data, {
        onEachFeature: (feature, layer) => {
          layer.bindPopup(
            version.startsWith("4")
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

      map.fitBounds(layerGroup.getBounds());
    });
}
