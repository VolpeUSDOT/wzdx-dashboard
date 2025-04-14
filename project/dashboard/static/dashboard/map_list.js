const STATUS_TYPES = {
  NA: "null",
  OK: "ok",
  ER: "error",
  OU: "outdated",
  ST: "stale",
  OF: "offline",
};

function makeMap(container) {
  const map = new maplibregl.Map({
    container: container, // container id
    style: "https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json", // style URL
    center: [-103.771556, 44.967243], // starting position [lng, lat]
    zoom: 1, // starting zoom
  });

  map.addControl(
    new maplibregl.FullscreenControl({
      container: document.querySelector(container),
    })
  );

  map.on("load", async () => {
    const points_url = "/api/points/";

    const resp = await fetch(points_url);
    const data = await resp.json();

    map.addSource("geojson-source", {
      type: "geojson",
      data: data,
    });

    map.addLayer({
      id: "geojson-points",
      type: "circle",
      source: "geojson-source",
      paint: {
        "circle-radius": 8,
        "circle-opacity": 0.8,
        "circle-color": [
          "match",
          ["get", "status_type"],
          "OK",
          "#538200",
          "#e52207",
        ],
      },
      filter: ["==", "$type", "Point"],
    });

    map.on("mouseenter", "geojson-points", () => {
      map.getCanvas().style.cursor = "pointer";
    });

    // Change it back to a pointer when it leaves.
    map.on("mouseleave", "geojson-points", () => {
      map.getCanvas().style.cursor = "";
    });

    map.on("click", "geojson-points", (e) => {
      const coordinates = e.features[0].geometry.coordinates.slice();
      const description = `<a class="usa-link" href="${
        e.features[0].properties.pk
      }">${e.features[0].properties.issuingorganization}</a>: <span class="${
        e.features[0].properties.status_type == "OK" ? "text-green" : "text-red"
      }">${STATUS_TYPES[
        e.features[0].properties.status_type
      ].toUpperCase()}</span>`;

      // Ensure that if the map is zoomed out such that multiple
      // copies of the feature are visible, the popup appears
      // over the copy being pointed to.
      while (Math.abs(e.lngLat.lng - coordinates[0]) > 180) {
        coordinates[0] += e.lngLat.lng > coordinates[0] ? 360 : -360;
      }

      new maplibregl.Popup()
        .setLngLat(coordinates)
        .setHTML(description)
        .addTo(map);
    });

    map
      .getSource("geojson-source")
      .getBounds()
      .then((bounds) => map.fitBounds(bounds, { padding: 20 }));
  });
}

// async function map_events(map, options, feeds) {
//   console.log(feeds);

//   const layerGroup = L.featureGroup().addTo(map);

//   L.setOptions(map, { preferCanvas: true });

//   L.control.fullscreen().addTo(map);

//   for await (const feed of feeds) {
//     const points_url = `/api/feeds/${feed}`;
//     const resp = await fetch(points_url);
//     const data = await resp.json();

//     const feed_data = data["feed_data"];

//     if (Object.keys(feed_data).length === 0) {
//       continue;
//     }

//     L.geoJSON(feed_data, {
//       onEachFeature: (feature, layer) => {
//         layer.bindPopup(
//           feed_data["feed_info"] ||
//             (feed_data["road_event_feed_info"] &&
//               feed_data["road_event_feed_info"]["version"].startsWith("4"))
//             ? `<ul class="usa-list usa-list--unstyled">
//                 <li>Event Type: ${feature.properties.core_details.event_type}</li>
//                 <li>Roads: ${feature.properties.core_details.road_names}</li>
//                 <li>Direction: ${feature.properties.core_details.direction}</li>
//                 <li>Start Date: ${feature.properties.start_date}</li>
//                 <li>End Date: ${feature.properties.end_date}</li>
//                 <li>Vehicle Impact: ${feature.properties.vehicle_impact}</li>
//                 </ul>
//                 `
//             : `<ul class="usa-list usa-list--unstyled">
//                 <li>Event Type: ${feature.properties.event_type}</li>
//                 <li>Roads: ${feature.properties.road_names}</li>
//                 <li>Direction: ${feature.properties.direction}</li>
//                 <li>Start Date: ${feature.properties.start_date}</li>
//                 <li>End Date: ${feature.properties.end_date}</li>
//                 <li>Vehicle Impact: ${feature.properties.vehicle_impact}</li>
//                 </ul>
//                 `
//         );
//       },
//     }).addTo(layerGroup);
//   }

//   map.fitBounds(layerGroup.getBounds());
// }
