# MAP — video2storyboard

## Responsibility

`video2storyboard` is the canonical video-to-storyboard engine. LangGraph orchestrates the workflow; plugin modules describe focused capabilities. YAML configures stage order/enabling. Storyboard JSON is canonical data; JSONL is suitable for append-only execution records.

## Plugin map

| Order | Plugin ID | Responsibility | Typical outputs |
|---:|---|---|---|
| 1 | `ingest` | Validate source and read metadata | `video_metadata` |
| 2 | `scene_detection` | Detect scene boundaries | `scenes` |
| 3 | `keyframes` | Sample and persist frames | `frames` |
| 4 | `pose` | MediaPipe landmarks and overlays | `pose_results`, `pose_overlays` |
| 5 | `composition` | OpenCV visual measurements | `composition_metrics` |
| 6 | `vision` | VLM scene interpretation | `visual_descriptions` |
| 7 | `speech` | Audio transcription | `transcript` |
| 8 | `storyboard` | Build canonical storyboard JSON | `storyboard_json` |
| 9 | `export` | HTML/SVG/media output | `exported_artifacts` |
| 10 | `validation` | Validate schemas and artifacts | `validation_report` |

## Structure

- `src/video2storyboard/plugins/contract.py`: shared context/result/spec contract.
- `src/video2storyboard/plugins/registry.py`: deterministic plugin registry.
- `src/video2storyboard/plugins/*.py`: one focused plugin definition per module.
- `config/plugin-pipeline.yaml`: starter stage configuration.
- `docs/adr/0002-rainbow-mediapipe-pose-overlay.md`: pose overlay decision record.
- `tests/test_plugin_registry.py`: registry and contract smoke tests.

## Current status

This is scaffolding only. Plugin modules return `not_implemented` until connected to the existing implementations. The existing LangGraph graph remains the workflow orchestrator; do not replace it with a second orchestration system.
