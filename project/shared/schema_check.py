import json
import os
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

import requests
from jsonschema import Draft7Validator, ValidationError
from jsonschema.exceptions import best_match
from referencing import Registry, Resource

SCHEMA_FOLDER = Path(os.path.dirname(__file__)) / "schemas"

VERSION_TO_SCHEMA = {
    "4.2": "https://raw.githubusercontent.com/usdot-jpo-ode/wzdx/main/schemas/4.2/WorkZoneFeed.json",
    "4.1": "https://raw.githubusercontent.com/usdot-jpo-ode/wzdx/main/schemas/4.1/WorkZoneFeed.json",
    "4.0": "https://raw.githubusercontent.com/usdot-jpo-ode/wzdx/main/schemas/4.0/WZDxFeed.json",
    "3.1": "https://raw.githubusercontent.com/usdot-jpo-ode/wzdx/main/schemas/3.1/WZDxFeed.json",
    "3.0": "https://raw.githubusercontent.com/usdot-jpo-ode/wzdx/main/schemas/3.0/WZDxFeed.json",
    "2.0": "https://raw.githubusercontent.com/usdot-jpo-ode/wzdx/main/schemas/2.0/WZDxFeed.json",
    # TODO: HANDLE NON-WZDX FEEDS (CWZ)
}


def get_schema_json(filename: str):
    with open(SCHEMA_FOLDER / filename, "r") as f:
        return json.load(f)


def retrieve_via_web(uri: str):
    print(f"requesting {uri}...")
    response = requests.get(uri)
    return Resource.from_contents(response.json())


def format_as_index(container: str, indices: Sequence):
    """Construct a single string containing indexing operations for the indices."""
    if not indices:
        return container
    return f"{container}[{']['.join(repr(index) for index in indices)}]"


def find_all_instances_key(
    obj: dict[str, Any], key: str, key_to_skip: Optional[str] = None
):
    if key in obj:
        yield obj[key]
    for k, v in obj.items():
        if (k is None or k != key_to_skip) and isinstance(v, dict):
            item = find_all_instances_key(v, key, key_to_skip)
            if item:
                yield from item


def get_formatted_errors(errors: list[ValidationError], feedname: str):

    for error in errors:
        if error.context is None or len(error.context) == 0:
            # No sub errors
            yield (error.message, format_as_index(feedname, error.path))
        else:
            # Get most relevant suberror, save that
            best_error: ValidationError = best_match(error.context)
            if type(best_error) is ValidationError:
                yield (
                    best_error.message,
                    format_as_index(
                        format_as_index(feedname, error.path),
                        best_error.path,
                    ),
                )


# GET ALL SCHEMAS AND SAVE IN REGISTRY (minimizes time to analyze schema)
REGISTRY = Registry(retrieve=retrieve_via_web).with_resources(
    [
        (
            "https://raw.githubusercontent.com/ite-org/cwz/refs/heads/main/schemas/1.0/WorkZoneFeed.json",
            Resource.from_contents(get_schema_json("cwz10.schema.json")),
        ),
        (
            "https://raw.githubusercontent.com/usdot-jpo-ode/wzdx/main/schemas/4.2/WorkZoneFeed.json",
            Resource.from_contents(get_schema_json("wzdx42.schema.json")),
        ),
        (
            "https://raw.githubusercontent.com/usdot-jpo-ode/wzdx/main/schemas/4.1/WorkZoneFeed.json",
            Resource.from_contents(get_schema_json("wzdx41.schema.json")),
        ),
        (
            "https://raw.githubusercontent.com/usdot-jpo-ode/wzdx/main/schemas/4.0/WZDxFeed.json",
            Resource.from_contents(get_schema_json("wzdx40.schema.json")),
        ),
        (
            "https://raw.githubusercontent.com/usdot-jpo-ode/wzdx/main/schemas/3.1/WZDxFeed.json",
            Resource.from_contents(get_schema_json("wzdx31.schema.json")),
        ),
        (
            "https://raw.githubusercontent.com/usdot-jpo-ode/wzdx/main/schemas/2.0/WZDxFeed.json",
            Resource.from_contents(get_schema_json("wzdx30.schema.json")),
        ),
        (
            "https://raw.githubusercontent.com/usdot-jpo-ode/wzdx/main/schemas/2.0/WZDxFeed.json",
            Resource.from_contents(get_schema_json("wzdx20.schema.json")),
        ),
    ]
)


def get_version_schema_errors(data: Any, version: str) -> list[ValidationError]:
    """If feed data fails to validate against JSON schema (with schema version)"""

    return get_schema_errors(data, {"$ref": VERSION_TO_SCHEMA[version]})


def get_schema_errors(
    data: Any, schema: Mapping[str, Any] | bool
) -> list[ValidationError]:
    """If feed data fails to validate against JSON schema (with schema version)"""

    v = Draft7Validator(schema, registry=REGISTRY)

    return sorted(v.iter_errors(data), key=str)
