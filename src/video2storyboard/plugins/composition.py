"""OpenCV composition and visual-measurement plugin scaffold."""
from .contract import PluginContext, PluginResult, PluginSpec
PLUGIN_SPEC = PluginSpec("composition", "Composition", "Measure frame composition and visual geometry.", ("frames",), ("composition_metrics",), ("opencv",))
def run(context: PluginContext) -> PluginResult:
    return PluginResult("composition", "not_implemented", context, "Scaffold only; adapter to existing composition analysis.")
