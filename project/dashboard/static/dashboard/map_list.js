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
 * LegendControl: A small MapLibre custom control that displays a legend.
 * - items: [{ color: "#fff", label: "text" }, ...]
 * - options: { title: "Legend", position: "bottom-left" } (position is passed to map.addControl)
 *
 * Using a MapLibre control ensures the legend behaves like native map controls
 * (z-ordering, positioning, and consistent CSS handling).
 */
class LegendControl {
  constructor(items = [], options = {}) {
    this._items = items;
    this._options = options || {};
    this._container = null;
  }

  onAdd(map) {
    this._map = map;

    // Create wrapper
    const container = document.createElement("div");
    container.className = "maplibre-legend-control maplibre-ctrl";
    // Minimal styling; you can move this into a stylesheet later
    container.style.background = "rgba(255,255,255,0.95)";
    container.style.padding = "8px 10px";
    container.style.borderRadius = "4px";
    container.style.boxShadow = "0 1px 4px rgba(0,0,0,0.2)";
    container.style.fontSize = "13px";
    container.style.maxWidth = "220px";
    container.style.overflow = "auto";

    // Optional title
    if (this._options.title) {
      const title = document.createElement("div");
      title.textContent = this._options.title;
      title.style.fontWeight = "600";
      title.style.marginBottom = "6px";
      container.appendChild(title);
    }

    // Add items
    this._items.forEach((it) => {
      const row = document.createElement("div");
      row.style.display = "flex";
      row.style.alignItems = "center";
      row.style.marginBottom = "6px";

      const swatch = document.createElement("span");
      swatch.style.width = it.swatchSize ? it.swatchSize + "px" : "12px";
      swatch.style.height = it.swatchSize ? it.swatchSize + "px" : "12px";
      swatch.style.background = it.color || "#000";
      swatch.style.display = "inline-block";
      swatch.style.marginRight = "8px";
      swatch.style.flex = "0 0 auto";
      if (it.shape === "circle") {
        swatch.style.borderRadius = "50%";
      } else if (it.shape === "rounded") {
        swatch.style.borderRadius = "3px";
      } // else square by default

      const lbl = document.createElement("span");
      lbl.textContent = it.label || "";
      lbl.style.whiteSpace = "nowrap";
      lbl.style.overflow = "hidden";
      lbl.style.textOverflow = "ellipsis";

      row.appendChild(swatch);
      row.appendChild(lbl);
      container.appendChild(row);
    });

    this._container = container;
    return container;
  }

  onRemove() {
    if (this._container && this._container.parentNode) {
      this._container.parentNode.removeChild(this._container);
    }
    this._map = undefined;
  }

  // Optional: allow updating legend items programmatically
  setItems(items) {
    this._items = items || [];
    if (this._container && this._map) {
      // re-render: remove all children and rebuild
      while (this._container.firstChild)
        this._container.removeChild(this._container.firstChild);
      if (this._options.title) {
        const title = document.createElement("div");
        title.textContent = this._options.title;
        title.style.fontWeight = "600";
        title.style.marginBottom = "6px";
        this._container.appendChild(title);
      }
      this._items.forEach((it) => {
        const row = document.createElement("div");
        row.style.display = "flex";
        row.style.alignItems = "center";
        row.style.marginBottom = "6px";

        const swatch = document.createElement("span");
        swatch.style.width = it.swatchSize ? it.swatchSize + "px" : "12px";
        swatch.style.height = it.swatchSize ? it.swatchSize + "px" : "12px";
        swatch.style.background = it.color || "#000";
        swatch.style.display = "inline-block";
        swatch.style.marginRight = "8px";
        swatch.style.flex = "0 0 auto";
        if (it.shape === "circle") {
          swatch.style.borderRadius = "50%";
        } else if (it.shape === "rounded") {
          swatch.style.borderRadius = "3px";
        }

        const lbl = document.createElement("span");
        lbl.textContent = it.label || "";
        lbl.style.whiteSpace = "nowrap";
        lbl.style.overflow = "hidden";
        lbl.style.textOverflow = "ellipsis";

        row.appendChild(swatch);
        row.appendChild(lbl);
        this._container.appendChild(row);
      });
    }
  }
}

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
function stringToHexCode(string, saturation = 100, lightness = 45) {
  let hash = 0;
  for (let i = 0; i < string.length; i++) {
    hash = string.charCodeAt(i) + ((hash << 5) - hash);
    hash = hash & hash;
  }
  return `hsl(${hash % 360}, ${saturation}%, ${lightness}%)`;
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
    (
      await Promise.all(
        feeds.map(async (feed) => {
          const points_url = `/api/feeds/${feed}`;
          const layer_source = `geojson-source-${feed}`;
          const layer_points = `geojson-points-${feed}`;
          const layer_lines = `geojson-lines-${feed}`;

          const resp = await fetch(points_url);
          const data = await resp.json();

          const feed_data = data["feed_data"];

          if (Object.keys(feed_data).length === 0) {
            return;
          }

          /** @type {[string, string, string, string, any]} */
          const return_data = [
            feed,
            layer_source,
            layer_points,
            layer_lines,
            feed_data,
          ];

          return return_data;
        })
      )
    ).forEach((data) => {
      if (!data) {
        return;
      }

      const [feed, layer_source, layer_points, layer_lines, feed_data] = data;

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
        const coordinates = e.lngLat;
        let description = `<a class="usa-link" href="${feed}">View feed (${feed})</a>`;

        if (e.features[0].properties.core_details) {
          const core_details = JSON.parse(
            e.features[0].properties.core_details
          );
          description += `<ul class="usa-list usa-list--unstyled">
        <li>ID: ${e.features[0].id} </li>
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
        <li>ID: ${e.features[0].id} </li>
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
        <li>ID: ${e.features[0].id} </li>
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
        <li>ID: ${e.features[0].id} </li>        
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

    // ------------------------
    // Legend: Events Map (as a MapLibre control)
    // Purpose: Use MapLibre control API to show each feed color; colors come from stringToHexCode(feed).
    // ------------------------
    // Build unique feed list in the same order as the input feeds array (filtering out empty entries).
    const uniqueFeeds = [];
    feeds.forEach((f) => {
      if (f && !uniqueFeeds.includes(f)) uniqueFeeds.push(f);
    });

    const eventsLegendItems = uniqueFeeds.length
      ? uniqueFeeds.map((feed) => ({
          color: stringToHexCode(feed),
          label: feed,
          shape: "rounded",
          swatchSize: 12,
        }))
      : [{ color: "#666", label: "No feeds available" }];

    const eventsLegendControl = new LegendControl(eventsLegendItems, {
      title: "Feeds Legend",
    });
    // Place it in top-right; change position if desired
    map.addControl(eventsLegendControl, "top-right");
    // ------------------------
    // End events legend (MapLibre control)
    // ------------------------
  });
}
