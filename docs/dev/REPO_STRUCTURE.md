# video2storyboard — Repository Structure Policy

## Root

The root contains only repository-wide configuration, entry scripts, and project guides.

- `src/` — Python source
- `tests/` — pytest suite
- `docs/`, `standards/`, `units/` — product and engineering documentation
- `config/`, `schemas/`, `examples/`, `wf/` — runtime definitions and examples
- `backends/`, `mcp/`, `models/` — external-runtime adapters, MCP entrypoint, and model assets
- `pipeline1_video_to_dance.py`, `pipeline2_dance_to_3d.py` — standalone entry scripts

## Source package layout

Source is grouped by the work it performs. Do not add feature modules directly under
`src/video2storyboard/`.

```
src/video2storyboard/
├── work/
│   ├── pose/                     # detect, render, preview, and layer pose data
│   │   ├── pose_tasks.py
│   │   ├── pose_render.py
│   │   ├── pose_video.py
│   │   └── pose_layer_image.py
│   ├── dance/                    # dance DSL, canonical IR, and similarity analysis
│   │   ├── dsl.py
│   │   ├── dsl/dance-retarget.yaml
│   │   ├── ir.py
│   │   └── semantic_cube.py
│   └── storyboard/               # reconstruct a storyboard from video
│       ├── graph/                # LangGraph state, nodes, and workflow wiring
│       └── plugins/              # storyboard worker-plugin contracts and registry
└── interfaces/
    ├── mcp.py                    # MCP process interface
    └── worker_api.py             # FastAPI process interface
```

## Import and naming rules

- Import source via `video2storyboard`, never `src.video2storyboard`.
- Use the work-domain path in commands and imports, for example
  `video2storyboard.work.pose.pose_render`.
- Keep implementation and its tests in corresponding work domains; tests remain in
  `tests/` and use the complete public module path.
- Add a new work domain only when it has a distinct user outcome. Infrastructure that
  exposes multiple domains belongs in `interfaces/`.
- Workflow YAML uses `wf/<name>.wf.yml`; backends use `backends/<name>.py`.

## Verification after a move

1. Update every import, CLI command, configuration entrypoint, and documentation link.
2. Run `PYTHONPATH=src pytest -q`.
3. Confirm `find src/video2storyboard -maxdepth 1 -type f` has no feature modules.
