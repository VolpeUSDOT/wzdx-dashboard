const US_CENTER = [-103.771556, 44.967243];

const BASEMAP_URL =
  "https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json";

/**
 *
 * @param {string} container
 * @param {[number, number]} coords
 * @param {string} version
 * @param {string} points_url
 */
function makeMap(container, coords, version, points_url) {
  const map = new maplibregl.Map({
    container: container, // container id
    style: BASEMAP_URL, // style URL
    center: coords ?? US_CENTER, // starting position [lng, lat]
    zoom: 4, // starting zoom
  });

  map.addControl(
    new maplibregl.FullscreenControl({
      container: document.querySelector(container),
    })
  );

  map.on("load", async () => {
    const resp = await fetch(points_url);
    const data = await resp.json();

    const feed_data = data["feed_data"];

    map.addSource("geojson-source", {
      type: "geojson",
      data: feed_data,
    });

    map.addLayer({
      id: "geojson-lines",
      type: "line",
      source: "geojson-source",
      filter: ["==", "$type", "LineString"],
      layout: {
        "line-join": "round",
        "line-cap": "round",
      },
      paint: {
        "line-width": 4,
      },
    });

    map.addLayer({
      id: "geojson-points",
      type: "circle",
      source: "geojson-source",
      filter: ["==", "$type", "Point"],
      paint: {
        "circle-radius": 4,
      },
    });

    map.on("click", "geojson-points", (e) => {
      console.log(e.features[0].properties);
      const coordinates = e.features[0].geometry.coordinates.slice();

      let description;

      if (version.startsWith("4")) {
        const core_details = JSON.parse(e.features[0].properties.core_details);
        description = `<ul class="usa-list usa-list--unstyled">
        <li>Event Type: ${core_details.event_type}</li>
        <li>Roads: ${core_details.road_names}</li>
        <li>Direction: ${core_details.direction}</li>
        <li>Start Date: ${e.features[0].properties.start_date}</li>
        <li>End Date: ${e.features[0].properties.end_date}</li>
        <li>Vehicle Impact: ${e.features[0].properties.vehicle_impact}</li>
        </ul>
        `;
      } else {
        description = `<ul class="usa-list usa-list--unstyled">
        <li>Event Type: ${e.features[0].properties.event_type}</li>
        <li>Roads: ${e.features[0].properties.road_names}</li>
        <li>Direction: ${e.features[0].properties.direction}</li>
        <li>Start Date: ${e.features[0].properties.start_date}</li>
        <li>End Date: ${e.features[0].properties.end_date}</li>
        <li>Vehicle Impact: ${e.features[0].properties.vehicle_impact}</li>
        </ul>
        `;
      }

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

    map.on("click", "geojson-lines", (e) => {
      const coordinates = e.lngLat;

      let description;

      if (version.startsWith("4")) {
        const core_details = JSON.parse(e.features[0].properties.core_details);
        description = `<ul class="usa-list usa-list--unstyled">
        <li>Event Type: ${core_details.event_type}</li>
        <li>Roads: ${core_details.road_names}</li>
        <li>Direction: ${core_details.direction}</li>
        <li>Start Date: ${e.features[0].properties.start_date}</li>
        <li>End Date: ${e.features[0].properties.end_date}</li>
        <li>Vehicle Impact: ${e.features[0].properties.vehicle_impact}</li>
        </ul>
        `;
      } else {
        description = `<ul class="usa-list usa-list--unstyled">
        <li>Event Type: ${e.features[0].properties.event_type}</li>
        <li>Roads: ${e.features[0].properties.road_names}</li>
        <li>Direction: ${e.features[0].properties.direction}</li>
        <li>Start Date: ${e.features[0].properties.start_date}</li>
        <li>End Date: ${e.features[0].properties.end_date}</li>
        <li>Vehicle Impact: ${e.features[0].properties.vehicle_impact}</li>
        </ul>
        `;
      }

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
