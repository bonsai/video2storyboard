# Demos

This directory contains **independent, runnable experiments**. They are not interchangeable implementations of one pipeline; choose by the output you want.

## Demo index

| Demo | Purpose | Input | Output | Runtime |
|---|---|---|---|---|
| [manga-cam](./manga-cam/) | Convert a camera/video frame into manga-like line art and optionally overlay MediaPipe Pose | Webcam or video file | Live preview; optionally saved video/frames | Python + OpenCV; MediaPipe for pose; optional Transformers/PyTorch for building segmentation |
| [mp-py-p5-java](./mp-py-p5-java/) | Separate pose detection from stylized drawing: Python sends landmarks over OSC to Processing | Webcam or video file | Live Processing sketch | Python + MediaPipe + python-osc; Processing + oscP5 |

## Which should I run?

- **Try manga line-art quickly:** start with [manga-cam README](./manga-cam/README.md).
- **Experiment with a separate detector and renderer:** use [mp-py-p5-java README](./mp-py-p5-java/README.md).
- **Inspect the architecture:** each demo keeps its own PlantUML/system map and implementation notes.

## Boundaries

- Keep demo-specific dependencies and launch instructions inside each demo folder.
- Do not move source videos, generated frames, model weights, or local environment files into Git.
- Keep the demos independent from the production storyboard graph. Promote shared functionality into `src/` only after defining and testing an explicit input/output contract.
- Treat the README as usage documentation, not evidence that a runtime path has been tested on every OS.
- The current CI workflow runs the repository's Python tests; it does not automatically validate Processing, Java, webcam, OSC, or optional building-segmentation paths.

## Validation checklist

1. Install the dependencies listed by the selected demo.
2. Run against a short local video before using a webcam.
3. Confirm that the input opens, frames are processed, and output is produced.
4. For OSC, start the Processing receiver before the Python sender and verify both use the same IP/port.
5. Record the OS, Python/MediaPipe versions, command, and observed result when reporting a failure.
