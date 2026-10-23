"""Shared contract for pipeline plugins."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Protocol


@dataclass(frozen=True)
class PluginSpec:
    """Stable metadata used by the registry and YAML pipeline definitions."""
    plugin_id: str
    title: str
    description: str
    inputs: tuple[str, ...] = ()
    outputs: tuple[str, ...] = ()
    optional_dependencies: tuple[str, ...] = ()
    enabled_by_default: bool = True


@dataclass
class PluginContext:
    """Shared run context; values should be JSON-serializable where practical."""
    run_id: str
    data: dict[str, Any] = field(default_factory=dict)
    artifacts: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PluginResult:
    """Explicit plugin outcome; errors should be returned, not silently swallowed."""
    plugin_id: str
    status: str
    context: PluginContext
    message: str = ""
    metrics: dict[str, int | float | str | bool] = field(default_factory=dict)


class Plugin(Protocol):
    spec: PluginSpec

    def run(self, context: PluginContext) -> PluginResult:
        """Run this plugin against the current context."""
        ...


PluginRunner = Callable[[PluginContext], PluginResult]
