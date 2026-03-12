# ComfyUI Skills for OpenClaw

![ComfyUI Skills Banner](./asset/banner-ui-20250309.jpg)
<p>
  <a href="./README.zh.md">
    <img src="https://img.shields.io/badge/简体中文-README.zh.md-blue?style=flat-square" alt="简体中文" />
  </a>
</p>

This project is a ComfyUI skill integration layer for OpenClaw and other LLM agents. It turns the workflows you build and export from ComfyUI (API format) into callable skills that agents can trigger with natural language.

It converts natural language requests into structured skill arguments, maps them to ComfyUI workflow inputs, submits jobs to ComfyUI, waits for completion, then pulls generated images back to local disk.

## What This Skill Can Do

- Turn your existing ComfyUI workflows into skills that OpenClaw or other agents can call directly
- Let OpenClaw or another agent call workflows deployed across different ComfyUI servers instead of being tied to a single machine
- Reuse the parameters you already exposed, so the agent can understand what each workflow expects
- Upload a workflow once, manage it from the UI, and use it again without rebuilding the whole setup
- Send jobs to ComfyUI, wait for completion, and pull the generated images back to local storage

---

## Installation

### Install As An OpenClaw Skill

OpenClaw creates the default skill directory for you. Install this repository by entering that directory first, then cloning the project:

```bash
cd ~/.openclaw/workspace/skills
git clone https://github.com/HuangYuChuh/ComfyUI_Skills_OpenClaw.git comfyui-skill-openclaw
cd comfyui-skill-openclaw
pip install -r requirements.txt
```

Installed path example:

- `~/.openclaw/workspace/skills/comfyui-skill-openclaw/`

OpenClaw will read `SKILL.md` and call:

- `scripts/registry.py list --agent`
- `scripts/comfyui_client.py --workflow ... --args '...json...'`

Minimal checklist:

1. The project is placed under `~/.openclaw/workspace/skills/`.
2. `SKILL.md` exists at the project root.
3. Python dependencies are installed.
4. `config.json` points to a reachable ComfyUI server.
5. At least one workflow and schema are configured.

### AI-Native Install Via Agent

You can also ask an OpenClaw Agent to install this skill for you.

Use a prompt like this:

```text
Please install this ComfyUI skill into my OpenClaw workspace.

Target path:
~/.openclaw/workspace/skills/comfyui-skill-openclaw/

Requirements:
1. Run `cd ~/.openclaw/workspace/skills` first.
2. Clone this repository into `comfyui-skill-openclaw`.
3. Keep SKILL.md at the project root.
4. Install Python dependencies from requirements.txt.
5. Create config.json from config.example.json if missing.
6. Set the default ComfyUI server URL to http://127.0.0.1:8188 unless I specify another one.
7. Make sure the skill can be discovered by OpenClaw after installation.
```

### 1) Requirements

- Python 3.10+
- A running ComfyUI server (default: `http://127.0.0.1:8188`)

### 2) Prepare runtime config

`config.json` is the runtime config for this project. The CLI, UI, and OpenClaw-facing scripts all use it.

Choose one of these two approaches:

- Manual: create `config.json` from `config.example.json` and fill in your first server yourself
- UI-based (recommended): start the UI first, then add your first server there, and the UI will write it back into `config.json`

`config.json` example:

```json
{
  "servers": [
    {
      "id": "local",
      "name": "Local Mac",
      "url": "http://127.0.0.1:8188",
      "enabled": true,
      "output_dir": "./outputs"
    }
  ],
  "default_server": "local"
}
```


### 3) Start the local UI

- macOS/Linux:
  ```bash
  ./ui/run_ui.sh
  ```
  or double-click `ui/run_ui.command`
- Windows:
  ```bat
  ui\run_ui.bat
  ```

Then open:

- `http://localhost:8189`

### 4) Add your first server and workflow

In the UI:

1. If you have not already configured a server in `config.json`, add a ComfyUI server first.
2. Upload a workflow exported from ComfyUI via **Save (API Format)**.
3. Expose the parameters you want the agent to use.
4. Save the workflow mapping.

### 5) Verify the installation

Check the registry:

```bash
python scripts/registry.py list
```

Run one test job:

```bash
python scripts/comfyui_client.py \
  --workflow local/test \
  --args '{"prompt":"A premium product photo on aged driftwood, warm cinematic light","size":"3:4,1728x2304","seed":20260307}'
```

If successful, output JSON includes local image path(s), for example:

```json
{
  "status": "success",
  "prompt_id": "...",
  "images": ["./outputs/<prompt_id>_...png"]
}
```

## Local Dashboard (UI)

Start dashboard:

- Via OpenClaw or any agent that can run local commands:
  ```bash
  python3 ./ui/open_ui.py
  ```
- macOS/Linux:
  ```bash
  ./ui/run_ui.sh
  ```
  or double-click `ui/run_ui.command`
- Windows:
  ```bat
  ui\run_ui.bat
  ```

Then open:

- `http://localhost:8189`

Use it to configure ComfyUI server URLs, outputs, and manage workflow/schema mapping.

Current highlights:

- Multi-server management with per-server and per-workflow enable/disable controls
- Workflow search, sort, and drag-to-reorder
- Upload workflow JSON and auto-fill workflow ID
- Custom dialogs, dropdowns, and language switching for daily editing
- One-click export/import for migrating the current skill configuration across machines

---

## Multi-Server Management

You can now configure multiple ComfyUI servers, enabling your agent to dispatch workflows across different hardware (e.g., local machines, cloud A100s).

