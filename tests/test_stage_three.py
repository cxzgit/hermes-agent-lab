import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from model_tools import get_tool_definitions, handle_function_call
from tools.registry import ToolRegistry


class StageThreeTests(unittest.TestCase):
    def test_registered_schema_is_exposed_to_model(self) -> None:
        definitions = get_tool_definitions()
        names = {item["function"]["name"] for item in definitions}
        self.assertIn("get_current_time", names)

    def test_dispatch_finds_registered_handler(self) -> None:
        zone = ZoneInfo("Asia/Shanghai")
        before = datetime.now(zone).replace(microsecond=0)
        result = handle_function_call(
            "get_current_time", {"timezone": "Asia/Shanghai"}
        )
        after = datetime.now(zone).replace(microsecond=0)
        prefix = "Asia/Shanghai 的时间是 "
        self.assertTrue(result.startswith(prefix))
        returned = datetime.strptime(
            result.removeprefix(prefix), "%Y-%m-%d %H:%M:%S"
        ).replace(tzinfo=zone)
        self.assertLessEqual(before, returned)
        self.assertLessEqual(returned, after)

    def test_unknown_tool_returns_error(self) -> None:
        self.assertEqual(
            handle_function_call("missing_tool", {}),
            "Unknown tool: missing_tool",
        )

    def test_duplicate_registration_is_rejected(self) -> None:
        registry = ToolRegistry()
        schema = {"description": "demo", "parameters": {"type": "object"}}
        registry.register(
            name="demo", toolset="demo", schema=schema, handler=lambda args: "ok"
        )
        with self.assertRaises(ValueError):
            registry.register(
                name="demo",
                toolset="demo",
                schema=schema,
                handler=lambda args: "again",
            )


if __name__ == "__main__":
    unittest.main()
