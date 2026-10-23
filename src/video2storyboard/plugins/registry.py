"""Plugin registry. Importing the registry does not load optional ML dependencies."""
from __future__ import annotations

from .contract import PluginSpec

from . import ingest, scene_detection, keyframes, pose, composition
from . import vision, speech, storyboard, export, validation

_PLUGIN_MODULES = (
    ingest, scene_detection, keyframes, pose, composition,
    vision, speech, storyboard, export, validation,
)
PLUGINS: dict[str, PluginSpec] = {module.PLUGIN_SPEC.plugin_id: module.PLUGIN_SPEC for module in _PLUGIN_MODULES}


def list_plugins() -> list[PluginSpec]:
    """Return plugin specs in deterministic pipeline order."""
    return [module.PLUGIN_SPEC for module in _PLUGIN_MODULES]


def get_plugin(plugin_id: str) -> PluginSpec:
    """Look up a plugin definition or raise a useful error."""
    try:
        return PLUGINS[plugin_id]
    except KeyError as exc:
        available = ", ".join(PLUGINS)
        raise KeyError(f"Unknown plugin {plugin_id!r}. Available plugins: {available}") from exc
