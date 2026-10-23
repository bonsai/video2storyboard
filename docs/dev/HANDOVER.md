# Handover: Local LM Studio Check

Date: 2026-10-23
Repository: `bonsai/video2storyboard`
Scope: verify the local-first topology and identify what is ready versus still a scaffold.

## Decision

- Default execution is local.
- VLM inference is intended to use LM Studio's OpenAI-compatible API at `http://127.0.0.1:1234/v1`.
- Cloud execution and cloud inference are disabled by default; no automatic cloud fallback.
- Do not upload source videos, extracted frames, audio, transcripts, or generated storyboards unless explicitly approved.
- Keep this implementation in `video2storyboard`; do not implement the pipeline in `visual-factory`.

## Local verification checklist

### 1. LM Studio server
- [ ] Open LM Studio and load a **vision-capable** model (text-only models will not work for frame descriptions).
- [ ] Start the local server and confirm it listens on port 1234.
- [ ] Check the model IDs returned by `GET http://127.0.0.1:1234/v1/models`.
- [ ] Set `VIDEO2STORYBOARD_VLM_MODEL` to the exact model ID returned by that endpoint.
- [ ] If server authentication is enabled, configure `LM_STUDIO_API_KEY`; otherwise it may be omitted.
- [ ] Verify one image can be sent to `/v1/chat/completions` and the response describes only visible content.

PowerShell quick check:

```powershell
Invoke-RestMethod http://127.0.0.1:1234/v1/models
```

### 2. Python environment and graph imports
- [ ] Use the project's Python environment.
- [ ] Install `requirements.txt`.
- [ ] Ensure the system `ffmpeg` executable is installed and available on PATH (it is not installed by pip requirements).
- [ ] Run `python -m pytest -q`.
- [ ] Confirm importing `video2storyboard.work.storyboard.graph.workflow` compiles the LangGraph graph.

### 3. Small, safe smoke test
Use a short, non-sensitive local video (ideally 5–15 seconds).
- [ ] Confirm the input video opens and metadata is reported.
- [ ] Confirm PNG frames appear under `outputs/<run_id>/frames/`.
- [ ] Confirm MediaPipe returns either landmarks or an explicit `not_detected` status.
- [ ] Confirm OpenCV measurements are returned.
- [ ] Confirm Whisper either returns timestamped segments or a clear worker error.
- [ ] Confirm the local VLM returns valid JSON for at least one frame.
- [ ] Confirm `storyboard.json`, `storyboard.html`, and `storyboard.svg` are written.
- [ ] Open the HTML and check that frame thumbnails load and timestamps match.
- [ ] Confirm no source media or generated artifacts were uploaded to cloud services.

## Important implementation gap

The current `eye_meaning_vlm` worker still expects `config["vlm_callable"]`. The topology declares the LM Studio endpoint, but the worker does **not yet** construct an OpenAI-compatible image request from `topology.yaml`. Therefore, a successful LM Studio API check alone does not prove the full pipeline is connected.

Also check the HTML image paths: the current storyboard builder may emit paths relative to the output root, while `storyboard.html` is stored inside the run directory. If thumbnails do not load, fix the relative path before calling the smoke test successful.

## Report back

Please note:
1. Python version and whether `pytest` passes.
2. Whether `/v1/models` responds and the vision model ID (do not share API keys).
3. Whether a single image prompt works in LM Studio.
4. The first error message from the pipeline, if any.
5. Whether output JSON, HTML, SVG and thumbnails are present.

Do not paste API keys, tokens, private videos, or private transcripts into an issue or chat.

## OpenCode MCP integration (2026-10-23)

Implementation entrypoint: `src/video2storyboard/mcp_server.py`.

GitHub issue: https://github.com/bonsai/video2storyboard/issues/2

### Tools exposed to OpenCode
- `video2storyboard_check_local`: checks installed packages, FFmpeg, and LM Studio's local `/v1/models` endpoint.
- `video2storyboard_analyze`: invokes LangGraph for a local video, supplying a local-only LM Studio image adapter.
- `video2storyboard_get_run`: inspects storyboard JSON/HTML/SVG outputs and panel count.

### Local setup
1. Install updated dependencies: `python -m pip install -r requirements.txt`.
2. Start LM Studio's local server and load a vision-capable model.
3. Set `VIDEO2STORYBOARD_VLM_MODEL` to an exact model ID returned by `http://127.0.0.1:1234/v1/models`.
4. Add the OpenCode config entry from the README, with absolute paths for the repository, Python executable and `src` directory.
5. Restart OpenCode, then run `opencode mcp list` and call `video2storyboard_check_local`.

### Before calling this complete
- Run `python -m pytest -q` in the project environment.
- Run a short, non-sensitive local video end-to-end.
- Verify HTML thumbnails load; storyboard image paths were adjusted to be relative to the run directory.
- Confirm MCP tool discovery and execution in OpenCode.
- Do not send source videos, extracted frames, transcripts or generated artifacts to cloud services. There is no cloud inference fallback.

The code and tests have been committed, but a successful local test run has not yet been confirmed.

