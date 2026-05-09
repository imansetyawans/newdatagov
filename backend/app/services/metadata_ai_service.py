import json
import re
from urllib import request

from app.config import settings
from app.models import Asset, Column


def _humanize_identifier(value: str) -> str:
    cleaned = re.sub(r"[_\-]+", " ", value).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned or value


def _fallback_description(asset: Asset, column: Column) -> str:
    table = _humanize_identifier(asset.name)
    name = _humanize_identifier(column.name)
    lower = column.name.lower()
    data_type = column.data_type.upper()

    if lower in {"id", f"{asset.name.lower()}_id"} or lower.endswith("_id"):
        return f"Unique identifier used to link each {table} record across the data model."
    if "email" in lower:
        return f"Email address associated with the {table} record."
    if "date" in lower or "time" in lower or "timestamp" in lower:
        return f"Date or time value that records when the {table} event or state occurred."
    if any(token in lower for token in ["amount", "price", "cost", "revenue", "total", "balance"]):
        return f"Numeric financial value for {name} on the {table} record."
    if "status" in lower or "state" in lower:
        return f"Current lifecycle status for the {table} record."
    if "name" in lower or "title" in lower:
        return f"Display name or title used to identify the {table} record."
    return f"{name.capitalize()} value for the {table} record, stored as {data_type}."


def _extract_output_text(response_payload: dict) -> str:
    if isinstance(response_payload.get("output_text"), str):
        return response_payload["output_text"]

    chunks: list[str] = []
    for item in response_payload.get("output", []):
        for content in item.get("content", []):
            text = content.get("text")
            if isinstance(text, str):
                chunks.append(text)
    return "\n".join(chunks)


def _openai_descriptions(asset: Asset, columns: list[Column]) -> dict[str, str]:
    if not settings.openai_api_key:
        return {}

    column_payload = [
        {
            "id": column.id,
            "name": column.name,
            "data_type": column.data_type,
            "nullable": column.nullable,
            "existing_description": column.description,
        }
        for column in columns
    ]
    prompt = (
        "Generate concise business metadata descriptions for each database column. "
        "Return JSON only as {\"columns\":[{\"id\":\"...\",\"description\":\"...\"}]}. "
        "Descriptions should be one sentence, business-readable, and specific to the table.\n\n"
        f"Table: {asset.name}\n"
        f"Source path: {asset.source_path}\n"
        f"Columns: {json.dumps(column_payload)}"
    )
    payload = {
        "model": settings.ai_metadata_model,
        "input": prompt,
        "text": {
            "format": {
                "type": "json_schema",
                "name": "column_metadata",
                "schema": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "columns": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "additionalProperties": False,
                                "properties": {
                                    "id": {"type": "string"},
                                    "description": {"type": "string"},
                                },
                                "required": ["id", "description"],
                            },
                        }
                    },
                    "required": ["columns"],
                },
                "strict": True,
            }
        },
    }
    data = json.dumps(payload).encode("utf-8")
    api_request = request.Request(
        "https://api.openai.com/v1/responses",
        data=data,
        headers={
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with request.urlopen(api_request, timeout=30) as response:
        body = json.loads(response.read().decode("utf-8"))

    output_text = _extract_output_text(body)
    parsed = json.loads(output_text)
    return {
        item["id"]: item["description"].strip()
        for item in parsed.get("columns", [])
        if item.get("id") and item.get("description")
    }


def generate_column_descriptions(asset: Asset) -> tuple[dict[str, str], str]:
    columns = sorted(asset.columns, key=lambda column: column.ordinal_position)
    provider = "local"
    descriptions: dict[str, str] = {}

    try:
        descriptions = _openai_descriptions(asset, columns)
        if descriptions:
            provider = "openai"
    except Exception:
        descriptions = {}

    if not descriptions:
        descriptions = {column.id: _fallback_description(asset, column) for column in columns}

    return descriptions, provider
