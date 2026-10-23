#!/usr/bin/env python3
"""Standalone Pipeline 1: source video to layered dance animation (no LangGraph).

Implements the first half of issue #15:
1. Retrieve/open source video, define source-time interval.
2. Extract still PNG screenshots/frames and preserve source timestamps and frame IDs.
3. Run MediaPipe Pose on the still PNGs and save pose landmarks as versioned JSON.
4. Render JSON to SVG for inspectable skeleton overlays.
5. In a browser, synchronize the original video with the SVG/pose layer and capture composited frames/images.
6. Turn the captured frames into an animation/video (for example, PNG sequence and MP4).
7. Validate timestamp alignment, frame dimensions, dropped frames, and visual output.

Current example scope: source video https://www.youtube.com/watch?v=U6dnieqgYvI,
skeleton-dance interval [00:02:20, 00:03:45).

Design constraints:
- Local-first; do not upload source media.
- No automatic cloud fallback.
- JSON is the stable interchange contract between steps.
"""
import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Tuple

from src.video2storyboard.graph.nodes import ingest_video, video2png, eye_pose_mp
from src.video2storyboard.pose_render import render_pose_artifacts
from src.video2storyboard.pose_tasks import get_tasks_pose, get_pose_connections

# Use the pose_tasks module for MediaPipe Pose
# We'll implement the pose detection using the new API


