from __future__ import annotations

import shutil
from pathlib import Path

from shared.config import (
    CONFIG_PATH,
    DATA_DIR,
    DEFAULT_SERVER_ID,
    default_config,
    default_server,
    get_server_schemas_dir,
    get_server_workflows_dir,
)
from shared.json_utils import load_json, save_json


def migrate_legacy_config() -> None:
    """Detect old flat config format and migrate to the new multi-server format.

    Old format:
        { "comfyui_server_url": "...", "output_dir": "..." }

    New format:
        { "servers": [ { "id": "local", ... } ], "default_server": "local" }

    Also migrates data/workflows/ and data/schemas/ into data/local/.
    """
    if not CONFIG_PATH.exists():
        return

    config = load_json(CONFIG_PATH)
    if not isinstance(config, dict):
        return

    # Already in new format
    if "servers" in config:
        return

    # Detect legacy flat format
    old_url = config.get("comfyui_server_url")
    old_output = config.get("output_dir")

    server = default_server()
    if old_url:
        server["url"] = old_url
    if old_output:
        server["output_dir"] = old_output

    new_config = {
        "servers": [server],
        "default_server": DEFAULT_SERVER_ID,
    }
    save_json(CONFIG_PATH, new_config)

    # Migrate data directories
    old_workflows = DATA_DIR / "workflows"
    old_schemas = DATA_DIR / "schemas"
    new_workflows = get_server_workflows_dir(DEFAULT_SERVER_ID)
    new_schemas = get_server_schemas_dir(DEFAULT_SERVER_ID)

    if old_workflows.exists() and not new_workflows.exists():
        new_workflows.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(old_workflows), str(new_workflows))

    if old_schemas.exists() and not new_schemas.exists():
        new_schemas.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(old_schemas), str(new_schemas))


def get_runtime_config() -> dict[str, object]:
    """Load the full multi-server config, migrating from legacy format if needed."""
    migrate_legacy_config()

    if not CONFIG_PATH.exists():
        return default_config()

    loaded = load_json(CONFIG_PATH)
    if not isinstance(loaded, dict) or "servers" not in loaded:
        return default_config()

    return loaded


def get_server_by_id(server_id: str) -> dict[str, object] | None:
    """Look up a single server entry by its id."""
    config = get_runtime_config()
    for server in config.get("servers", []):
        if isinstance(server, dict) and server.get("id") == server_id:
            return server
    return None


def get_default_server_id() -> str:
    """Return the default server id from config."""
    config = get_runtime_config()
    return str(config.get("default_server", DEFAULT_SERVER_ID))
