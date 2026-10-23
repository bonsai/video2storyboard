# Pose unit

**Milestone 1:** visibly render the MediaPipe Pose skeleton on local video using the existing implementation.

## Run now

From the repository root, after dependencies are installed:

```powershell
python src/video2storyboard/pose_video.py --input-video "PATH_TO_LOCAL_VIDEO.mp4" --preview
```

- Press **P** to toggle the Pose overlay.
- Press **Q** or **Esc** to quit.

To export a silent overlay video without requiring FFmpeg:

```powershell
python src/video2storyboard/pose_video.py --input-video "PATH_TO_LOCAL_VIDEO.mp4" --output-video "artifacts/pose/pose-overlay.mp4" --no-audio
```

The output path must differ from the source path. This reuses the existing implementation. It does **not yet** create the JSON landmark/JSONL artifacts required by the longer-term API contract.

## Canonical contracts

- Workflow: [`wf/pose.wf.yml`](../../wf/pose.wf.yml)
- Agent work: [`aw/pose.aw.yaml`](../../aw/pose.aw.yaml)
- API contract: [`openapi/pose.yaml`](../../openapi/pose.yaml)
- Artifact schema: [`contracts/pose-artifact.schema.json`](../../contracts/pose-artifact.schema.json)

## Reuse first

Reuse `src/video2storyboard/pose_video.py` and `pose_render.py`; do not introduce a second renderer or install heavyweight tools unnecessarily.

## Acceptance

- [ ] The preview visibly shows the skeleton on a real local input.
- [ ] A silent overlay MP4 can be exported without FFmpeg when requested.
- [ ] Source file remains unchanged.
- [ ] Focused tests pass.

The full contract target additionally requires pose JSON, explicit `detected/no_pose/error` status, a JSONL run record, and artifact validation. These are not claimed implemented by this scaffold.

## Tomorrow

Use timestamped Pose JSON sequences to reconstruct dance motion as a synchronized 2D stick-figure animation.
