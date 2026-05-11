import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Asset, Column, DQIssue
from app.services.standard_format_rules import matcher_from_standard_format


@dataclass(frozen=True)
class ColumnDQScores:
    completeness: float | None
    uniqueness: float | None
    consistency: float | None
    accuracy: float | None


PATTERNS = {
    "email": re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$"),
    "uuid": re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"),
    "url": re.compile(r"^https?://[^\s]+$"),
    "phone": re.compile(r"^\+?[0-9][0-9\s().-]{6,}$"),
    "date": re.compile(r"^\d{4}-\d{2}-\d{2}"),
}


def _quote(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def _attach_databases(connection: sqlite3.Connection, database_path: str, attached_databases: list[dict] | None) -> None:
    base_path = Path(database_path).expanduser()
    for attached in attached_databases or []:
        schema = str(attached.get("schema", "")).strip()
        attached_path = Path(str(attached.get("database_path", ""))).expanduser()
        if not attached_path.is_absolute():
            attached_path = base_path.parent / attached_path
        connection.execute(f"attach database ? as {_quote(schema)}", (str(attached_path),))


def _score(valid_count: int, total: int) -> float | None:
    if total == 0:
        return None
    return round((valid_count / total) * 100, 1)


def _pattern_for(column: Column) -> re.Pattern | None:
    lower_name = column.name.lower()
    lower_type = column.data_type.lower()
    if "email" in lower_name:
        return PATTERNS["email"]
    if "uuid" in lower_name:
        return PATTERNS["uuid"]
    if "url" in lower_name or "uri" in lower_name:
        return PATTERNS["url"]
    if "phone" in lower_name or "mobile" in lower_name:
        return PATTERNS["phone"]
    if "date" in lower_name or "time" in lower_name or "date" in lower_type or "time" in lower_type:
        return PATTERNS["date"]
    return None


def _consistency_matcher_for(column: Column):
    pattern = _pattern_for(column)
    if pattern is not None:
        return lambda value: bool(pattern.match(str(value)))
    return matcher_from_standard_format(column.standard_format)


def _accuracy_valid(value: object, column: Column) -> bool:
    if value is None:
        return False
    lower_name = column.name.lower()
    if lower_name in {"age", "customer_age", "user_age"}:
        try:
            age = float(value)
        except (TypeError, ValueError):
            return False
        return 0 <= age <= 120
    if "status" in lower_name:
        return str(value).lower() in {"active", "inactive", "pending", "closed", "open", "draft", "completed"}
    return True


def _calculate_column_scores(
    connection: sqlite3.Connection,
    table_name: str,
    column: Column,
    schema_name: str | None = None,
) -> ColumnDQScores:
    table = f"{_quote(schema_name)}.{_quote(table_name)}" if schema_name else _quote(table_name)
    field = _quote(column.name)
    total = connection.execute(f"select count(*) from {table}").fetchone()[0]
    if total == 0:
        return ColumnDQScores(None, None, None, None)

    non_null = connection.execute(f"select count({field}) from {table}").fetchone()[0]
    distinct = connection.execute(f"select count(distinct {field}) from {table} where {field} is not null").fetchone()[0]
    values = [row[0] for row in connection.execute(f"select {field} from {table}").fetchall()]

    consistency_matcher = _consistency_matcher_for(column)
    if consistency_matcher is None:
        consistency = 100.0
    else:
        consistency = _score(sum(1 for value in values if value is not None and consistency_matcher(value)), total)

    accuracy = _score(sum(1 for value in values if _accuracy_valid(value, column)), total)

    return ColumnDQScores(
        completeness=_score(non_null, total),
        uniqueness=_score(distinct, total),
        consistency=consistency,
        accuracy=accuracy,
    )


def _average(values: list[float | None]) -> float | None:
    usable = [value for value in values if value is not None]
    if not usable:
        return None
    return round(sum(usable) / len(usable), 1)


def _create_issue_if_needed(
    quality_db: Session,
    asset: Asset,
    column: Column,
    metric_name: str,
    previous_score: float | None,
    current_score: float | None,
) -> None:
    if previous_score is None or current_score is None:
        return
    delta = round(current_score - previous_score, 1)
    if delta >= -10:
        return

    existing_open = quality_db.scalar(
        select(DQIssue).where(
            DQIssue.asset_id == asset.id,
            DQIssue.column_id == column.id,
            DQIssue.metric_name == metric_name,
            DQIssue.status == "open",
        )
    )
    if existing_open:
        existing_open.delta_value = delta
        existing_open.previous_score = previous_score
        existing_open.current_score = current_score
        existing_open.severity = "critical" if current_score < 50 or delta <= -30 else "warning"
        return

    quality_db.add(
        DQIssue(
            asset_id=asset.id,
            column_id=column.id,
            metric_name=metric_name,
            severity="critical" if current_score < 50 or delta <= -30 else "warning",
            status="open",
            delta_value=delta,
            previous_score=previous_score,
            current_score=current_score,
        )
    )


def calculate_asset_quality(
    catalogue_db: Session,
    quality_db: Session,
    database_path: str,
    asset: Asset,
    table_name: str,
    attached_databases: list[dict] | None = None,
) -> int:
    issue_count_before = len(list(quality_db.scalars(select(DQIssue).where(DQIssue.asset_id == asset.id)).all()))

    with sqlite3.connect(database_path) as connection:
        _attach_databases(connection, database_path, attached_databases)
        for column in asset.columns:
            previous = {
                "completeness": column.completeness_score,
                "uniqueness": column.uniqueness_score,
                "consistency": column.consistency_score,
                "accuracy": column.accuracy_score,
            }
            scores = _calculate_column_scores(connection, table_name, column, asset.schema_name)
            current = {
                "completeness": scores.completeness,
                "uniqueness": scores.uniqueness,
                "consistency": scores.consistency,
                "accuracy": scores.accuracy,
            }

            for metric_name, current_score in current.items():
                _create_issue_if_needed(quality_db, asset, column, metric_name, previous[metric_name], current_score)

            column.completeness_score = scores.completeness
            column.uniqueness_score = scores.uniqueness
            column.consistency_score = scores.consistency
            column.accuracy_score = scores.accuracy

    asset.dq_score = _average(
        [
            score
            for column in asset.columns
            for score in [
                column.completeness_score,
                column.uniqueness_score,
                column.consistency_score,
                column.accuracy_score,
            ]
        ]
    )
    catalogue_db.flush()
    quality_db.flush()
    issue_count_after = len(list(quality_db.scalars(select(DQIssue).where(DQIssue.asset_id == asset.id)).all()))
    return max(0, issue_count_after - issue_count_before)
