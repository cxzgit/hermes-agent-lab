"""Outer command entry, corresponding to hermes_cli/main.py in Hermes."""

from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mini-hermes")
    parser.add_argument("command", nargs="?", choices=("chat",))
    parser.add_argument(
        "--resume",
        metavar="SESSION_ID",
        help="resume a previously persisted conversation",
    )
    return parser


def cmd_chat(*, model: str, base_url: str, session_id: str | None = None) -> None:
    print("[1] hermes_cli.main.cmd_chat -> cli.main")
    from cli import main as cli_main

    cli_main(model=model, base_url=base_url, session_id=session_id)


def main() -> None:
    """Entry called by the mini-hermes command in pyproject.toml."""
    args = build_parser().parse_args()
    from hermes_cli.config import load_model_settings

    settings = load_model_settings()
    if args.command is None or args.command == "chat":
        cmd_chat(
            model=settings.name,
            base_url=settings.base_url,
            session_id=args.resume,
        )


if __name__ == "__main__":
    main()
