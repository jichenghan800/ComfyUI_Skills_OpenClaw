#!/bin/bash
cd "$(dirname "$0")"
echo "Ensuring port 8189 is free..."
lsof -ti:8189 | xargs kill -9 2>/dev/null || true

echo "Starting ComfyUI OpenClaw Skill UI..."
python3 app.py
