"""YAML scenario loader for UAT tests.

Loads scenario definitions from YAML files and validates them
against the UATScenario model.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from tests.uat.models import UATScenario


class ScenarioLoadError(Exception):
    """Raised when a scenario fails to load or validate."""

    def __init__(self, path: Path, reason: str) -> None:
        self.path = path
        self.reason = reason
        super().__init__(f"Failed to load scenario from {path}: {reason}")


def load_scenario(path: Path) -> UATScenario:
    """Load a single scenario from a YAML file.

    Args:
        path: Path to the YAML file.

    Returns:
        The parsed UATScenario.

    Raises:
        ScenarioLoadError: If loading or validation fails.
    """
    if not path.exists():
        raise ScenarioLoadError(path, "File not found")

    try:
        with path.open() as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ScenarioLoadError(path, f"Invalid YAML: {e}") from e

    if not isinstance(data, dict):
        raise ScenarioLoadError(path, "YAML must contain a mapping")

    try:
        return UATScenario.model_validate(data)
    except ValidationError as e:
        raise ScenarioLoadError(path, f"Validation failed: {e}") from e


def load_scenarios_from_directory(directory: Path) -> list[UATScenario]:
    """Load all scenarios from a directory.

    Args:
        directory: Directory containing YAML scenario files.

    Returns:
        List of parsed scenarios.

    Raises:
        ScenarioLoadError: If any scenario fails to load.
    """
    if not directory.exists():
        raise ScenarioLoadError(directory, "Directory not found")

    scenarios: list[UATScenario] = []
    for path in sorted(directory.glob("*.yaml")):
        scenarios.append(load_scenario(path))
    for path in sorted(directory.glob("*.yml")):
        scenarios.append(load_scenario(path))

    return scenarios


def filter_scenarios_by_tags(
    scenarios: list[UATScenario],
    include_tags: list[str] | None = None,
    exclude_tags: list[str] | None = None,
) -> list[UATScenario]:
    """Filter scenarios by tags.

    Args:
        scenarios: List of scenarios to filter.
        include_tags: If provided, only include scenarios with at least one of these tags.
        exclude_tags: If provided, exclude scenarios with any of these tags.

    Returns:
        Filtered list of scenarios.
    """
    result = scenarios

    if include_tags:
        include_set = set(include_tags)
        result = [s for s in result if include_set.intersection(s.tags)]

    if exclude_tags:
        exclude_set = set(exclude_tags)
        result = [s for s in result if not exclude_set.intersection(s.tags)]

    return result
