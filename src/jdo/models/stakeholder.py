"""Stakeholder SQLModel entity."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel

from jdo.utils.datetime import utc_now


class StakeholderType(str, Enum):
    """Types of stakeholders."""

    PERSON = "person"
    TEAM = "team"
    ORGANIZATION = "organization"
    SELF = "self"


class Stakeholder(SQLModel, table=True):
    """A stakeholder to whom commitments are made.

    Stakeholders represent entities (people, teams, organizations, or self)
    to whom the user has made commitments.
    """

    __tablename__ = "stakeholders"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(min_length=1)
    type: StakeholderType
    contact_info: str | None = Field(default=None)
    notes: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
