"""Tests for models/base.py module."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from jdo.models.base import BaseModel


class TestBaseModel:
    """Tests for BaseModel class."""

    def test_default_config(self) -> None:
        """Test that BaseModel has expected default configuration."""

        class TestModel(BaseModel):
            name: str
            value: int

        model = TestModel(name="test", value=42)

        assert model.name == "test"
        assert model.value == 42

    def test_validate_assignment(self) -> None:
        """Test that validate_assignment is enabled."""

        class TestModel(BaseModel):
            value: int

        model = TestModel(value=10)

        with pytest.raises(ValidationError):
            model.value = "not an int"  # type: ignore[assignment]

    def test_extra_forbidden(self) -> None:
        """Test that extra fields are forbidden."""

        class TestModel(BaseModel):
            name: str

        with pytest.raises(ValidationError):
            TestModel(name="test", extra_field="not allowed")  # type: ignore[call-arg]

    def test_not_frozen(self) -> None:
        """Test that model is not frozen (can be mutated)."""

        class TestModel(BaseModel):
            value: int

        model = TestModel(value=10)
        model.value = 20  # type: ignore[assignment]
        assert model.value == 20

    def test_nested_models(self) -> None:
        """Test that nested models work correctly."""

        class Inner(BaseModel):
            x: int

        class Outer(BaseModel):
            inner: Inner
            y: str

        outer = Outer(inner=Inner(x=5), y="test")
        assert outer.inner.x == 5
        assert outer.y == "test"

    def test_model_repr(self) -> None:
        """Test model string representation."""

        class TestModel(BaseModel):
            name: str

        model = TestModel(name="test")
        assert "test" in repr(model)
