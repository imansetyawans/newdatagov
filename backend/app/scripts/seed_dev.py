import sqlite3
from pathlib import Path

from sqlalchemy import select

from app.config import settings
from app.database import create_module_tables, sessionmakers
from app.models import Connector, GlossaryTerm, Policy, User
from app.services.classification_service import ensure_default_classification_labels
from app.utils.security import hash_password


def seed_sample_source() -> Path:
    source_path = Path(settings.sample_source_path)
    if not source_path.is_absolute():
        source_path = Path.cwd() / source_path

    with sqlite3.connect(source_path) as connection:
        connection.execute(
            """
            create table if not exists customers (
                id integer primary key,
                customer_name text not null,
                email text,
                age integer,
                status text,
                created_at text
            )
            """
        )
        connection.execute(
            """
            create table if not exists orders (
                id integer primary key,
                customer_id integer,
                order_total real,
                order_status text,
                ordered_at text
            )
            """
        )
        customer_count = connection.execute("select count(*) from customers").fetchone()[0]
        if customer_count == 0:
            connection.executemany(
                "insert into customers (customer_name, email, age, status, created_at) values (?, ?, ?, ?, ?)",
                [
                    ("Ana Wijaya", "ana@example.com", 31, "active", "2026-01-05"),
                    ("Bima Santoso", "bima@example.com", 27, "inactive", "2026-01-12"),
                    ("Citra Lestari", "citra@example.com", 44, "pending", "2026-02-03"),
                    ("Dian Pratama", "dian@example.com", 36, "active", "2026-02-20"),
                ],
            )
        order_count = connection.execute("select count(*) from orders").fetchone()[0]
        if order_count == 0:
            connection.executemany(
                "insert into orders (customer_id, order_total, order_status, ordered_at) values (?, ?, ?, ?)",
                [
                    (1, 1250000, "completed", "2026-03-01"),
                    (2, 775000, "open", "2026-03-04"),
                    (3, 220000, "completed", "2026-03-10"),
                    (1, 990000, "pending", "2026-03-12"),
                ],
            )
        connection.commit()
    return source_path


def seed_dataset_source(file_name: str, statements: list[str], rows: list[tuple[str, list[tuple]]]) -> Path:
    source_path = Path(file_name)
    if not source_path.is_absolute():
        source_path = Path.cwd() / source_path

    with sqlite3.connect(source_path) as connection:
        for statement in statements:
            connection.execute(statement)
        for table_name, table_rows in rows:
            row_count = connection.execute(f'select count(*) from "{table_name}"').fetchone()[0]
            if row_count == 0 and table_rows:
                placeholders = ", ".join("?" for _ in table_rows[0])
                connection.executemany(f'insert into "{table_name}" values ({placeholders})', table_rows)
        connection.commit()
    return source_path


