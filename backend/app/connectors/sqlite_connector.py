import sqlite3
from pathlib import Path

from app.connectors.base import BaseConnector, DiscoveredAsset, DiscoveredColumn, DiscoveredSchema


def _quote_identifier(value: str) -> str:
    return f'"{value.replace(chr(34), chr(34) + chr(34))}"'


class SQLiteConnector(BaseConnector):
    def __init__(self, database_path: str, attached_databases: list[dict] | None = None) -> None:
        self.database_path = Path(database_path)
        self.attached_databases = attached_databases or []

    def _connect(self) -> sqlite3.Connection:
        if not self.database_path.exists():
            raise FileNotFoundError(f"SQLite database not found: {self.database_path}")
        connection = sqlite3.connect(str(self.database_path))
        for attached in self.attached_databases:
            schema = str(attached.get("schema", "")).strip()
            database_path = Path(str(attached.get("database_path", ""))).expanduser()
            if not schema:
                raise ValueError("Attached SQLite schema name is required")
            if not database_path.is_absolute():
                database_path = self.database_path.parent / database_path
            if not database_path.exists():
                raise FileNotFoundError(f"Attached SQLite database not found: {database_path}")
            connection.execute(f"attach database ? as {_quote_identifier(schema)}", (str(database_path),))
        return connection

    def test(self) -> dict:
        with self._connect() as connection:
            row = connection.execute("select sqlite_version()").fetchone()
        return {
            "success": True,
            "sqlite_version": row[0] if row else "unknown",
            "schemas": ["main", *[str(attached.get("schema")) for attached in self.attached_databases]],
        }

    def _schema_names(self) -> list[str]:
        return ["main", *[str(attached.get("schema")) for attached in self.attached_databases]]

    def _table_rows(self, connection: sqlite3.Connection, schema: str) -> list[tuple[str, str]]:
        return list(
            connection.execute(
                f"""
                select name, type
                from {_quote_identifier(schema)}.sqlite_master
                where type in ('table', 'view')
                  and name not like 'sqlite_%'
                  and name != 'alembic_version'
                order by name
                """
            ).fetchall()
        )

    def discover_schemas(self) -> list[DiscoveredSchema]:
        with self._connect() as connection:
            return [
                DiscoveredSchema(name=schema, asset_names=[name for name, _ in self._table_rows(connection, schema)])
                for schema in self._schema_names()
            ]

    def discover_assets(self, scope: dict | None = None) -> list[DiscoveredAsset]:
        assets: list[DiscoveredAsset] = []
        selected_schemas = set(scope.get("schemas") or []) if scope else set()
        scope_tables = scope.get("tables") or {} if scope else {}

        with self._connect() as connection:
            for schema in self._schema_names():
                if selected_schemas and schema not in selected_schemas:
                    continue
                table_scope = scope_tables.get(schema) if scope else None
                selected_tables = set(table_scope) if table_scope is not None else None
                table_rows = self._table_rows(connection, schema)

                for table_name, table_type in table_rows:
                    if selected_tables is not None and table_name not in selected_tables:
                        continue
                    column_rows = connection.execute(f"pragma {_quote_identifier(schema)}.table_info({_quote_identifier(table_name)})").fetchall()
                    columns = [
                        DiscoveredColumn(
                            name=row[1],
                            data_type=row[2] or "TEXT",
                            ordinal_position=row[0],
                            nullable=not bool(row[3]),
                        )
                        for row in column_rows
                    ]
                    row_count = 0
                    if table_type == "table":
                        try:
                            row = connection.execute(
                                f"select count(*) from {_quote_identifier(schema)}.{_quote_identifier(table_name)}"
                            ).fetchone()
                            row_count = int(row[0]) if row else 0
                        except sqlite3.DatabaseError:
                            row_count = 0

                    assets.append(
                        DiscoveredAsset(
                            name=table_name,
                            source_path=f"sqlite.{table_name}" if schema == "main" else f"sqlite.{schema}.{table_name}",
                            asset_type=table_type,
                            schema_name=schema,
                            row_count=row_count,
                            columns=columns,
                        )
                    )
        return assets
