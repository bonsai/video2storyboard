"""Canonical storyboard JSON construction plugin scaffold."""
from .contract import PluginContext, PluginResult, PluginSpec
PLUGIN_SPEC = PluginSpec("storyboard", "Storyboard", "Combine analysis into canonical storyboard data.", ("scenes", "frames"), ("storyboard_json",))
def run(context: PluginContext) -> PluginResult:
    return PluginResult("storyboard", "not_implemented", context, "Scaffold only; use storyboard JSON as canonical data.")
