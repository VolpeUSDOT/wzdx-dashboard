const US_CENTER = [-103.771556, 44.967243];

const BASEMAP_URL =
  "https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json";

/**
 * Simple JSON syntax highlighter
 * @param {object|string} json
 * @returns {string} HTML string with inline styles for colors
 */
function syntaxHighlight(json) {
  if (typeof json != "string") {
    json = JSON.stringify(json, undefined, 2);
  }
  json = json
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
  return json.replace(
    /("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g,
    function (match) {
      let color = "#005ea2"; // Default number color (blue)
      if (/^"/.test(match)) {
        if (/:$/.test(match)) {
          color = "#e52207"; // Key color (red)
        } else {
          color = "#538200"; // String color (green)
        }
      } else if (/true|false/.test(match)) {
        color = "#b35c00"; // Boolean color (orange)
      } else if (/null/.test(match)) {
        color = "#888888"; // Null color (gray)
      }
      return `<span style="color: ${color}; font-weight: ${/^"/.test(match) && /:$/.test(match) ? "bold" : "normal"};">${match}</span>`;
    },
  );
}

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
    }),
  );

  let clickedFeatureId = null;

  // Helper function to clear the highlighted feature
  function clearHighlight() {
    if (clickedFeatureId !== null) {
      map.setFeatureState(
        { source: "geojson-source", id: clickedFeatureId },
        { clicked: false },
      );
      clickedFeatureId = null;
    }
  }

  map.on("load", async () => {
    const resp = await fetch(points_url);
    const data = await resp.json();

    const feed_data = data["feed_data"];

    if (Object.keys(feed_data).length === 0) {
      return;
    }

    // --- TRANSFORMATION STEP FOR MULTIPOINT LINES ---
    // GeoJSON cannot draw lines between MultiPoints natively.
    // We create secondary LineString features specifically for drawing thin connectors.
    if (feed_data.features) {
      const extraFeatures = [];
      feed_data.features.forEach((feature) => {
        if (feature.geometry && feature.geometry.type === "MultiPoint") {
          extraFeatures.push({
            type: "Feature",
            id: feature.id, // Share the ID so highlighting works on both the points and the line simultaneously
            properties: { ...feature.properties, is_connector: true },
            geometry: {
              type: "LineString",
              coordinates: feature.geometry.coordinates,
            },
          });
        }
      });
      feed_data.features.push(...extraFeatures);
    }

    map.addSource("geojson-source", {
      type: "geojson",
      data: feed_data,
      promoteId: "ID_for_dashboard", // Promotes it safely!
    });

    // 1. Thin dashed lines for MultiPoint connectors
    map.addLayer({
      id: "geojson-multipoint-lines",
      type: "line",
      source: "geojson-source",
      filter: ["==", "is_connector", true],
      layout: {
        "line-join": "round",
        "line-cap": "round",
      },
      paint: {
        "line-width": [
          "case",
          ["boolean", ["feature-state", "clicked"], false],
          2,
          1,
        ],
        "line-dasharray": [2, 2],
        "line-color": [
          "case",
          ["boolean", ["feature-state", "clicked"], false],
          "#e52207",
          "#555555",
        ],
      },
    });

    // 2. Standard solid lines for LineStrings
    map.addLayer({
      id: "geojson-lines",
      type: "line",
      source: "geojson-source",
      filter: [
        "all",
        ["==", "$type", "LineString"],
        ["!=", "is_connector", true],
      ],
      layout: {
        "line-join": "round",
        "line-cap": "round",
      },
      paint: {
        "line-width": [
          "case",
          ["boolean", ["feature-state", "clicked"], false],
          6,
          4,
        ],
        "line-color": [
          "case",
          ["boolean", ["feature-state", "clicked"], false],
          "#e52207",
          "#005ea2",
        ],
      },
    });

    // 3. Directional Arrows for LineStrings
    map.addLayer({
      id: "geojson-line-arrows",
      type: "symbol",
      source: "geojson-source",
      filter: [
        "all",
        ["==", "$type", "LineString"],
        ["!=", "is_connector", true],
      ],
      layout: {
        "symbol-placement": "line",
        "symbol-spacing": 100,
        "text-field": "▶",
        "text-font": ["Open Sans Regular", "Arial Unicode MS Regular"],
        "text-size": 14,
        "text-allow-overlap": true,
        "text-ignore-placement": true,
        "text-keep-upright": false,
      },
      paint: {
        "text-color": [
          "case",
          ["boolean", ["feature-state", "clicked"], false],
          "#e52207",
          "#ffffff",
        ],
        "text-halo-color": "#000000",
        "text-halo-width": 1,
      },
    });

    // 4. Points (and MultiPoints)
    map.addLayer({
      id: "geojson-points",
      type: "circle",
      source: "geojson-source",
      filter: ["==", "$type", "Point"],
      paint: {
        "circle-radius": [
          "case",
          ["boolean", ["feature-state", "clicked"], false],
          8,
          5,
        ],
        "circle-color": [
          "case",
          ["boolean", ["feature-state", "clicked"], false],
          "#e52207",
          "#005ea2",
        ],
        "circle-stroke-width": 1,
        "circle-stroke-color": "#ffffff",
      },
    });

    // --- INTERACTIVITY HANDLERS ---

    // Clear highlight when clicking on the map background
    map.on("click", (e) => {
      const features = map.queryRenderedFeatures(e.point, {
        layers: ["geojson-points", "geojson-lines", "geojson-multipoint-lines"],
      });
      if (!features.length) {
        clearHighlight();
      }
    });

    // Function to handle clicking a feature (shared for points and lines)
    const handleFeatureClick = (e) => {
      if (!e.features.length) return;

      const feature = e.features[0];
      const coordinates = e.lngLat;

      // Handle Highlighting
      if (feature.id !== undefined) {
        clearHighlight();
        clickedFeatureId = feature.id;
        map.setFeatureState(
          { source: "geojson-source", id: clickedFeatureId },
          { clicked: true },
        );
      } else {
        console.warn(
          "Clicked feature has no top-level ID. Highlighting will not work.",
          feature,
        );
      }

      // Handle Description HTML
      let description;
      let props = feature.properties;

      // Check if the feature actually has a core_details property!
      if (props.core_details) {
        const core_details =
          typeof props.core_details === "string"
            ? JSON.parse(props.core_details)
            : props.core_details;

        description = `<ul class="usa-list usa-list--unstyled">
        <li>ID: ${feature.id || "N/A"}</li>
        <li>Event Type: ${core_details.event_type || "N/A"}</li>
        <li>Roads: ${core_details.road_names || "N/A"}</li>
        <li>Direction: ${core_details.direction || "N/A"}</li>
        <li>Start Date: ${props.start_date || "N/A"}</li>
        <li>End Date: ${props.end_date || "N/A"}</li>
        <li>Vehicle Impact: ${props.vehicle_impact || "N/A"}</li>
        </ul>`;
      } else {
        description = `<ul class="usa-list usa-list--unstyled">
        <li>ID: ${feature.id || "N/A"}</li>
        <li>Event Type: ${props.event_type || "N/A"}</li>
        <li>Roads: ${props.road_names || "N/A"}</li>
        <li>Direction: ${props.direction || "N/A"}</li>
        <li>Start Date: ${props.start_date || "N/A"}</li>
        <li>End Date: ${props.end_date || "N/A"}</li>
        <li>Vehicle Impact: ${props.vehicle_impact || "N/A"}</li>
        </ul>`;
      }

      // --- ADD THE RAW JSON DUMP HERE ---
      // Generate the syntax-highlighted HTML string
      const highlightedJSON = syntaxHighlight(feature);

      // Append it inside a collapsible details tag with a scrolling pre block
      description += `
        <details style="margin-top: 1rem; border-top: 1px solid #ccc; padding-top: 0.5rem;">
          <summary style="cursor: pointer; font-weight: bold; color: #005ea2;">View Raw Feature</summary>
          <pre style="background: #f4f4f4; padding: 10px; border-radius: 4px; overflow-y: auto; max-height: 200px; font-size: 12px; margin-top: 0.5rem;"><code>${highlightedJSON}</code></pre>
        </details>
      `;

      while (Math.abs(e.lngLat.lng - coordinates[0]) > 180) {
        coordinates[0] += e.lngLat.lng > coordinates[0] ? 360 : -360;
      }

      const popup = new maplibregl.Popup()
        .setLngLat(coordinates)
        .setHTML(description)
        .addTo(map);

      // Optional: Clear highlight if user clicks the 'X' on the popup
      popup.on("close", clearHighlight);
    };

    map.on("click", "geojson-points", handleFeatureClick);
    map.on("click", "geojson-lines", handleFeatureClick);

    // Change cursor to pointer on hover
    map.on(
      "mouseenter",
      "geojson-points",
      () => (map.getCanvas().style.cursor = "pointer"),
    );
    map.on(
      "mouseleave",
      "geojson-points",
      () => (map.getCanvas().style.cursor = ""),
    );
    map.on(
      "mouseenter",
      "geojson-lines",
      () => (map.getCanvas().style.cursor = "pointer"),
    );
    map.on(
      "mouseleave",
      "geojson-lines",
      () => (map.getCanvas().style.cursor = ""),
    );

    map
      .getSource("geojson-source")
      .getBounds()
      .then((bounds) => map.fitBounds(bounds, { padding: 50 }));
  });
}
