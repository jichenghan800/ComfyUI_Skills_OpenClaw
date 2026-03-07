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
app.mount("/assets", StaticFiles(directory=os.path.join(STATIC_DIR, "assets")), name="assets")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

class ConfigModel(BaseModel):
    comfyui_server_url: str
    output_dir: str

class SchemaModel(BaseModel):
    workflow_id: str
    description: str
    workflow_data: dict
@app.get("/{filename}.svg")
@app.get("/{filename}.ico")
@app.get("/{filename}.png")
async def read_static_file(filename: str, request: Request):
    ext = os.path.splitext(request.url.path)[1]
    file_path = os.path.join(STATIC_DIR, f"{filename}{ext}")
    if os.path.exists(file_path):
        from fastapi.responses import FileResponse
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="File not found")

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
                workflows.append(f.replace(".json", ""))
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
        "parameters": data.schema_params
    }
    with open(schema_path, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2)
        
    return {"status": "success", "workflow_id": wf_id}

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
