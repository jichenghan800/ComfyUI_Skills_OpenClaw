from __future__ import annotations

import os
import json
import uuid
import time
import argparse
import urllib.request
import urllib.parse
import sys
import re
from logging import getLogger

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from shared.config import get_server_schema_path, get_server_workflow_path
from shared.json_utils import load_json
from shared.runtime_config import get_server_by_id, get_default_server_id
from shared.schema_aliases import build_unique_parameter_alias_map, get_display_parameter_name

logger = getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def is_valid_identifier(value: str) -> bool:
    """Reject path-like identifiers to prevent path traversal."""
    if not value:
        return False
    if value in {".", ".."}:
        return False
    if any(sep in value for sep in ("/", "\\")):
        return False
    return True


def parse_workflow_arg(workflow_arg: str) -> tuple[str, str]:
    """Parse a composite workflow argument like 'server_id/workflow_id'.

    If no '/' is present, uses the default server.
    Returns (server_id, workflow_id).
    """
    if "/" in workflow_arg:
        parts = workflow_arg.split("/", 1)
        return parts[0], parts[1]
    else:
        return get_default_server_id(), workflow_arg


def sanitize_filename_part(value: str, fallback: str) -> str:
    """Build a readable, filesystem-safe filename component."""
    normalized = re.sub(r"[^A-Za-z0-9._-]+", "-", (value or "").strip())
    normalized = re.sub(r"-{2,}", "-", normalized).strip("._-")
    return normalized or fallback


def get_output_prefix(workflow_id: str, input_args: dict, parameters: dict) -> str:
    """Prefer an explicit filename_prefix arg, otherwise fall back to workflow_id."""
    for key, param in parameters.items():
        if param.get("field") == "filename_prefix" and key in input_args:
            return sanitize_filename_part(str(input_args[key]), workflow_id)

    raw_prefix = input_args.get("filename_prefix")
    if raw_prefix is not None:
        return sanitize_filename_part(str(raw_prefix), workflow_id)

    return sanitize_filename_part(workflow_id, "image")


def build_output_filename(prefix: str, timestamp: str, index: int, original_filename: str) -> str:
    """Create a stable, readable local filename for downloaded images."""
    _, ext = os.path.splitext(original_filename)
    ext = ext or ".png"
    return f"{prefix}_{timestamp}_{index:02d}{ext}"


def coerce_parameter_value(value, param_type: str):
    if param_type == "int":
        return int(value)
    if param_type == "float":
        return float(value)
    if param_type == "boolean":
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"true", "1", "yes", "on"}:
                return True
            if normalized in {"false", "0", "no", "off"}:
                return False
        raise ValueError(f"Cannot coerce value '{value}' to boolean")
    return value


def resolve_input_args(parameters: dict, input_args: dict) -> tuple[dict, list[str], str | None]:
    alias_map = build_unique_parameter_alias_map(parameters)
    resolved_args: dict = {}
    unknown_keys: list[str] = []
    seen_inputs_for_target: dict[str, str] = {}

    for input_key, value in input_args.items():
        target_key = input_key
        if input_key not in parameters:
            target_key = alias_map.get(input_key, "")

        if not target_key:
            unknown_keys.append(input_key)
            continue

        previous_source = seen_inputs_for_target.get(target_key)
        if previous_source and previous_source != input_key:
            display_name = get_display_parameter_name(target_key, parameters)
            return {}, [], f"Duplicate values provided for parameter '{display_name}'"

        seen_inputs_for_target[target_key] = input_key
        resolved_args[target_key] = value

    return resolved_args, unknown_keys, None


def queue_prompt(server_url, prompt_workflow):
    data = json.dumps({"prompt": prompt_workflow, "client_id": str(uuid.uuid4())}).encode('utf-8')
    req = urllib.request.Request(f"{server_url}/prompt", data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read())
    except urllib.error.URLError as e:
        print(f"Error connecting to ComfyUI ({server_url}): {e}")
        return None


def get_history(server_url, prompt_id):
    req = urllib.request.Request(f"{server_url}/history/{prompt_id}")
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read())
    except urllib.error.URLError:
        return None


def get_image(server_url, filename, subfolder, folder_type):
    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    url_values = urllib.parse.urlencode(data)
    req = urllib.request.Request(f"{server_url}/view?{url_values}")
    try:
        with urllib.request.urlopen(req) as response:
            return response.read()
    except urllib.error.URLError:
        return None


