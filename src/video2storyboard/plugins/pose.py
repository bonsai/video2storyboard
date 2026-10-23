"""MediaPipe pose landmarks and overlay plugin scaffold."""
from .contract import PluginContext, PluginResult, PluginSpec
PLUGIN_SPEC = PluginSpec("pose", "Pose", "Estimate body landmarks and render optional pose overlays.", ("frames",), ("pose_results", "pose_overlays"), ("mediapipe", "opencv"), False)
def run(context: PluginContext) -> PluginResult:
    return PluginResult("pose", "not_implemented", context, "Scaffold only; import MediaPipe lazily in the implementation.")
