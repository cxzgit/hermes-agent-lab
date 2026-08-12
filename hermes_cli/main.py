"""Outer command entry, corresponding to hermes_cli/main.py in Hermes."""

from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mini-hermes")
    parser.add_argument("command", nargs="?", choices=("chat",))
    return parser


def cmd_chat() -> None:
    print("[1] hermes_cli.main.cmd_chat -> cli.main")
    from cli import main as cli_main

    cli_main()


def main() -> None:
    """Entry called by the mini-hermes command in pyproject.toml."""
    args = build_parser().parse_args()
    if args.command is None or args.command == "chat":
        cmd_chat()


if __name__ == "__main__":
    main()

