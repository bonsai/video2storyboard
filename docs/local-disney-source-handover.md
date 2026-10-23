# Local source-video handover: Disney public-domain shorts

Date: 2026-10-23
Repository: https://github.com/bonsai/video2storyboard

## Goal

Run the video-to-storyboard pipeline locally with a real, short animated film after the synthetic-video smoke test. Keep the source video on the local machine. Do not upload it to Colab or any cloud service automatically.

## Recommended source

### First choice: Steamboat Willie (1928)

- Source page: https://commons.wikimedia.org/wiki/File:Steamboat_Willie_(1928)_by_Walt_Disney.webm
- Work: the original 1928 black-and-white animated short, approximately 7 minutes 40 seconds.
- Why: clear character motion, scene changes, backgrounds, and synchronized sound make it a useful end-to-end storyboard test.
- Rights note: Wikimedia Commons identifies the underlying work as public domain in the United States. This does not automatically establish public-domain status in every country, and a restoration or digital encoding can have separate terms. Review the file page's current licensing and jurisdiction notes before reuse.

### Additional candidates

1. **The Skeleton Dance (1929)** — useful for music-synchronized movement, multiple figures, and changing compositions. Check the exact source file and its rights statement before use.
   - Background reference: https://legalclarity.org/which-disney-characters-are-public-domain/
2. **The Chain Gang (1930)** — useful for chase/action shot segmentation. This 1930 short entered the US public domain on 2026-01-01; that statement is US-specific and does not establish worldwide status.
   - Background reference: https://legalclarity.org/which-disney-characters-are-public-domain/

## Local setup

Use the source file obtained from the source page above. Keep the original filename and record its SHA-256 before processing.

1. Create the input directory in the local clone if it does not exist: `data/input/`.
2. Download the chosen file manually from the source page and save it as `data/input/steamboat-willie-1928.webm`.
3. Do not commit the video to Git. Keep it out of cloud sync and remote bundles unless the user explicitly chooses otherwise.
4. Record provenance in a local note: source page URL, retrieval date, original filename, file size, SHA-256, and the jurisdiction/license statement displayed by the source.

PowerShell example from the repository root:

```powershell
New-Item -ItemType Directory -Force data/input | Out-Null
Get-FileHash .\data\input\steamboat-willie-1928.webm -Algorithm SHA256
ffprobe -hide_banner .\data\input\steamboat-willie-1928.webm
```

If `ffprobe` is not on PATH, verify FFmpeg is installed before proceeding. Do not rename a WebM file to .mp4; convert only if the pipeline requires it.

## Local test sequence

1. Run the existing unit tests first:
   ```powershell
   $env:PYTHONPATH = "src"
   python -m pytest -q
   ```
2. Run the repository's documented synthetic-video smoke test / full graph entry point. Check the current README and CLI help before assuming a command; do not invent a CLI that the repository does not provide.
3. Run the storyboard flow against the local source, using the repository's documented input contract.
4. Inspect the generated storyboard JSON and all referenced keyframe/thumbnail paths. Open the HTML/SVG output if generated.
5. Record the result, missing dependencies, model used, elapsed time, and any failed stage. The known local VLM endpoint is LM Studio at `http://127.0.0.1:1234/v1`; do not add cloud fallback.
6. Keep a clear distinction between a successful model probe and a successful full end-to-end graph run.

## Colab handoff boundary

Local execution is the default. Colab is an optional later step for stages that genuinely need a GPU or heavier dependencies.

- Never upload source video automatically.
- Before any upload, ask for explicit confirmation and show exactly which files will be sent.
- Prefer a minimal job bundle with a versioned `job.json`, source hash, configuration, and explicit worker allowlist.
- On return, validate the artifact manifest, file hashes, schema, and referenced image paths locally.
- Do not include API keys, tokens, cookies, or other credentials in the bundle.
- Preserve a fully local path that works without Colab.

## Acceptance checklist

- [ ] Exact source page and license/jurisdiction note recorded.
- [ ] Original source kept local and SHA-256 recorded.
- [ ] Existing tests pass, or failures are captured with exact output.
- [ ] Full graph is run against the real clip, or blockers are documented.
- [ ] Storyboard JSON and referenced image paths are inspected.
- [ ] HTML/SVG outputs are visually checked when present.
- [ ] No source media is uploaded to Colab or committed to Git without explicit approval.

## Rights and scope

This is a technical test-source shortlist, not legal advice. Public-domain status is jurisdiction-specific. Use the original work/version covered by the source's rights statement; do not assume that later restorations, added music, subtitles, logos, or encodings share the same status.