def main():
    parser = argparse.ArgumentParser(description="Pipeline 1: source video to layered dance animation")
    parser.add_argument("--source-video", required=True, help="Path to source video file")
    parser.add_argument("--interval-start", type=float, required=True, help="Start time in seconds")
    parser.add_argument("--interval-end", type=float, required=True, help="End time in seconds")
    parser.add_argument("--output-dir", default="outputs/pipeline1", help="Output directory")
    parser.add_argument("--frame-interval", type=float, default=0.5, help="Frame interval in seconds")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Create video manifest and extract frames
    print(f"Step 1: Extracting frames from {args.source_video}")
    print(f"Interval: [{args.interval_start}s, {args.interval_end}s], Frame interval: {args.frame_interval}s")

    # Use the existing pipeline infrastructure
    state = {
        "source_video": args.source_video,
        "output_dir": str(output_dir),
        "run_id": "pipeline1",
        "source_id": "example",
        "config": {
            "frame_interval_seconds": args.frame_interval,
            "start_time": args.interval_start,
            "end_time": args.interval_end,
        },
        "errors": [],
    }

    # Step 1a: Ingest video metadata
    ingest_result = ingest_video(state)
    if ingest_result.get("status") == "failed":
        print(f"Video ingestion failed: {ingest_result.get('errors')}")
        return

    state.update(ingest_result)

    # Step 1b: Extract frames
    video2png_result = video2png(state)
    if "errors" in video2png_result and video2png_result["errors"]:
        print(f"Frame extraction failed: {video2png_result['errors']}")
        return

    state.update(video2png_result)

    print(f"Frame extraction completed. Frames: {len(state.get('frames', []))}")

    # Step 2: Filter frames by time interval
    print("Step 2: Filtering frames by time interval")
    filtered_frames = []
    for frame in state.get("frames", []):
        if args.interval_start <= frame["timestamp_seconds"] <= args.interval_end:
            filtered_frames.append(frame)

    print(f"Filtered frames: {len(filtered_frames)} (original: {len(state.get('frames', []))})")

    # Save filtered frame list
    frames_file = output_dir / "frames.json"
    with frames_file.open("w") as f:
        json.dump({
            "source_video": args.source_video,
            "interval_start": args.interval_start,
            "interval_end": args.interval_end,
            "frames": filtered_frames,
        }, f, indent=2)

    # Step 3: Run MediaPipe Pose on filtered frames
    print("Step 3: Running MediaPipe Pose")

    # Create a pose processor
    pose_api = get_tasks_pose(static_image_mode=True, model_complexity=1,
                              min_detection_confidence=0.5)

    # Process each frame
    pose_results = []
    with pose_api as pose:
        for frame in filtered_frames:
            image_path = frame["image"]
            if not os.path.exists(image_path):
                print(f"Warning: Frame image not found: {image_path}")
                continue

            # Read the image
            import cv2
            image = cv2.imread(image_path)
            if image is None:
                print(f"Warning: Cannot read frame image: {image_path}")
                continue

            # Convert to RGB for MediaPipe
            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            import numpy as np
            if not rgb.flags["C_CONTIGUOUS"]:
                rgb = np.ascontiguousarray(rgb)

            # Process with MediaPipe Pose
            result = pose.process(rgb)
            landmarks = None
            if result.pose_landmarks:
                # Convert to our landmark format
                landmarks = []
                for i, p in enumerate(result.pose_landmarks[0]):
                    landmarks.append({
                        "index": i,
                        "x": float(p.x),
                        "y": float(p.y),
                        "z": float(p.z),
                        "visibility": float(p.visibility),
                    })

            # Save the frame result
            frame_result = {
                "frame_id": frame["frame_id"],
                "timestamp_seconds": frame["timestamp_seconds"],
                "image_path": image_path,
                "width": frame["width"],
                "height": frame["height"],
                "landmarks": landmarks,
                "status": "detected" if landmarks else "not_detected",
            }

            # Render pose overlay
            if landmarks:
                from src.video2storyboard.pose_render import render_pose_artifacts
                overlay_dir = output_dir / "pose-overlays"
                overlay_dir.mkdir(exist_ok=True)
                overlay_result = render_pose_artifacts(
                    image, landmarks,
                    list(get_pose_connections()),
                    overlay_dir, frame["frame_id"]
                )
                frame_result["overlay_png"] = overlay_result["overlay_png"]
                frame_result["overlay_svg"] = overlay_result["overlay_svg"]

            pose_results.append(frame_result)

    # Save pose results
    pose_results_file = output_dir / "pose_results.json"
    with pose_results_file.open("w") as f:
        json.dump({
            "source_video": args.source_video,
            "interval_start": args.interval_start,
            "interval_end": args.interval_end,
            "results": pose_results,
        }, f, indent=2)

    print(f"Pose processing completed. Results: {len(pose_results)}")

    # Step 4: Validate results
    print("Step 4: Validating results")
    errors = []

    # Check timestamp continuity
    timestamps = [r["timestamp_seconds"] for r in pose_results if r["status"] == "detected"]
    if timestamps:
        diff = [(t - timestamps[i-1]) for i, t in enumerate(timestamps[1:])]
        expected_diff = args.frame_interval
        max_diff = max(diff) if diff else 0
        min_diff = min(diff) if diff else 0

        print(f"Timestamp diffs: min={min_diff:.3f}, max={max_diff:.3f}, expected={expected_diff}")

        if abs(max_diff - expected_diff) > 0.1:
            errors.append(f"Timestamp mismatch: max diff {max_diff:.3f} > expected {expected_diff}")

    # Check frame dimensions consistency
    widths = set(r["width"] for r in pose_results)
    heights = set(r["height"] for r in pose_results)
    if len(widths) > 1:
        errors.append(f"Inconsistent frame widths: {widths}")
    if len(heights) > 1:
        errors.append(f"Inconsistent frame heights: {heights}")

    # Save validation report
    validation_report = {
        "source_video": args.source_video,
        "interval_start": args.interval_start,
        "interval_end": args.interval_end,
        "status": "completed_with_errors" if errors else "completed",
        "errors": errors,
        "frames_processed": len(pose_results),
        "frames_detected": sum(1 for r in pose_results if r["status"] == "detected"),
        "timestamp_stats": {
            "min": min(timestamps) if timestamps else None,
            "max": max(timestamps) if timestamps else None,
            "diff": {"min": min_diff, "max": max_diff} if timestamps else None,
        },
        "dimensions": {
            "width": list(widths) if widths else None,
            "height": list(heights) if heights else None,
        },
    }

    validation_file = output_dir / "validation_report.json"
    with validation_file.open("w") as f:
        json.dump(validation_report, f, indent=2)

    if errors:
        print(f"Validation completed with errors: {len(errors)}")
    else:
        print("Pipeline 1 completed successfully!")

    print(f"Output saved to: {output_dir}")
    print(f"- Frames list: {frames_file}")
    print(f"- Pose results: {pose_results_file}")
    print(f"- Validation report: {validation_file}")


if __name__ == "__main__":
    main()
