from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ClassificationLabel


DEFAULT_CLASSIFICATION_LABELS = [
    {
        "name": "PII",
        "color_key": "danger",
        "description": "Personally identifiable information",
        "masks_samples": True,
    },
    {
        "name": "GDPR",
        "color_key": "blue",
        "description": "GDPR governed asset or column",
        "masks_samples": False,
    },
    {
        "name": "Finance",
        "color_key": "warning",
        "description": "Financial data",
        "masks_samples": False,
    },
    {
        "name": "Internal",
        "color_key": "purple",
        "description": "Internal business data",
        "masks_samples": False,
    },
    {
        "name": "Public",
        "color_key": "success",
        "description": "Publicly shareable data",
        "masks_samples": False,
    },
    {
        "name": "Sensitive",
        "color_key": "danger",
        "description": "Sensitive information",
        "masks_samples": True,
    },
    {
        "name": "Restricted",
        "color_key": "danger",
        "description": "Restricted access information",
        "masks_samples": True,
    },
]


def ensure_default_classification_labels(db: Session) -> None:
    for label_data in DEFAULT_CLASSIFICATION_LABELS:
        label = db.scalar(select(ClassificationLabel).where(ClassificationLabel.name == label_data["name"]))
        if label is None:
            db.add(ClassificationLabel(**label_data))
            continue
        label.color_key = str(label_data["color_key"])
        label.description = str(label_data["description"])
        label.masks_samples = bool(label_data["masks_samples"])
    db.commit()
