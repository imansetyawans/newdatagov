from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Asset, LineageEdge


def _singular(name: str) -> str:
    return name[:-1] if name.endswith("s") else name


def _edge_exists(db: Session, upstream_asset_id: str, downstream_asset_id: str) -> bool:
    return (
        db.scalar(
            select(LineageEdge).where(
                LineageEdge.upstream_asset_id == upstream_asset_id,
                LineageEdge.downstream_asset_id == downstream_asset_id,
            )
        )
        is not None
    )


def extract_table_lineage(db: Session) -> int:
    assets = list(
        db.scalars(
            select(Asset)
            .options(selectinload(Asset.columns))
            .where(Asset.deleted_at.is_(None), Asset.asset_type == "table")
        ).all()
    )
    by_name = {asset.name.lower(): asset for asset in assets}
    created_count = 0

    for downstream in assets:
        for column in downstream.columns:
            column_name = column.name.lower()
            if not column_name.endswith("_id"):
                continue
            base = column_name.removesuffix("_id")
            upstream = by_name.get(base) or by_name.get(f"{base}s")
            if upstream is None or upstream.id == downstream.id:
                continue
            if _edge_exists(db, upstream.id, downstream.id):
                continue
            db.add(
                LineageEdge(
                    upstream_asset_id=upstream.id,
                    downstream_asset_id=downstream.id,
                    source_type="scan",
                    confidence=0.86,
                    edge_metadata={"reason": f"Matched foreign-key-like column {column.name}"},
                )
            )
            created_count += 1
    db.flush()
    return created_count


def build_lineage_graph(db: Session) -> dict:
    assets = list(db.scalars(select(Asset).where(Asset.deleted_at.is_(None)).order_by(Asset.name)).all())
    edges = list(db.scalars(select(LineageEdge).order_by(LineageEdge.created_at.desc())).all())
    return {
        "nodes": [
            {
                "id": asset.id,
                "name": asset.name,
                "source_path": asset.source_path,
                "dq_score": asset.dq_score,
                "classifications": asset.classifications,
            }
            for asset in assets
        ],
        "edges": [
            {
                "id": edge.id,
                "upstream_asset_id": edge.upstream_asset_id,
                "downstream_asset_id": edge.downstream_asset_id,
                "source_type": edge.source_type,
                "confidence": edge.confidence,
                "edge_metadata": edge.edge_metadata,
            }
            for edge in edges
        ],
    }
