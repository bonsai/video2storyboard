"""Frame sampling and keyframe extraction plugin scaffold."""
from .contract import PluginContext, PluginResult, PluginSpec
PLUGIN_SPEC = PluginSpec("keyframes", "Keyframes", "Sample frames and persist frame metadata.", ("source_video",), ("frames",), ("opencv",))
def run(context: PluginContext) -> PluginResult:
    return PluginResult("keyframes", "not_implemented", context, "Scaffold only; adapter to existing frame extraction.")
