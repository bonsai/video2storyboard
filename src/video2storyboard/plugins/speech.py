"""Audio transcription plugin scaffold."""
from .contract import PluginContext, PluginResult, PluginSpec
PLUGIN_SPEC = PluginSpec("speech", "Speech", "Transcribe source audio and align text with timestamps.", ("source_video",), ("transcript",), ("asr_client",), False)
def run(context: PluginContext) -> PluginResult:
    return PluginResult("speech", "not_implemented", context, "Scaffold only; connect configured ASR provider.")
