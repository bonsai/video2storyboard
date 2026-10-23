"""Composable processing plugins for the video2storyboard pipeline.

Plugins are small units; LangGraph remains responsible for orchestration.
"""
from .registry import PLUGINS, get_plugin, list_plugins

__all__ = ["PLUGINS", "get_plugin", "list_plugins"]
