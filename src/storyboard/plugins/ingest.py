"""Source-video validation and metadata plugin scaffold."""
from .contract import PluginContext, PluginResult, PluginSpec
PLUGIN_SPEC = PluginSpec("ingest", "Ingest", "Validate source and collect video metadata.", ("source_video",), ("video_metadata",))
def run(context: PluginContext) -> PluginResult:
    return PluginResult("ingest", "not_implemented", context, "Scaffold only; adapter to existing ingest logic.")
