"""Base model configuration for Pydantic models."""

from __future__ import annotations

from pydantic import BaseModel as PydanticBaseModel
from pydantic import ConfigDict


class BaseModel(PydanticBaseModel):
    """Base model with common configuration for all models."""

    model_config = ConfigDict(
        frozen=False,
        validate_assignment=True,
        extra="forbid",
    )
