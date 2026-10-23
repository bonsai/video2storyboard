"""HTML, SVG and media artifact export plugin scaffold."""
from .contract import PluginContext, PluginResult, PluginSpec
PLUGIN_SPEC = PluginSpec("export", "Export", "Export storyboard and overlay artifacts to HTML/SVG/media.", ("storyboard_json",), ("exported_artifacts",))
def run(context: PluginContext) -> PluginResult:
    return PluginResult("export", "not_implemented", context, "Scaffold only; connect current exporters.")
