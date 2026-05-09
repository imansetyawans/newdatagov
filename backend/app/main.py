from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import create_module_tables, sessionmakers
from app.routers.catalogue import router as catalogue_router
from app.routers.connectors import router as connectors_router
from app.routers.governance import router as governance_router
from app.routers.identity import router as identity_router
from app.routers.glossary import router as glossary_router
from app.routers.lineage import router as lineage_router
from app.routers.notifications import router as notifications_router
from app.routers.quality import router as quality_router
from app.routers.scans import router as scans_router
from app.routers.uploads import router as uploads_router
from app.services.classification_service import ensure_default_classification_labels


def create_app() -> FastAPI:
    create_module_tables()
    with sessionmakers["classification"]() as db:
        ensure_default_classification_labels(db)

    app = FastAPI(
        title="DataGov API",
        version="0.1.0",
        debug=settings.debug,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["system"])
    def health_check() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(identity_router)
    app.include_router(connectors_router)
    app.include_router(catalogue_router)
    app.include_router(scans_router)
    app.include_router(uploads_router)
    app.include_router(quality_router)
    app.include_router(governance_router)
    app.include_router(glossary_router)
    app.include_router(lineage_router)
    app.include_router(notifications_router)

    return app


app = create_app()
