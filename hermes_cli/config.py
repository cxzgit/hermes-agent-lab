"""Load Mini Hermes settings using the same secret/config split as Hermes."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml
from dotenv import load_dotenv


@dataclass(frozen=True)
class ModelSettings:
    name: str
    base_url: str


def load_model_settings(project_root: Path | None = None) -> ModelSettings:
    root = project_root or Path(__file__).resolve().parents[1]
    load_dotenv(root / ".env", override=False)

    config_path = root / "config.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"Required config file not found: {config_path}")

    raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    model = raw.get("model") or {}
    if not isinstance(model, dict):
        raise ValueError("config.yaml: 'model' must be a mapping")

    name = str(model.get("name") or "").strip()
    base_url = str(model.get("base_url") or "").strip()
    if not name:
        raise ValueError("config.yaml: 'model.name' is required")
    if not base_url:
        raise ValueError("config.yaml: 'model.base_url' is required")

    return ModelSettings(
        name=name,
        base_url=base_url,
    )
