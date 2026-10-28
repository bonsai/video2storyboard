#!/usr/bin/env python3
"""mp_osc_sender.py
MediaPipe Pose (Python) で骨格を検出し、OSC で Processing に送信する

送信先: 127.0.0.1:9000
アドレス:
  /mppose/start
  /mppose/landmark  [idx, x, y, z, visibility]  (正規化座標 0-1)
  /mppose/frame     [frame_idx, width, height, fps]
  /mppose/end
"""

import argparse
import time

import cv2
import mediapipe as mp
from pythonosc import udp_client

mp_pose = mp.solutions.pose


def main():
    ap = argparse.ArgumentParser(description="MediaPipe Pose -> OSC sender")
    ap.add_argument("--input", default="0", help="0=webcam or path to video")
    ap.add_argument("--ip", default="127.0.0.1", help="OSC target IP")
    ap.add_argument("--port", type=int, default=9000, help="OSC target port")
    ap.add_argument("--model", type=int, default=1, choices=[0, 1, 2], help="Pose model_complexity")
    ap.add_argument("--min-det", type=float, default=0.5)
    ap.add_argument("--min-track", type=float, default=0.5)
    ap.add_argument("--mirror", action="store_true", help="mirror for webcam preview")
    args = ap.parse_args()

    src = int(args.input) if args.input.isdigit() else args.input
    cap = cv2.VideoCapture(src)
    if not cap.isOpened():
        raise SystemExit(f"Failed to open input: {args.input}")

    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0

    client = udp_client.SimpleUDPClient(args.ip, args.port)
    client.send_message("/mppose/start", [time.time(), w, h, fps])
    print(f"[OSC] sending to {args.ip}:{args.port}  (w={w} h={h} fps={fps:.1f})")
    print("Press 'q' to quit preview")

    pose = mp_pose.Pose(
        static_image_mode=False,
        model_complexity=args.model,
        smooth_landmarks=True,
        enable_segmentation=False,
        min_detection_confidence=args.min_det,
        min_tracking_confidence=args.min_track,
    )

    frame_idx = 0
    t_prev = time.time()
    fps_disp = fps

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            frame_idx += 1

            if args.mirror and isinstance(src, int):
                frame = cv2.flip(frame, 1)

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            res = pose.process(rgb)

            now = time.time()
            dt = now - t_prev
            t_prev = now
            if dt > 0:
                fps_disp = 0.9 * fps_disp + 0.1 * (1.0 / dt)

            client.send_message("/mppose/frame", [frame_idx, w, h, fps_disp])

            if res.pose_landmarks:
                lm_list = res.pose_landmarks.landmark
                for i, lm in enumerate(lm_list):
                    client.send_message("/mppose/landmark", [i, lm.x, lm.y, lm.z, lm.visibility])

            vis = frame.copy()
            if res.pose_landmarks:
                mp.solutions.drawing_utils.draw_landmarks(
                    vis,
                    res.pose_landmarks,
                    mp_pose.POSE_CONNECTIONS,
                    mp.solutions.drawing_utils.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
                    mp.solutions.drawing_utils.DrawingSpec(color=(0, 180, 255), thickness=2),
                )
            cv2.putText(vis, f"OSC -> {args.ip}:{args.port} | {fps_disp:.0f} fps", (10, 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.imshow("mp_osc_sender (q: quit)", vis)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        client.send_message("/mppose/end", [frame_idx, time.time()])
        cap.release()
        cv2.destroyAllWindows()
        pose.close()
        print("[OSC] sent /mppose/end")


if __name__ == "__main__":
    main()
