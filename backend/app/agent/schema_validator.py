"""Validate content packs with both Pydantic models and JSON Schema."""

import json
from jsonschema import validate as jsonschema_validate
from jsonschema.exceptions import ValidationError as JsonSchemaValidationError

from app.models import ContentPack
from app.core.paths import CONTENT_PACK_SCHEMA_PATH


def validate_with_pydantic(content_pack: dict) -> ContentPack:
    """
    Validate and parse a dict into a ContentPack Pydantic model.
    Raises pydantic.ValidationError on failure.
    """
    return ContentPack.model_validate(content_pack)


def validate_with_json_schema(content_pack: dict) -> None:
    """
    Validate a dict against the JSON Schema file.
    Raises ValueError on failure.
    """
    if not CONTENT_PACK_SCHEMA_PATH.exists():
        raise FileNotFoundError(
            f"Schema file not found: {CONTENT_PACK_SCHEMA_PATH}"
        )

    schema = json.loads(CONTENT_PACK_SCHEMA_PATH.read_text(encoding="utf-8"))

    try:
        jsonschema_validate(instance=content_pack, schema=schema)
    except JsonSchemaValidationError as exc:
        raise ValueError(f"JSON Schema validation failed: {exc.message}")


def validate_content_pack(content_pack: dict) -> ContentPack:
    """
    Full validation: Pydantic first, then JSON Schema.
    Returns a ContentPack instance on success.
    Raises on any validation failure.
    """
    cp = validate_with_pydantic(content_pack)
    validate_with_json_schema(content_pack)
    return cp
