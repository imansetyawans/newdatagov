from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import Asset, GlossaryTerm


def list_terms(db: Session, q: str | None = None) -> list[GlossaryTerm]:
    statement = select(GlossaryTerm).order_by(GlossaryTerm.term)
    if q:
        like = f"%{q}%"
        statement = statement.where(or_(GlossaryTerm.term.ilike(like), GlossaryTerm.definition.ilike(like)))
    return list(db.scalars(statement).all())


def suggest_glossary_links(glossary_db: Session, catalogue_db: Session) -> list[dict]:
    terms = list_terms(glossary_db)
    assets = list(catalogue_db.scalars(select(Asset).where(Asset.deleted_at.is_(None))).all())
    suggestions: list[dict] = []

    for term in terms:
        candidates = {term.term.lower(), *[synonym.lower() for synonym in term.synonyms]}
        for asset in assets:
            asset_name = asset.name.lower()
            for candidate in candidates:
                if candidate and candidate in asset_name and asset.id not in term.linked_asset_ids:
                    suggestions.append(
                        {
                            "term_id": term.id,
                            "term": term.term,
                            "resource_type": "asset",
                            "resource_id": asset.id,
                            "resource_name": asset.name,
                            "confidence": 0.82,
                        }
                    )
            for column in asset.columns:
                column_name = column.name.lower()
                for candidate in candidates:
                    if candidate and candidate in column_name and column.id not in term.linked_column_ids:
                        suggestions.append(
                            {
                                "term_id": term.id,
                                "term": term.term,
                                "resource_type": "column",
                                "resource_id": column.id,
                                "resource_name": f"{asset.name}.{column.name}",
                                "confidence": 0.9,
                            }
                        )
    return suggestions
