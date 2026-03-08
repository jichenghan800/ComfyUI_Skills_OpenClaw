from __future__ import annotations

from pathlib import Path

from shared.config import (
    DATA_DIR,
    get_server_schemas_dir,
    get_server_workflows_dir,
)
from shared.runtime_config import get_runtime_config

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "ui" / "static"
CONFIG_PATH = BASE_DIR / "config.json"
CONFIG_EXAMPLE_PATH = BASE_DIR / "config.example.json"
OUTPUTS_DIR = BASE_DIR / "outputs"

# Legacy flat paths kept for backwards compat in UI json_store reads
WORKFLOWS_DIR = DATA_DIR / "workflows"
SCHEMAS_DIR = DATA_DIR / "schemas"

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8189
DEFAULT_COMFYUI_SERVER_URL = "http://127.0.0.1:8188"


def ensure_runtime_dirs() -> None:
    """Create data directories for all configured servers."""
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

    config = get_runtime_config()
    for server in config.get("servers", []):
        server_id = server.get("id")
        if server_id:
            get_server_workflows_dir(server_id).mkdir(parents=True, exist_ok=True)
            get_server_schemas_dir(server_id).mkdir(parents=True, exist_ok=True)


def default_config() -> dict[str, str]:
    return {
        "comfyui_server_url": DEFAULT_COMFYUI_SERVER_URL,
        "output_dir": "./outputs",
    }