### Concept
- **Dual-Layer Toggles**: Both *servers* and *individual workflows* can be enabled or disabled. A workflow is only visible to the AI agent if **both** the server and the workflow itself are enabled.
- **Namespacing**: Workflows are identified with a composite ID: `<server_id>/<workflow_id>` (e.g., `local/sdxl-base` vs. `cloud-a100/sdxl-base`).

### Configuration via CLI
A built-in CLI tool (`scripts/server_manager.py`) allows server management on headless Linux machines:
```bash
python scripts/server_manager.py list
python scripts/server_manager.py add --id cloud --name "Cloud Node" --url http://10.0.0.1:8188
python scripts/server_manager.py disable cloud
```
*You can also manage servers fully via the Web UI.*

### Configuration Migration (Export / Import)

If you move this skill to a new path or deploy it on another machine, use the built-in bundle flow to transfer your current config and workflow mappings.

UI flow:

- Click `Export Config` on the main page to download `openclaw-skill-export.json`
- Open the UI on the target machine and click `Import Config`
- Select the exported JSON bundle
- Review the preview summary, then decide whether to also apply the source machine's default server, URL, and output directory

CLI flow:

```bash
python scripts/transfer_manager.py export --output ./openclaw-skill-export.json
python scripts/transfer_manager.py import --input ./openclaw-skill-export.json --dry-run
python scripts/transfer_manager.py import --input ./openclaw-skill-export.json
```

Optional flags:

- `--portable-only`: export without environment-specific runtime fields
- `--apply-environment`: also apply bundle default server, URL, and output directory during import
- `--no-overwrite`: skip existing workflows instead of overwriting them

Default import behavior:

- Existing workflows with the same ID are overwritten
- Existing servers are merged instead of replaced
- The target machine keeps its current `url`, `output_dir`, and `default_server` unless `--apply-environment` is used

---

## Workflow Requirements (Important)

To ensure a workflow can be executed by this project reliably:

1. **Export ComfyUI workflow in API format**
   - In ComfyUI, click **Save (API Format)**.
   - Use that exported JSON in `data/<server_id>/workflows/<workflow_id>.json`.

2. **The final output path should include a `Save Image` node**
   - The current client downloads generated results from ComfyUI output images.
   - Without a `Save Image` node (or equivalent image output in history), the tool may finish but return no downloadable image.

In short: **API-format workflow + Save Image output node** are required for stable usage.

---

## Known Caveats

- If ComfyUI returns HTTP 400 on `/prompt`, the workflow payload or parameter value is usually invalid.
- `size` must match values accepted by the underlying node (e.g. `3:4,1728x2304`).
- If `config.json` points to the wrong server URL, job queueing will fail.

---

## Roadmap (next)

- Workflow version history and rollback
- Upgrade preview before applying a new workflow version
- Parameter migration support when upgrading a workflow
- Better schema validation before queueing
- Richer error reporting from ComfyUI node errors
- Optional batch generation / multi-seed helpers

---

## Project Structure

```text
ComfyUI_Skills_OpenClaw/
├── SKILL.md                    # Agent instruction spec (how to call registry/client)
├── README.md
├── README.zh.md
├── LICENSE
├── .gitignore
├── requirements.txt            # Python deps (FastAPI, requests, etc.)
├── config.example.json         # Example runtime config
├── config.json                 # Actual local runtime config (gitignored)
├── asset/
│   └── banner-ui-20250309.jpg
├── data/
│   ├── <server_id>/
│   │   ├── workflows/
│   │   │   └── <workflow_id>.json  # ComfyUI workflow API export
│   │   └── schemas/
│   │       └── <workflow_id>.json  # Exposed parameter mapping
├── scripts/
│   ├── server_manager.py       # CLI tool for managing servers
│   ├── registry.py             # List workflows + exposed parameters for agent
│   ├── comfyui_client.py       # Inject args, queue prompt, poll history, download images
│   └── shared/                 # Shared config & JSON utils (reused across scripts)
│       ├── config.py
│       ├── json_utils.py
│       └── runtime_config.py
├── ui/
│   ├── app.py                  # FastAPI app – routes only
│   ├── open_ui.py              # Agent-friendly UI launcher
│   ├── services.py             # Business logic (workflow CRUD)
│   ├── models.py               # Pydantic request/response models
│   ├── json_store.py           # Low-level JSON file read/write helpers
│   ├── settings.py             # App-level settings
│   ├── run_ui.sh               # Start UI (macOS/Linux)
│   ├── run_ui.command          # Double-click launcher (macOS)
│   ├── run_ui.bat              # Launcher (Windows)
│   └── static/                 # Modular ES6 frontend (HTML/CSS/JS)
└── outputs/
    └── .gitkeep
```

---

<details>
<summary>Project Keywords And Resources</summary>

## Project Keywords

This repository is optimized around these search intents:

- OpenClaw
- ComfyUI
- ComfyUI Skills
- ComfyUI workflow automation
- OpenClaw ComfyUI integration
- AI image generation skill
- Xiao Long Xia (small crawfish / 小龙虾, project nickname)

Related files for project understanding and retrieval:
- `README.md` (English overview)
- `README.zh.md` (Chinese overview)
- `SKILL.md` (agent execution contract)
- `docs/llms.txt` and `docs/llms-full.txt` (LLM-oriented summaries)

---

## Project Resources

- Project summary: `docs/llms.txt`
- Extended project context: `docs/llms-full.txt`
- Project discovery checklist: `docs/PROJECT_DISCOVERY_CHECKLIST.md`

</details>
