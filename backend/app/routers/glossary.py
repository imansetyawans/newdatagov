from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_audit_db, get_catalogue_db, get_glossary_db
from app.middleware.auth import get_current_user, require_roles
from app.models import GlossaryTerm, User
from app.schemas.glossary import (
    GlossarySuggestionListResponse,
    GlossarySuggestionRead,
    GlossaryTermCreate,
    GlossaryTermListResponse,
    GlossaryTermRead,
    GlossaryTermResponse,
    GlossaryTermUpdate,
)
from app.services.glossary_service import list_terms, suggest_glossary_links
from app.services.audit_service import write_audit_log


router = APIRouter(prefix="/api/v1/glossary", tags=["glossary"])


@router.get("", response_model=GlossaryTermListResponse)
def glossary_terms(
    q: str | None = None,
    db: Session = Depends(get_glossary_db),
    _: User = Depends(get_current_user),
) -> GlossaryTermListResponse:
    terms = list_terms(db, q=q)
    return GlossaryTermListResponse(data=[GlossaryTermRead.model_validate(term) for term in terms], meta={"count": len(terms)})


@router.post("", response_model=GlossaryTermResponse)
def create_glossary_term(
    payload: GlossaryTermCreate,
    db: Session = Depends(get_glossary_db),
    audit_db: Session = Depends(get_audit_db),
    user: User = Depends(require_roles(["admin", "editor"])),
) -> GlossaryTermResponse:
    data = payload.model_dump()
    data["steward_id"] = payload.steward_id or user.id
    term = GlossaryTerm(**data)
    db.add(term)
    db.commit()
    db.refresh(term)
    write_audit_log(
        audit_db,
        user,
        action="glossary_term_created",
        resource_type="glossary_term",
        resource_id=term.id,
        event_type="glossary",
        metadata={"term": term.term},
    )
    audit_db.commit()
    return GlossaryTermResponse(data=GlossaryTermRead.model_validate(term), meta={})


@router.patch("/{term_id}", response_model=GlossaryTermResponse)
def update_glossary_term(
    term_id: str,
    payload: GlossaryTermUpdate,
    db: Session = Depends(get_glossary_db),
    audit_db: Session = Depends(get_audit_db),
    user: User = Depends(require_roles(["admin", "editor"])),
) -> GlossaryTermResponse:
    term = db.get(GlossaryTerm, term_id)
    if term is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Glossary term not found")
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(term, key, value)
    db.commit()
    db.refresh(term)
    write_audit_log(
        audit_db,
        user,
        action="glossary_term_updated",
        resource_type="glossary_term",
        resource_id=term.id,
        event_type="glossary",
        metadata={"term": term.term, "fields": sorted(updates)},
    )
    audit_db.commit()
    return GlossaryTermResponse(data=GlossaryTermRead.model_validate(term), meta={})


@router.delete("/{term_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_glossary_term(
    term_id: str,
    db: Session = Depends(get_glossary_db),
    audit_db: Session = Depends(get_audit_db),
    user: User = Depends(require_roles(["admin"])),
) -> None:
    term = db.get(GlossaryTerm, term_id)
    if term is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Glossary term not found")
    term_name = term.term
    db.delete(term)
    db.commit()
    write_audit_log(
        audit_db,
        user,
        action="glossary_term_deleted",
        resource_type="glossary_term",
        resource_id=term_id,
        event_type="glossary",
        metadata={"term": term_name},
    )
    audit_db.commit()


@router.get("/suggestions", response_model=GlossarySuggestionListResponse)
def glossary_suggestions(
    glossary_db: Session = Depends(get_glossary_db),
    catalogue_db: Session = Depends(get_catalogue_db),
    _: User = Depends(get_current_user),
) -> GlossarySuggestionListResponse:
    suggestions = suggest_glossary_links(glossary_db, catalogue_db)
    return GlossarySuggestionListResponse(
        data=[GlossarySuggestionRead(**suggestion) for suggestion in suggestions],
        meta={"count": len(suggestions)},
    )
