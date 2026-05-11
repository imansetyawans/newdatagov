import re
from collections.abc import Callable


EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
INTEGER_PATTERN = re.compile(r"^-?\d+$")
DECIMAL_PATTERN = re.compile(r"^-?\d+\.\d+$")
UUID_PATTERN = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
URL_PATTERN = re.compile(r"^https?://\S+$", re.IGNORECASE)

ConsistencyMatcher = Callable[[object], bool]


def matcher_from_standard_format(standard_format: str | None) -> ConsistencyMatcher | None:
    if not standard_format:
        return None

    normalized = standard_format.strip().lower()
    if not normalized:
        return None

    if "valid email address" in normalized:
        return _regex_matcher(EMAIL_PATTERN)
    if "yyyy-mm-dd" in normalized or normalized == "date":
        return _regex_matcher(DATE_PATTERN)
    if normalized == "uuid":
        return _regex_matcher(UUID_PATTERN)
    if normalized == "url":
        return _regex_matcher(URL_PATTERN)
    if normalized == "boolean value":
        return lambda value: str(value).strip().lower() in {"true", "false", "0", "1", "yes", "no"}
    if normalized in {"integer identifier", "integer number"}:
        return _regex_matcher(INTEGER_PATTERN)
    if normalized == "decimal number":
        return lambda value: _matches(INTEGER_PATTERN, value) or _matches(DECIMAL_PATTERN, value)
    if normalized.startswith("controlled vocabulary:"):
        allowed_values = {
            value.strip().lower()
            for value in standard_format.split(":", maxsplit=1)[1].split(",")
            if value.strip()
        }
        if not allowed_values:
            return None
        return lambda value: str(value).strip().lower() in allowed_values
    if normalized == "lowercase text":
        return _lowercase_text
    return None


def _regex_matcher(pattern: re.Pattern) -> ConsistencyMatcher:
    return lambda value: _matches(pattern, value)


def _matches(pattern: re.Pattern, value: object) -> bool:
    return bool(pattern.match(str(value).strip()))


def _lowercase_text(value: object) -> bool:
    text = str(value).strip()
    return text == text.lower()
