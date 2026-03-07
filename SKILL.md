---
name: comfyui-agent
description: |
  利用 ComfyUI 强大的节点工作流能力生成图像。支持动态加载多套配置好的生图工作流以及对应的参数映射，将自然语言转化为参数，驱动本地或远程的 ComfyUI 服务执行，最终将图片返回给目标客户端。
  
  **当以下情况时使用此 Skill**：
  (1) 用户需要“生成图片”、“画一张图”、“执行 ComfyUI 工作流”
  (2) 用户对图像生成有特定的画风、人物、场景需求
---

# ComfyUI Agent SKILL

## 🚨 核心执行规范

作为搭载了 ComfyUI 技能的 OpenClaw Agent，你的目标是将用户口语化的需求转化为严格的结构化参数，并交由底层 Python 脚本执行工作流。

### 第一步：查询当前可用工作流 (Registry)

在尝试生成任何图片之前，你必须**首先查询登记表**，了解当前支持哪些工作流，以及它们分别需要哪些参数：
```bash
python /Users/huangyuchuh/AI_Project/ComfyUI_Skills_OpenClaw/scripts/registry.py list
```

**返回格式解析**：
你会得到一个包含所有工作流 `workflow_id` 及对应 `parameters` 的 JSON：
- `required: true` 的参数，如果用户没提供，你必须 **反问用户补充**。
- `required: false` 的参数，你可以根据用户的描述自行推理生成（例如翻译用户的场景并优化），或直接使用空值/随机数（如 `seed` = 随机数）。
- 绝不要向用户暴露底层节点信息（不要提 Node ID），只询问业务参数名（如 prompt、风格等）。

### 第二步：参数装配与交互

一旦你确定了要使用的 `workflow_id`，并且收集/生成了所有必要的参数，你需要将其组装为一个紧凑的 JSON 字符串。
例如，如果 schema 中暴露了 `prompt` 和 `seed`，你需要构造：
`{"prompt": "A beautiful landscape, high quality, masterpiece", "seed": 40128491}`

*如果关键参数缺失，请使用 `notify_user` 礼貌地询问用户。比如：“为了生成您需要的图，请问您想画特定的人物还是动物？有没有期望的画面风格？”*

### 第三步：触发图片生成任务

收集到完整参数后，请在一个命令行环境（使用对应的工具，确保工作路径在项目中，或者使用绝对路径调用）中执行工作流客户端。
> **注意**：大括号外必须使用单引号，防止 bash 解析 JSON 双引号出错。

```bash
python /Users/huangyuchuh/AI_Project/ComfyUI_Skills_OpenClaw/scripts/comfyui_client.py --workflow <workflow_id> --args '{"key1": "value1", "key2": 123}'
```

**阻塞与结果获取**：
- 这个脚本会自动发送任务并**轮询等待** ComfyUI 完成渲染，随后下载图片。
- 如果执行成功，脚本最终的标准输出会提供一个 JSON，包含 `images` 列表，里面的绝对路径即为生成的图片文件。

### 第四步：将图片发送给用户

得到生成的图片本地绝对路径后，请使用你原生的能力将文件展示给用户（如果是 OpenClaw 环境下，返回路径即可被客户端拦截转换为富文本或图片预览）。

## 🔧 常见排错与须知
1. **ComfyUI 离线**：如果脚本返回 "Error connecting to ComfyUI"，请提醒用户检查 ComfyUI 服务是否开启，或者去 Web UI 面板 (`python3 ui/app.py` 开启) 配置正确的 `comfyui_server_url`。
2. **Schema 未找到**：如果你直接调用了某个用户口头上说的工作流，但脚本报错缺 Schema，请执行第一步 `registry.py`，告诉用户需要先去 Web UI 面板“上传并配置映射该工作流”。
3. **参数格式错误**：确保通过 `--args` 传入的 JSON 是被单引号包裹住的合法 JSON 字符串。
