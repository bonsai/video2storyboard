#!/usr/bin/env python3
"""Create a local browser-playable stick-figure dance from timestamped Pose JSONL.

Each line should contain {"frame_id":"f001","timestamp_ms":0,"landmarks":[
{"index":11,"x":0.4,"y":0.2,"visibility":0.99}, ...]}.
Coordinates x/y are normalized to 0..1. Uses only Python's standard library.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
from typing import Any

CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 7), (0, 4), (4, 5), (5, 6), (6, 8),
    (9, 10), (11, 12), (11, 13), (13, 15), (15, 17), (15, 19), (15, 21),
    (12, 14), (14, 16), (16, 18), (16, 20), (16, 22), (11, 23), (12, 24),
    (23, 24), (23, 25), (25, 27), (27, 29), (29, 31), (27, 31),
    (24, 26), (26, 28), (28, 30), (30, 32), (28, 32),
]

def landmark_map(record: dict[str, Any]) -> dict[str, dict[str, float]]:
    raw = record.get("landmarks", record.get("pose_landmarks", []))
    if isinstance(raw, dict):
        raw = raw.get("landmarks", [])
    result = {}
    if not isinstance(raw, list):
        return result
    for position, item in enumerate(raw):
        if not isinstance(item, dict):
            continue
        try:
            index = int(item.get("index", position))
            x, y = float(item["x"]), float(item["y"])
            visibility = float(item.get("visibility", 1.0))
        except (KeyError, TypeError, ValueError):
            continue
        if all(math.isfinite(v) for v in (x, y, visibility)):
            result[str(index)] = {
                "x": min(1.0, max(0.0, x)),
                "y": min(1.0, max(0.0, y)),
                "visibility": min(1.0, max(0.0, visibility)),
            }
    return result

def load_jsonl(path: Path) -> list[dict[str, Any]]:
    frames = []
    with path.open("r", encoding="utf-8-sig") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number}: {exc}") from exc
            if not isinstance(record, dict):
                raise ValueError(f"Line {line_number} must be a JSON object")
            timestamp = record.get("timestamp_ms", len(frames) * 33.333)
            try:
                timestamp = max(0.0, float(timestamp))
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Invalid timestamp_ms on line {line_number}") from exc
            frames.append({
                "frame_id": str(record.get("frame_id", f"frame-{len(frames):06d}")),
                "timestamp_ms": timestamp,
                "landmarks": landmark_map(record),
            })
    if not frames:
        raise ValueError(f"No frame records found in {path}")
    return sorted(frames, key=lambda f: f["timestamp_ms"])

def make_html(frames: list[dict[str, Any]], title: str) -> str:
    data = json.dumps(frames, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    edges = json.dumps(CONNECTIONS)
    safe_title = title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>""" + safe_title + r""" — Stick Figure Dance</title>
<style>
:root{color-scheme:dark;font:16px system-ui,sans-serif;background:#111827;color:#f9fafb}
body{max-width:1000px;margin:24px auto;padding:0 16px}
h1{font-size:1.35rem}p{color:#cbd5e1}
canvas{display:block;width:100%;height:auto;aspect-ratio:16/9;background:white;border-radius:12px}
.controls{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-top:14px}
button,select{font:inherit;padding:8px 12px;border-radius:8px}
input[type=range]{flex:1;min-width:180px}#status{font-variant-numeric:tabular-nums;color:#cbd5e1}
</style></head><body>
<h1>""" + safe_title + r""" — Stick Figure Dance</h1>
<p>Local playback from Pose JSONL. This page makes no network requests.</p>
<canvas id="stage" width="960" height="540" aria-label="Animated stick figure"></canvas>
<div class="controls">
<button id="play">Play</button><button id="restart">Restart</button>
<label>Speed <select id="speed"><option value="0.5">0.5×</option><option value="1" selected>1×</option><option value="1.5">1.5×</option><option value="2">2×</option></select></label>
<input id="seek" type="range" min="0" max="0" value="0" step="1" aria-label="Frame">
<span id="status">Loading…</span></div>
<script>
"use strict";
const FRAMES = """ + data + r""";
const EDGES = """ + edges + r""";
const canvas=document.getElementById("stage"),ctx=canvas.getContext("2d");
const seek=document.getElementById("seek"),playButton=document.getElementById("play");
const status=document.getElementById("status"),speedSelect=document.getElementById("speed");
seek.max=String(Math.max(0,FRAMES.length-1));
let playing=false,current=0,lastTick=0,elapsed=0;
const firstTime=FRAMES.length?FRAMES[0].timestamp_ms:0;
const lastTime=FRAMES.length?FRAMES[FRAMES.length-1].timestamp_ms:0;
function draw(){
 const frame=FRAMES[current];ctx.clearRect(0,0,canvas.width,canvas.height);
 ctx.fillStyle="#fff";ctx.fillRect(0,0,canvas.width,canvas.height);
 if(!frame){status.textContent="No frames";return;}
 const points=new Map();
 for(const [key,p] of Object.entries(frame.landmarks||{}))if(p.visibility>=0.35)points.set(Number(key),p);
 const xy=p=>({x:110+p.x*(canvas.width-220),y:35+p.y*(canvas.height-70)});
 ctx.lineCap="round";ctx.lineJoin="round";ctx.strokeStyle="#111827";ctx.lineWidth=7;
 for(const [a,b] of EDGES){if(!points.has(a)||!points.has(b))continue;
  const p=xy(points.get(a)),q=xy(points.get(b));ctx.beginPath();ctx.moveTo(p.x,p.y);ctx.lineTo(q.x,q.y);ctx.stroke();}
 for(const p of points.values()){const q=xy(p);ctx.beginPath();ctx.arc(q.x,q.y,5,0,Math.PI*2);ctx.fillStyle="#f97316";ctx.fill();}
 ctx.fillStyle="#334155";ctx.font="15px system-ui";ctx.fillText(frame.frame_id,16,26);
 status.textContent=(current+1)+"/"+FRAMES.length+" · "+Math.round(frame.timestamp_ms)+" ms · "+points.size+" joints";
 seek.value=String(current);
}
function nearestFrame(time){
 let lo=0,hi=FRAMES.length-1;
 while(lo<hi){const mid=(lo+hi)>>1;if(FRAMES[mid].timestamp_ms<time)lo=mid+1;else hi=mid;}
 if(lo>0&&Math.abs(FRAMES[lo-1].timestamp_ms-time)<=Math.abs(FRAMES[lo].timestamp_ms-time))return lo-1;
 return lo;
}
function tick(now){
 if(!playing)return;if(!lastTick)lastTick=now;
 elapsed+=(now-lastTick)*Number(speedSelect.value);lastTick=now;
 const target=firstTime+elapsed;
 if(target>=lastTime){current=FRAMES.length-1;playing=false;playButton.textContent="Play";}
 else current=nearestFrame(target);
 draw();if(playing)requestAnimationFrame(tick);
}
playButton.addEventListener("click",()=>{
 if(!FRAMES.length)return;if(current>=FRAMES.length-1){current=0;elapsed=0;}
 playing=!playing;playButton.textContent=playing?"Pause":"Play";lastTick=0;
 if(playing)requestAnimationFrame(tick);
});
document.getElementById("restart").addEventListener("click",()=>{
 playing=false;playButton.textContent="Play";current=0;elapsed=0;lastTick=0;draw();
});
seek.addEventListener("input",()=>{
 playing=false;playButton.textContent="Play";current=Number(seek.value);
 elapsed=FRAMES[current].timestamp_ms-firstTime;draw();
});
draw();
</script></body></html>
"""

def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a local stick-figure dance player from Pose JSONL.")
    parser.add_argument("--input-jsonl", required=True, help="One Pose frame per JSONL line")
    parser.add_argument("--output-html", default="artifacts/pose/stick-figure-dance.html")
    parser.add_argument("--title", default="Pose Dance")
    args = parser.parse_args()
    source = Path(args.input_jsonl).expanduser().resolve()
    output = Path(args.output_html).expanduser().resolve()
    if not source.is_file():
        parser.error(f"Input JSONL not found: {source}")
    if source == output:
        parser.error("Output HTML must not overwrite the input JSONL")
    frames = load_jsonl(source)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(make_html(frames, args.title), encoding="utf-8")
    print(f"Frames: {len(frames)}")
    print(f"Duration: {frames[-1]['timestamp_ms'] - frames[0]['timestamp_ms']:.1f} ms")
    print(f"HTML: {output}")
    print("Open the HTML file in a browser to play the stick-figure animation.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