def seed_attached_sources() -> list[dict]:
    sales_path = seed_dataset_source(
        "sample_sales.db",
        [
            """
            create table if not exists opportunities (
                id integer primary key,
                customer_id integer,
                deal_name text,
                stage text,
                expected_value real,
                close_date text
            )
            """,
            """
            create table if not exists invoices (
                id integer primary key,
                customer_id integer,
                invoice_number text,
                amount real,
                payment_status text,
                issued_at text
            )
            """,
        ],
        [
            (
                "opportunities",
                [
                    (1, 1, "Enterprise renewal", "proposal", 5400000, "2026-05-30"),
                    (2, 2, "Data platform pilot", "negotiation", 2750000, "2026-06-12"),
                    (3, 3, "Governance rollout", "qualified", 3850000, "2026-07-03"),
                ],
            ),
            (
                "invoices",
                [
                    (1, 1, "INV-2026-001", 1250000, "paid", "2026-03-02"),
                    (2, 2, "INV-2026-002", 775000, "open", "2026-03-05"),
                    (3, 3, "INV-2026-003", 220000, "paid", "2026-03-11"),
                ],
            ),
        ],
    )
    hr_path = seed_dataset_source(
        "sample_hr.db",
        [
            """
            create table if not exists employees (
                id integer primary key,
                employee_name text,
                work_email text,
                department text,
                employment_status text,
                hired_at text
            )
            """,
            """
            create table if not exists departments (
                id integer primary key,
                department_name text,
                cost_center text,
                manager_email text
            )
            """,
        ],
        [
            (
                "employees",
                [
                    (1, "Rani Kusuma", "rani@datagov.local", "Data", "active", "2024-08-01"),
                    (2, "Aditya Putra", "aditya@datagov.local", "Finance", "active", "2025-01-15"),
                    (3, "Maya Sari", "maya@datagov.local", "People", "inactive", "2023-11-20"),
                ],
            ),
            (
                "departments",
                [
                    (1, "Data", "CC-100", "lead-data@datagov.local"),
                    (2, "Finance", "CC-200", "lead-finance@datagov.local"),
                    (3, "People", "CC-300", "lead-people@datagov.local"),
                ],
            ),
        ],
    )
    finance_path = seed_dataset_source(
        "sample_finance.db",
        [
            """
            create table if not exists payments (
                id integer primary key,
                invoice_id integer,
                payment_reference text,
                payment_amount real,
                payment_method text,
                paid_at text
            )
            """,
            """
            create table if not exists budget_allocations (
                id integer primary key,
                department_name text,
                fiscal_year integer,
                allocated_amount real,
                owner_email text
            )
            """,
        ],
        [
            (
                "payments",
                [
                    (1, 1, "PAY-2026-001", 1250000, "bank_transfer", "2026-03-03"),
                    (2, 3, "PAY-2026-002", 220000, "credit_card", "2026-03-12"),
                    (3, 2, "PAY-2026-003", 300000, "bank_transfer", "2026-03-16"),
                ],
            ),
            (
                "budget_allocations",
                [
                    (1, "Data", 2026, 15000000, "lead-data@datagov.local"),
                    (2, "Finance", 2026, 9000000, "lead-finance@datagov.local"),
                    (3, "People", 2026, 7000000, "lead-people@datagov.local"),
                ],
            ),
        ],
    )
    return [
        {"schema": "sales", "database_path": str(sales_path)},
        {"schema": "hr", "database_path": str(hr_path)},
        {"schema": "finance", "database_path": str(finance_path)},
    ]


def seed() -> None:
    create_module_tables()
    sample_source_path = seed_sample_source()
    attached_databases = seed_attached_sources()

    with sessionmakers["admin"]() as db:
        admin = db.scalar(select(User).where(User.email == "admin@datagov.local"))
        if admin is None:
            admin = User(
                email="admin@datagov.local",
                hashed_password=hash_password("admin123"),
                full_name="DataGov Admin",
                role="admin",
            )
            db.add(admin)
            db.flush()
        admin_id = admin.id

        connector = db.scalar(select(Connector).where(Connector.name == "Sample Business SQLite"))
        if connector is None:
            db.add(
                Connector(
                    name="Sample Business SQLite",
                    connector_type="sqlite",
                    config_encrypted={"database_path": str(sample_source_path), "attached_databases": attached_databases},
                    status="active",
                )
            )
        else:
            config = dict(connector.config_encrypted or {})
            config["database_path"] = str(sample_source_path)
            config["attached_databases"] = attached_databases
            connector.config_encrypted = config
            connector.status = "active"
        db.commit()

    with sessionmakers["classification"]() as db:
        ensure_default_classification_labels(db)

    with sessionmakers["policy"]() as db:
        email_policy = db.scalar(select(Policy).where(Policy.name == "Classify email columns as PII"))
        if email_policy is None:
            db.add(
                Policy(
                    name="Classify email columns as PII",
                    policy_type="classification",
                    status="active",
                    rules=[{"field": "column_name", "operator": "contains", "value": "email"}],
                    action={"classification": "PII"},
                    created_by_id=admin_id,
                )
            )
        db.commit()

    with sessionmakers["glossary"]() as db:
        default_terms = [
            ("Customer", "A person or organization that purchases or uses products and services.", ["client", "buyer"]),
            ("Order", "A commercial transaction created when a customer requests goods or services.", ["purchase", "sale"]),
        ]
        for term_name, definition, synonyms in default_terms:
            exists = db.scalar(select(GlossaryTerm).where(GlossaryTerm.term == term_name))
            if exists is None:
                db.add(
                    GlossaryTerm(
                        term=term_name,
                        definition=definition,
                        synonyms=synonyms,
                        status="approved",
                        steward_id=admin_id,
                    )
                )
        db.commit()


if __name__ == "__main__":
    seed()
    print("Seeded modular development data: admin@datagov.local / admin123")