def main():
    parser = argparse.ArgumentParser(description="ComfyUI Client for OpenClaw Skill")
    parser.add_argument("--workflow", required=True,
                        help="Workflow identifier: '<server_id>/<workflow_id>' or just '<workflow_id>' (uses default server)")
    parser.add_argument("--args", required=True, help="JSON string of parameter key-values mapping to the schema")

    args = parser.parse_args()

    # 1. Parse composite workflow argument
    server_id, workflow_id = parse_workflow_arg(args.workflow)
    if not is_valid_identifier(server_id):
        print(json.dumps({"error": "Invalid server id in --workflow"}))
        return
    if not is_valid_identifier(workflow_id):
        print(json.dumps({"error": "Invalid workflow id in --workflow"}))
        return

    # 2. Look up server config
    server = get_server_by_id(server_id)
    if not server:
        print(json.dumps({"error": f"Server '{server_id}' not found in config.json"}))
        return

    if not server.get("enabled", True):
        print(json.dumps({"error": f"Server '{server_id}' is disabled"}))
        return

    server_url = server.get("url", "http://127.0.0.1:8188")
    output_dir = server.get("output_dir", os.path.join(BASE_DIR, "outputs"))

    # Resolve relative output_dir
    if not os.path.isabs(output_dir):
        output_dir = os.path.join(BASE_DIR, output_dir)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    # 3. Parse input arguments
    try:
        input_args = json.loads(args.args)
    except json.JSONDecodeError:
        print(json.dumps({"error": "Invalid JSON format for --args"}))
        return

    if not isinstance(input_args, dict):
        print(json.dumps({"error": "--args must decode to a JSON object"}))
        return

    # 4. Load Workflow and Schema from server-specific directory
    wf_path = str(get_server_workflow_path(server_id, workflow_id))
    schema_path = str(get_server_schema_path(server_id, workflow_id))

    if not os.path.exists(wf_path):
        print(json.dumps({"error": f"Workflow file not found for '{server_id}/{workflow_id}'"}))
        return

    if not os.path.exists(schema_path):
        print(json.dumps({"error": f"Schema file not found for '{server_id}/{workflow_id}'"}))
        return

    workflow_data = load_json(wf_path)
    schema_data = load_json(schema_path)

    # Check workflow enabled
    if not schema_data.get("enabled", True):
        print(json.dumps({"error": f"Workflow '{workflow_id}' is disabled on server '{server_id}'"}))
        return

    parameters = schema_data.get("parameters", {})
    resolved_args, unknown_keys, resolve_error = resolve_input_args(parameters, input_args)
    if resolve_error:
        print(json.dumps({"error": resolve_error}))
        return

    if unknown_keys:
        print(json.dumps({
            "error": "Unknown workflow parameter(s)",
            "unknown": unknown_keys,
        }))
        return

    missing_required = [
        get_display_parameter_name(param_key, parameters)
        for param_key, param_info in parameters.items()
        if param_info.get("required", False) and param_key not in resolved_args
    ]
    if missing_required:
        print(json.dumps({
            "error": "Missing required workflow parameter(s)",
            "missing": missing_required,
        }))
        return

    # 5. Map parameters to workflow nodes
    for key, value in resolved_args.items():
        if key in parameters:
            node_id = str(parameters[key]["node_id"])
            field = parameters[key]["field"]
            if node_id in workflow_data and "inputs" in workflow_data[node_id]:
                param_type = parameters[key].get("type", "string")
                try:
                    value = coerce_parameter_value(value, param_type)
                except (TypeError, ValueError):
                    display_name = get_display_parameter_name(key, parameters)
                    print(json.dumps({
                        "error": f"Invalid value for parameter '{display_name}'",
                        "expected_type": param_type,
                    }))
                    return

                workflow_data[node_id]["inputs"][field] = value

    output_prefix = get_output_prefix(workflow_id, resolved_args, parameters)

    # 6. Queue Prompt
    queue_res = queue_prompt(server_url, workflow_data)
    if not queue_res or 'prompt_id' not in queue_res:
        print(json.dumps({"error": "Failed to queue prompt to ComfyUI."}))
        return

    prompt_id = queue_res['prompt_id']

    # 7. Poll for completion via history
    while True:
        history = get_history(server_url, prompt_id)
        if history and prompt_id in history:
            job_info = history[prompt_id]
            break
        time.sleep(2)

    # 8. Extract images
    if 'outputs' not in job_info:
        print(json.dumps({"error": "No outputs found in job execution."}))
        return

    downloaded_files = []
    run_timestamp = f"{time.strftime('%Y%m%d-%H%M%S')}-{int((time.time() % 1) * 1000):03d}"
    image_index = 1

    for node_id, node_output in job_info['outputs'].items():
        if 'images' in node_output:
            for image in node_output['images']:
                filename = image['filename']
                subfolder = image.get('subfolder', '')
                folder_type = image.get('type', 'output')

                img_data = get_image(server_url, filename, subfolder, folder_type)
                if img_data:
                    local_filename = build_output_filename(
                        output_prefix,
                        run_timestamp,
                        image_index,
                        filename,
                    )
                    local_filepath = os.path.join(output_dir, local_filename)
                    with open(local_filepath, "wb") as f:
                        f.write(img_data)
                    downloaded_files.append(local_filepath)
                    image_index += 1

    # Output the JSON result
    print(json.dumps({
        "status": "success",
        "server": server_id,
        "prompt_id": prompt_id,
        "images": downloaded_files,
    }))


if __name__ == "__main__":
    main()
