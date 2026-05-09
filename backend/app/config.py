from functools import lru_cache

from pydantic import Field
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


LOCAL_MODULE_DATABASE_URLS = {
    "admin_database_url": "sqlite:///./datagov_admin.db",
    "catalogue_database_url": "sqlite:///./datagov_catalogue.db",
    "classification_database_url": "sqlite:///./datagov_classification.db",
    "quality_database_url": "sqlite:///./datagov_quality.db",
    "policy_database_url": "sqlite:///./datagov_policy.db",
    "glossary_database_url": "sqlite:///./datagov_glossary.db",
    "audit_database_url": "sqlite:///./datagov_audit.db",
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env.local", "../.env.local"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = ""
    admin_database_url: str = LOCAL_MODULE_DATABASE_URLS["admin_database_url"]
    catalogue_database_url: str = LOCAL_MODULE_DATABASE_URLS["catalogue_database_url"]
    classification_database_url: str = LOCAL_MODULE_DATABASE_URLS["classification_database_url"]
    quality_database_url: str = LOCAL_MODULE_DATABASE_URLS["quality_database_url"]
    policy_database_url: str = LOCAL_MODULE_DATABASE_URLS["policy_database_url"]
    glossary_database_url: str = LOCAL_MODULE_DATABASE_URLS["glossary_database_url"]
    audit_database_url: str = LOCAL_MODULE_DATABASE_URLS["audit_database_url"]
    sample_source_path: str = "sample_business.db"
    secret_key: str = "dev-secret-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480

    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"

    debug: bool = True
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    openai_api_key: str | None = None
    ai_metadata_model: str = "gpt-5-mini"

    @model_validator(mode="after")
    def apply_shared_database_url(self) -> "Settings":
        """Use DATABASE_URL as the shared cloud metadata DB unless a module URL is explicitly overridden."""
        if self.database_url:
            for field_name, local_default in LOCAL_MODULE_DATABASE_URLS.items():
                if getattr(self, field_name) == local_default:
                    setattr(self, field_name, self.database_url)
        else:
            self.database_url = self.admin_database_url
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
