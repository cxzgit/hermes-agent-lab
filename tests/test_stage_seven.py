import unittest

from model_tools import get_tool_definitions, handle_function_call
from hermes_cli.plugins import get_plugin_manager


class StageSevenPluginTests(unittest.TestCase):
    def test_manifest_and_register_entrypoint_load(self) -> None:
        manager = get_plugin_manager()
        manager.discover_and_load()
        self.assertIn("demo", manager.plugins)
        self.assertEqual(handle_function_call("plugin_repeat", {"text": "hi", "count": 2}), "hi hi")

    def test_plugin_tool_schema_is_visible_to_model(self) -> None:
        names = {item["function"]["name"] for item in get_tool_definitions()}
        self.assertIn("plugin_repeat", names)


if __name__ == "__main__":
    unittest.main()
