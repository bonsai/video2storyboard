"""LangGraph wiring for the video-to-storyboard worker pipeline."""
from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from .nodes import (
    ear_stt_whisper, eye_composition_cv2, eye_meaning_vlm, eye_pose_mp,
    hand_storyboard_builder, ingest_video, paper_html_svg, validate_storyboard, video2png,
)
from .state import VideoState


def build_graph(checkpointer=None):
    graph = StateGraph(VideoState)
    graph.add_node("ingest_video", ingest_video)
    graph.add_node("video2png", video2png)
    graph.add_node("eye_pose_mp", eye_pose_mp)
    graph.add_node("eye_composition_cv2", eye_composition_cv2)
    graph.add_node("eye_meaning_vlm", eye_meaning_vlm)
    graph.add_node("ear_stt_whisper", ear_stt_whisper)
    graph.add_node("hand_storyboard_builder", hand_storyboard_builder)
    graph.add_node("paper_html_svg", paper_html_svg)
    graph.add_node("validate_storyboard", validate_storyboard)

    graph.add_edge(START, "ingest_video")
    graph.add_conditional_edges(
        "ingest_video",
        lambda s: "continue" if s.get("status") != "failed" else "stop",
        {"continue": "video2png", "stop": END},
    )
    # Fan out to independent modality workers after the shared frame manifest exists.
    graph.add_edge("video2png", "eye_pose_mp")
    graph.add_edge("video2png", "eye_composition_cv2")
    graph.add_edge("video2png", "eye_meaning_vlm")
    graph.add_edge("video2png", "ear_stt_whisper")
    # A barrier ensures the storyboard builder sees all modality results together.
    graph.add_edge(
        ["eye_pose_mp", "eye_composition_cv2", "eye_meaning_vlm", "ear_stt_whisper"],
        "hand_storyboard_builder",
    )
    graph.add_edge("hand_storyboard_builder", "paper_html_svg")
    graph.add_edge("paper_html_svg", "validate_storyboard")
    graph.add_edge("validate_storyboard", END)
    return graph.compile(checkpointer=checkpointer)


app = build_graph()
