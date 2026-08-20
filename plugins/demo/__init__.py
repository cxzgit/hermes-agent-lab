"""Example Mini Hermes plugin."""


def _repeat(args: dict) -> str:
    text = str(args.get("text", ""))
    count = int(args.get("count", 1))
    return " ".join([text] * max(0, min(count, 5)))


def register(ctx) -> None:
    ctx.register_tool(
        name="plugin_repeat",
        toolset="plugin",
        schema={
            "description": "Repeat short text using the demo plugin.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "count": {"type": "integer", "minimum": 0, "maximum": 5},
                },
                "required": ["text"],
            },
        },
        handler=_repeat,
    )
