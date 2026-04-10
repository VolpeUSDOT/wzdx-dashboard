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
      let color = "#005ea2";
      if (/^"/.test(match)) {
        if (/:$/.test(match)) {
          color = "#e52207";
        } else {
          color = "#538200";
        }
      } else if (/true|false/.test(match)) {
        color = "#b35c00";
      } else if (/null/.test(match)) {
        color = "#888888";
      }
      return `<span style="color: ${color}; font-weight: ${/^"/.test(match) && /:$/.test(match) ? "bold" : "normal"};">${match}</span>`;
    },
  );
}

function makeValidationMap(containerId) {
  const feedData = JSON.parse(document.getElementById("map-data").textContent);
  const mapErrors = JSON.parse(
    document.getElementById("map-errors").textContent,
  );

  if (feedData.features) {
    const extraFeatures = [];

    feedData.features.forEach((feature, index) => {
      const featureId =
        (feature.properties && feature.properties.id) ||
        feature.id ||
        String(index);
      feature.id = featureId;

      if (!feature.properties) feature.properties = {};

      // Flag errors
      if (mapErrors[featureId]) {
        feature.properties.has_errors = true;
        feature.properties.schema_errors = JSON.stringify(mapErrors[featureId]);
      } else {
        feature.properties.has_errors = false;
      }

      // --- MULTIPOINT CONNECTOR LOGIC ---
      if (feature.geometry && feature.geometry.type === "MultiPoint") {
        extraFeatures.push({
          type: "Feature",
          id: featureId + "_connector", // Ensure unique ID for MapLibre
          properties: {
            ...feature.properties, // Inherits the has_errors flag perfectly!
            is_connector: true,
          },
          geometry: {
            type: "LineString",
            coordinates: feature.geometry.coordinates,
          },
        });
      }
    });

    // Append the new connector lines to the data
    feedData.features.push(...extraFeatures);
  }

  const map = new maplibregl.Map({
    container: containerId,
    style: BASEMAP_URL,
    center: US_CENTER,
    zoom: 4,
  });

  map.addControl(new maplibregl.FullscreenControl());

  map.on("load", () => {
    map.addSource("geojson-source", {
      type: "geojson",
      data: feedData,
      promoteId: "id",
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
        "line-width": 2,
        "line-dasharray": [2, 2],
        // Red if error, dark gray if valid
        "line-color": [
          "case",
          ["==", ["get", "has_errors"], true],
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
      layout: { "line-join": "round", "line-cap": "round" },
      paint: {
        "line-width": 5,
        "line-color": [
          "case",
          ["==", ["get", "has_errors"], true],
          "#e52207",
          "#005ea2",
        ],
      },
    });

    // 3. Points (and MultiPoints)
    map.addLayer({
      id: "geojson-points",
      type: "circle",
      source: "geojson-source",
      filter: ["==", "$type", "Point"],
      paint: {
        "circle-radius": 6,
        "circle-color": [
          "case",
          ["==", ["get", "has_errors"], true],
          "#e52207",
          "#005ea2",
        ],
        "circle-stroke-width": 1,
        "circle-stroke-color": "#ffffff",
      },
    });

    // Popups
    const handleFeatureClick = (e) => {
      const feature = e.features[0];
      const coordinates = e.lngLat;
      let description = "";

      if (feature.properties.has_errors) {
        const errorsList = JSON.parse(feature.properties.schema_errors);
        const errorItems = errorsList.map((err) => `<li>${err}</li>`).join("");

        description += `
                    <div style="background-color: #f8dfeb; border-left: 4px solid #e52207; padding: 10px; margin-bottom: 10px;">
                        <strong style="color: #e52207;">Schema Validation Errors:</strong>
                        <ul style="margin: 5px 0 0 0; padding-left: 20px; font-size: 12px; color: #b31b04;">
                            ${errorItems}
                        </ul>
                    </div>
                `;
      } else {
        description += `
                    <div style="background-color: #e7f4e4; border-left: 4px solid #538200; padding: 10px; margin-bottom: 10px;">
                        <strong style="color: #538200;">Valid Feature</strong>
                    </div>
                `;
      }

      const cleanProperties = { ...feature.properties };

      // Clean up drawing flags
      delete cleanProperties.has_errors;
      delete cleanProperties.schema_errors;
      delete cleanProperties.is_connector;

      if (
        cleanProperties.road_event_core_details &&
        typeof cleanProperties.road_event_core_details === "string"
      ) {
        try {
          cleanProperties.road_event_core_details = JSON.parse(
            cleanProperties.road_event_core_details,
          );
        } catch (err) {}
      }
      if (
        cleanProperties.core_details &&
        typeof cleanProperties.core_details === "string"
      ) {
        try {
          cleanProperties.core_details = JSON.parse(
            cleanProperties.core_details,
          );
        } catch (err) {}
      }

      // Strip the "_connector" suffix off the ID for the raw output if they clicked the dashed line
      let displayId = cleanProperties.id || feature.id;
      if (typeof displayId === "string" && displayId.endsWith("_connector")) {
        displayId = displayId.replace("_connector", "");
      }

      // Reconstruct the original geometry for the raw view if they clicked the connector line
      const displayGeometry = feature.properties.is_connector
        ? { type: "MultiPoint", coordinates: feature.geometry.coordinates }
        : feature.geometry;

      const rawFeature = {
        id: displayId,
        type: "Feature",
        geometry: displayGeometry,
        properties: cleanProperties,
      };

      const highlightedJSON = syntaxHighlight(rawFeature);

      description += `
                <details open style="margin-top: 1rem; border-top: 1px solid #ccc; padding-top: 0.5rem;">
                  <summary style="cursor: pointer; font-weight: bold; color: #005ea2;">View Raw Feature</summary>
                  <pre style="background: #f4f4f4; padding: 10px; border-radius: 4px; overflow-y: auto; max-height: 250px; font-size: 12px; margin-top: 0.5rem;"><code>${highlightedJSON}</code></pre>
                </details>
            `;

      new maplibregl.Popup({ maxWidth: "400px" })
        .setLngLat(coordinates)
        .setHTML(description)
        .addTo(map);
    };

    map.on("click", "geojson-points", handleFeatureClick);
    map.on("click", "geojson-lines", handleFeatureClick);
    map.on("click", "geojson-multipoint-lines", handleFeatureClick); // Add click handler for connectors

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
    map.on(
      "mouseenter",
      "geojson-multipoint-lines",
      () => (map.getCanvas().style.cursor = "pointer"),
    );
    map.on(
      "mouseleave",
      "geojson-multipoint-lines",
      () => (map.getCanvas().style.cursor = ""),
    );

    map
      .getSource("geojson-source")
      .getBounds()
      .then((bounds) => map.fitBounds(bounds, { padding: 50 }));
  });
}
