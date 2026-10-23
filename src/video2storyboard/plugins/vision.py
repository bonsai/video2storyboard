"""Vision-language scene interpretation plugin scaffold."""
from .contract import PluginContext, PluginResult, PluginSpec
PLUGIN_SPEC = PluginSpec("vision", "Vision", "Describe scenes and visual events with a VLM.", ("frames",), ("visual_descriptions",), ("vlm_client",), False)
def run(context: PluginContext) -> PluginResult:
    return PluginResult("vision", "not_implemented", context, "Scaffold only; connect configured VLM provider.")
