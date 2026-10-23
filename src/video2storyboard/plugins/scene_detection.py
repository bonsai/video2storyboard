"""Scene-boundary detection plugin scaffold."""
from .contract import PluginContext, PluginResult, PluginSpec
PLUGIN_SPEC = PluginSpec("scene_detection", "Scene detection", "Find scene boundaries in the source video.", ("source_video",), ("scenes",), ("opencv",))
def run(context: PluginContext) -> PluginResult:
    return PluginResult("scene_detection", "not_implemented", context, "Scaffold only; connect a scene detector.")
