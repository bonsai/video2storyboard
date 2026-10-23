"""Storyboard schema and artifact validation plugin scaffold."""
from .contract import PluginContext, PluginResult, PluginSpec
PLUGIN_SPEC = PluginSpec("validation", "Validation", "Validate storyboard schemas and output artifacts.", ("storyboard_json",), ("validation_report",))
def run(context: PluginContext) -> PluginResult:
    return PluginResult("validation", "not_implemented", context, "Scaffold only; connect current validation checks.")
