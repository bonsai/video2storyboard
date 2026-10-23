# Rainbow Pose Overlay Scaffold

The original video is read-only. Always choose a different output path.

## Export MP4 with source audio

Requires FFmpeg on PATH:

```bash
PYTHONPATH=src python -m video2storyboard.pose_video --input-video input.mp4 --output-video outputs/pose-rainbow.mp4
```

## Export silent MP4

```bash
PYTHONPATH=src python -m video2storyboard.pose_video --input-video input.mp4 --output-video outputs/pose-rainbow-silent.mp4 --no-audio
```

## Interactive preview

Press P to toggle the rainbow pose layer. Press Q or Esc to quit.

```bash
PYTHONPATH=src python -m video2storyboard.pose_video --input-video input.mp4 --preview
```

## Options

- `--visibility-threshold 0.5`: hide low-confidence landmarks.
- `--model-complexity 0`: choose MediaPipe model complexity 0, 1, or 2.
- GIF is not the main output format because it has no audio and is unsuitable for long clips.

## Status

Scaffolding only. Validate with `python -m pytest -q` and a short local clip before production use. Check video/audio synchronization after FFmpeg muxing.
