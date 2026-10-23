from video2storyboard.plugins import get_plugin, list_plugins
from video2storyboard.plugins.contract import PluginContext
from video2storyboard.plugins import ingest


def test_registry_has_ten_unique_plugins():
    plugins = list_plugins()
    ids = [plugin.plugin_id for plugin in plugins]
    assert len(ids) == 10
    assert len(set(ids)) == 10


def test_registry_lookup_returns_expected_spec():
    assert get_plugin("pose").plugin_id == "pose"


def test_unknown_plugin_has_available_plugin_list():
    try:
        get_plugin("does-not-exist")
    except KeyError as exc:
        assert "ingest" in str(exc)
    else:
        raise AssertionError("Unknown plugin must fail")


def test_scaffold_run_is_explicitly_not_implemented():
    result = ingest.run(PluginContext(run_id="test"))
    assert result.status == "not_implemented"
    assert result.plugin_id == "ingest"
