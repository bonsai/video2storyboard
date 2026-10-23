from video2storyboard.graph.workflow import build_graph


def test_graph_compiles_and_exposes_worker_nodes():
    graph = build_graph()
    assert graph is not None
    # Compiled LangGraph exposes a graph representation with the registered nodes.
    drawable = graph.get_graph()
    names = set(drawable.nodes)
    for expected in {
        "ingest_video", "video2png", "eye_pose_mp", "eye_composition_cv2",
        "eye_meaning_vlm", "ear_stt_whisper", "hand_storyboard_builder",
        "paper_html_svg", "validate_storyboard",
    }:
        assert expected in names
