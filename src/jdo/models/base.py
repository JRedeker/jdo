"""Base model configuration for Pydantic models."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel as PydanticBaseModel
from pydantic import ConfigDict


def utc_now() -> datetime:
    """Get current UTC datetime.

    This is a shared utility for consistent datetime handling across models.
    """
    return datetime.now(UTC)


class BaseModel(PydanticBaseModel):
    """Base model with common configuration for all models."""

    model_config = ConfigDict(
        frozen=False,
        validate_assignment=True,
        extra="forbid",
    )
