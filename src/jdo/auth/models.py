"""Pydantic models for authentication credentials."""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, Field


class ApiKeyCredentials(BaseModel):
    """API key credentials for providers that use simple key authentication."""

    api_key: Annotated[str, Field(min_length=1)]


ProviderAuth = ApiKeyCredentials
