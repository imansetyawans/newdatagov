import json
import re
from urllib import request

from app.config import settings
from app.models import Asset, Column


def _humanize_identifier(value: str) -> str:
    cleaned = re.sub(r"[_\-]+", " ", value).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned or value


def _sample_values(column: Column, limit: int = 4) -> list[str]:
    values = getattr(column, "sample_values", []) or []
    return [str(value) for value in values[:limit] if value is not None and str(value).strip()]


def _examples_phrase(column: Column) -> str:
    examples = _sample_values(column, 3)
    if not examples:
        return ""
    if len(examples) == 1:
        return f", with observed value {examples[0]}"
    return f", with observed values such as {', '.join(examples)}"


def _loan_description(asset: Asset, column: Column) -> str | None:
    table_context = f"{asset.name} {asset.source_path}".lower()
    if "loan" not in table_context:
        return None

    lower = column.name.lower()
    descriptions = {
        "loan_id": "Unique loan application identifier for each loan sanction record",
        "gender": "Applicant gender recorded for the loan application",
        "married": "Applicant marital status used in the loan eligibility profile",
        "dependents": "Number of dependents declared by the applicant for loan assessment",
        "education": "Applicant education level considered during loan assessment",
        "self_employed": "Indicates whether the applicant is self-employed for income and risk assessment",
        "applicantincome": "Applicant income amount used to assess loan affordability",
        "coapplicantincome": "Co-applicant income amount included in the loan affordability assessment",
        "loanamount": "Requested loan amount for the loan application",
        "loan_amount_term": "Loan repayment term for the application, typically expressed in months",
        "credit_history": "Credit history indicator used in loan eligibility assessment",
        "property_area": "Property area category associated with the loan application",
    }
    description = descriptions.get(lower)
    if description is None:
        return None
    return f"{description}{_examples_phrase(column)}."


def _fallback_description(asset: Asset, column: Column) -> str:
    table = _humanize_identifier(asset.name)
    name = _humanize_identifier(column.name)
    lower = column.name.lower()
    data_type = column.data_type.upper()
    examples = _examples_phrase(column)

    contextual = _loan_description(asset, column)
    if contextual:
        return contextual

    if lower in {"id", f"{asset.name.lower()}_id"} or lower.endswith("_id"):
        return f"Unique identifier for each {table} record{examples}."
    if "email" in lower:
        return f"Email address associated with the {table} record{examples}."
    if "date" in lower or "time" in lower or "timestamp" in lower:
        return f"Date or time value that records when the {table} event or state occurred{examples}."
    if any(token in lower for token in ["amount", "price", "cost", "revenue", "total", "balance"]):
        return f"Numeric financial value for {name} on the {table} record{examples}."
    if "income" in lower:
        return f"Income amount captured for the {table} record{examples}."
    if "status" in lower or "state" in lower:
        return f"Current lifecycle status for the {table} record{examples}."
    if "name" in lower or "title" in lower:
        return f"Display name or title used to identify the {table} record{examples}."
    if len(_sample_values(column, 8)) <= 5 and _sample_values(column):
        return f"Categorical {name.lower()} attribute for the {table} record{examples}."
    return f"{name.capitalize()} business attribute for the {table} record, represented as {data_type}{examples}."


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
            "standard_format": column.standard_format,
            "sample_values": _sample_values(column, 5),
            "classifications": column.classifications,
            "existing_description": column.description,
        }
        for column in columns
    ]
    prompt = (
        "Generate concise business metadata descriptions for each database column. "
        "Return JSON only as {\"columns\":[{\"id\":\"...\",\"description\":\"...\"}]}. "
        "Descriptions must infer the business meaning from the table name, source path, column name, "
        "standard format, and sample values. Do not merely restate the data type. "
        "Explain coded values when they are obvious from samples, but do not invent facts that are not supported. "
        "Each description should be one sentence, business-readable, and specific to the dataset context.\n\n"
        f"Table: {asset.name}\n"
        f"Source path: {asset.source_path}\n"
        f"Schema: {asset.schema_name}\n"
        f"Rows: {asset.row_count}\n"
        f"Table description: {asset.description}\n"
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
