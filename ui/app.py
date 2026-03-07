from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import json
import os
import shutil

app = FastAPI(title="ComfyUI OpenClaw Skill Manager")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKFLOWS_DIR = os.path.join(BASE_DIR, "data", "workflows")
SCHEMAS_DIR = os.path.join(BASE_DIR, "data", "schemas")
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
STATIC_DIR = os.path.join(BASE_DIR, "ui", "static")

os.makedirs(WORKFLOWS_DIR, exist_ok=True)
os.makedirs(SCHEMAS_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

class ConfigModel(BaseModel):
    comfyui_server_url: str
    output_dir: str

class SchemaModel(BaseModel):
    workflow_id: str
    description: str
    workflow_data: dict
    schema_params: dict

class ToggleModel(BaseModel):
    enabled: bool

@app.get("/", response_class=HTMLResponse)
async def read_index():
    with open(os.path.join(STATIC_DIR, "index.html"), "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/api/config")
async def get_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"comfyui_server_url": "http://127.0.0.1:8188", "output_dir": os.path.join(BASE_DIR, "outputs")}

@app.post("/api/config")
async def save_config(config: ConfigModel):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config.dict(), f, indent=2)
    return {"status": "success"}

@app.get("/api/workflows")
async def list_workflows():
    workflows = []
    if os.path.exists(SCHEMAS_DIR):
        for f in os.listdir(SCHEMAS_DIR):
            if f.endswith(".json"):
                wf_id = f.replace(".json", "")
                try:
                    with open(os.path.join(SCHEMAS_DIR, f), "r", encoding="utf-8") as schema_file:
                        schema_data = json.load(schema_file)
                        enabled = schema_data.get("enabled", True)
                        workflows.append({"id": wf_id, "enabled": enabled})
                except Exception:
                    workflows.append({"id": wf_id, "enabled": True})
    return {"workflows": workflows}

@app.post("/api/workflow/save")
async def save_workflow(data: SchemaModel):
    wf_id = data.workflow_id
    if not wf_id:
        raise HTTPException(status_code=400, detail="Workflow ID is required")
        
    wf_path = os.path.join(WORKFLOWS_DIR, f"{wf_id}.json")
    schema_path = os.path.join(SCHEMAS_DIR, f"{wf_id}.json")
    
    # Save original workflow JSON
    with open(wf_path, "w", encoding="utf-8") as f:
        json.dump(data.workflow_data, f, indent=2)
        
    # Save schema mapping
    schema = {
        "workflow_id": wf_id,
        "description": data.description,
        "enabled": True,  # newly uploaded are enabled by default
        "parameters": data.schema_params
    }
    with open(schema_path, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2)
        
    return {"status": "success", "workflow_id": wf_id}

@app.post("/api/workflow/{wf_id}/toggle")
async def toggle_workflow(wf_id: str, data: ToggleModel):
    schema_path = os.path.join(SCHEMAS_DIR, f"{wf_id}.json")
    if not os.path.exists(schema_path):
        raise HTTPException(status_code=404, detail="Workflow schema not found")
        
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)
        
    schema["enabled"] = data.enabled
    
    with open(schema_path, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2)
        
    return {"status": "success", "enabled": data.enabled}

@app.delete("/api/workflow/{wf_id}")
async def delete_workflow(wf_id: str):
    wf_path = os.path.join(WORKFLOWS_DIR, f"{wf_id}.json")
    schema_path = os.path.join(SCHEMAS_DIR, f"{wf_id}.json")
    
    if os.path.exists(wf_path):
        os.remove(wf_path)
    if os.path.exists(schema_path):
        os.remove(schema_path)
        
    return {"status": "success"}

if __name__ == "__main__":
    import uvicorn
    # run locally
    uvicorn.run(app, host="127.0.0.1", port=8189, log_level="info")
