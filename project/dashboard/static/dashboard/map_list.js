const STATUS_TYPES = {
  NA: "null",
  OK: "ok",
  ER: "error",
  OU: "outdated",
  ST: "stale",
  OF: "offline",
};

const US_CENTER = [-103.771556, 44.967243];

const BASEMAP_URL =
  "https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json";

/**
 *
 * @param {string} container
 */
async function makeFeedsMap(container) {
  const map = new maplibregl.Map({
    container: container, // container id
    style: BASEMAP_URL, // style URL
    center: US_CENTER, // starting position [lng, lat]
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

    const bounds = await map.getSource("geojson-source").getBounds();
    map.fitBounds(bounds, { padding: 20 });
  });
}

/**
 *
 * @param {string} str
 * @returns hex code
 */
function stringToHexCode(str) {
  let hash = 0;
  if (str.length === 0) return hash;
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
    hash = hash & hash;
  }
  let color = "#";
  for (let i = 0; i < 3; i++) {
    let value = (hash >> (i * 8)) & 255;
    color += ("00" + value.toString(16)).slice(-2);
  }
  return color;
}

/**
 *
 * @param {string} container
 * @param {string[]} feeds
 */
async function makeEventsMap(container, feeds) {
  const map = new maplibregl.Map({
    container: container, // container id
    style: BASEMAP_URL, // style URL
    center: US_CENTER, // starting position [lng, lat]
    zoom: 1, // starting zoom
  });

  map.addControl(
    new maplibregl.FullscreenControl({
      container: document.querySelector(container),
    })
  );

  map.on("load", async () => {
    await Promise.all(
      feeds.map((feed) => {
        const points_url = `/api/feeds/${feed}`;
        const layer_source = `geojson-source-${feed}`;
        const layer_points = `geojson-points-${feed}`;
        const layer_lines = `geojson-lines-${feed}`;

        return fetch(points_url)
          .then((resp) => resp.json())
          .then((data) => {
            const feed_data = data["feed_data"];

            map.addSource(layer_source, {
              type: "geojson",
              data: feed_data,
            });

            map.addLayer({
              id: layer_lines,
              type: "line",
              source: layer_source,
              filter: ["==", "$type", "LineString"],
              layout: {
                "line-join": "round",
                "line-cap": "round",
              },
              paint: {
                "line-width": 4,
                "line-color": stringToHexCode(feed),
              },
            });

            map.addLayer({
              id: layer_points,
              type: "circle",
              source: layer_source,
              filter: ["==", "$type", "Point"],
              paint: {
                "circle-radius": 4,
                "circle-color": stringToHexCode(feed),
              },
            });

            map.on("click", layer_points, (e) => {
              const coordinates = e.features[0].geometry.coordinates.slice();

              let description = `<a class="usa-link" href="${feed}">View feed (${feed})</a>`;

              if (e.features[0].properties.core_details) {
                const core_details = JSON.parse(
                  e.features[0].properties.core_details
                );
                description += `<ul class="usa-list usa-list--unstyled">
        <li>Event Type: ${core_details.event_type}</li>
        <li>Roads: ${core_details.road_names}</li>
        <li>Direction: ${core_details.direction}</li>
        <li>Start Date: ${e.features[0].properties.start_date}</li>
        <li>End Date: ${e.features[0].properties.end_date}</li>
        <li>Vehicle Impact: ${e.features[0].properties.vehicle_impact}</li>
        </ul>
        `;
              } else {
                description += `<ul class="usa-list usa-list--unstyled">
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

            map.on("click", layer_lines, (e) => {
              const coordinates = e.lngLat;

              let description = `<a class="usa-link" href="${feed}">View feed (${feed})</a>`;

              if (e.features[0].properties.core_details) {
                const core_details = JSON.parse(
                  e.features[0].properties.core_details
                );
                description += `<ul class="usa-list usa-list--unstyled">
        <li>Event Type: ${core_details.event_type}</li>
        <li>Roads: ${core_details.road_names}</li>
        <li>Direction: ${core_details.direction}</li>
        <li>Start Date: ${e.features[0].properties.start_date}</li>
        <li>End Date: ${e.features[0].properties.end_date}</li>
        <li>Vehicle Impact: ${e.features[0].properties.vehicle_impact}</li>
        </ul>
        `;
              } else {
                description += `<ul class="usa-list usa-list--unstyled">
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
          });
      })
    );
  });
}
