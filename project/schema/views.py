import json
from typing import Any

from django.shortcuts import render
from shared.schema_check import get_version_schema_errors

from .forms import SchemaForm


def index(request):
    context: dict[str, Any] = {}

    if request.method == "POST":
        form = SchemaForm(request.POST)
        if form.is_valid():
            feed_data = json.loads(form.cleaned_data["feed_data"])

            # This returns a list of jsonschema.exceptions.ValidationError objects
            raw_errors = get_version_schema_errors(
                feed_data, form.cleaned_data["version"]
            )

            structured_errors = {}
            general_errors = []

            for error in raw_errors:
                path = list(error.path)

                # Check if the error is inside a specific feature in the 'features' array
                if (
                    len(path) >= 2
                    and path[0] == "features"
                    and isinstance(path[1], int)
                ):
                    feature_idx = path[1]
                    feature = feed_data["features"][feature_idx]

                    # Try to get top-level ID, fallback to properties.id, fallback to index
                    feature_id = feature.get(
                        "id", feature.get("properties", {}).get("id", str(feature_idx))
                    )

                    if feature_id not in structured_errors:
                        structured_errors[feature_id] = []

                    failed_field = path[-1] if len(path) > 2 else "feature"

                    # --- NEW LOGIC: Unpack nested context errors ---
                    if error.context:
                        # Iterate through the deeper reasons the schema failed
                        for sub_err in error.context:
                            sub_path = list(sub_err.path)

                            # Grab the specific nested field that failed, if available
                            specific_field = sub_path[-1] if sub_path else failed_field

                            # Filter out redundant "not valid under any schema" noise
                            if (
                                "is not valid under any of the given schemas"
                                not in sub_err.message
                            ):
                                structured_errors[feature_id].append(
                                    f"[{failed_field} -> {specific_field}]: {sub_err.message}"
                                )

                        # If filtering left us with nothing, provide a fallback
                        if not structured_errors[feature_id]:
                            structured_errors[feature_id].append(
                                f"[{failed_field}]: Sub-schema validation failed."
                            )
                    else:
                        # Standard top-level error (e.g., missing 'geometry')
                        structured_errors[feature_id].append(
                            f"[{failed_field}]: {error.message}"
                        )
                else:
                    general_errors.append(error.message)

            context["general_errors"] = general_errors or (
                ["No general schema errors!"] if not structured_errors else []
            )
            context["structured_errors"] = structured_errors
            context["feed_data"] = (
                feed_data  # Pass the data to the template for the map!
            )

    else:
        form = SchemaForm()

    context["form"] = form
    return render(request, "schema/index.html", context)
