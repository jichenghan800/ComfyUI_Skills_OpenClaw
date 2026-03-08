from __future__ import annotations

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = BASE_DIR / "config.json"
DATA_DIR = BASE_DIR / "data"
OUTPUTS_DIR = BASE_DIR / "outputs"
DEFAULT_COMFYUI_SERVER_URL = "http://127.0.0.1:8188"
DEFAULT_SERVER_ID = "local"


def default_server() -> dict[str, object]:
    return {
        "id": DEFAULT_SERVER_ID,
        "name": "Local",
        "url": DEFAULT_COMFYUI_SERVER_URL,
        "enabled": True,
        "output_dir": str(OUTPUTS_DIR),
    }


def default_config() -> dict[str, object]:
    return {
        "servers": [default_server()],
        "default_server": DEFAULT_SERVER_ID,
    }


def get_server_data_dir(server_id: str) -> Path:
    """Return the data directory for a specific server."""
    return DATA_DIR / server_id


def get_server_workflows_dir(server_id: str) -> Path:
    return get_server_data_dir(server_id) / "workflows"


def get_server_schemas_dir(server_id: str) -> Path:
    return get_server_data_dir(server_id) / "schemas"
