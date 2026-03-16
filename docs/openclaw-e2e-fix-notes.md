---
title: OpenClaw E2E Fix Notes
description: Record of the OpenClaw end-to-end fixes that made the ComfyUI skill execute real registry and generation commands instead of stopping at text-only replies.
permalink: /openclaw-e2e-fix-notes/
---

# OpenClaw End-to-End Fix Notes

Date: 2026-03-16

This note records the code and documentation changes made to get the full OpenClaw -> SKILL.md -> registry -> comfyui_client -> image output chain working reliably.

## Problem Summary

Two separate failures were present:

1. The documented example used `local/Default`, but the real configured workflow in the test environment was `local/文生图`, so the sample command failed immediately.
2. The saved schema exposed an auto-generated parameter like `prompt_23`, while agent examples and OpenClaw prompts used `prompt`. The old client silently ignored that mismatch, so a run could appear to succeed without actually injecting the user prompt into the workflow.

There was also an OpenClaw-specific execution problem:

- The skill instructions assumed the current working directory was the skill root and used `./scripts/...`.
- In real OpenClaw runs the working directory was the workspace root, so relative skill paths were unsafe.
- The skill metadata and top-level instructions were not strong enough to force the model to actually read the skill and execute commands instead of only replying with prompt suggestions.

## Files Changed

### Runtime behavior

- `scripts/shared/schema_aliases.py`
  - Added alias normalization for business-facing parameter names such as `prompt`, `negative_prompt`, `seed`, `width`, `height`, and `filename_prefix`.
- `scripts/registry.py`
  - Agent JSON output now exposes normalized parameter keys when a unique alias can be derived.
- `scripts/comfyui_client.py`
  - Added alias-aware argument resolution.
  - Added explicit errors for:
    - unknown parameters
    - missing required parameters
    - invalid parameter types
  - Added Python 3.9 compatibility fix with `from __future__ import annotations`.

### Skill and documentation

- `SKILL.md`
  - Rewrote the description to explicitly say this skill must execute real commands and return real image paths.
  - Added OpenClaw metadata with `python3` requirement.
  - Changed all command examples to use `{baseDir}` instead of assuming the current working directory is the skill root.
  - Added a strict "no fake execution" rule.
- `README.md`
  - Replaced `python` with `python3` in the CLI verification examples.
  - Replaced hard-coded `local/Default` usage with `<workflow_id_from_list>`.
  - Documented normalized parameter aliases.
- `README.zh.md`
  - Same fixes as the English README.
- `docs/getting-started.md`
  - Updated CLI examples to avoid hard-coded workflow IDs.

## Why These Changes Were Needed

### 1. Workflow ID mismatch

The repository documentation treated `local/Default` as if it always existed. In practice, workflow IDs come directly from the actual directory names under:

```text
data/<server_id>/<workflow_id>/
```

That means OpenClaw must first query:

```bash
python3 {baseDir}/scripts/registry.py list --agent
```

and then use the returned workflow ID exactly.

### 2. Parameter alias mismatch

Auto-extracted schema parameters from the UI could produce names like `prompt_23`, but user-facing agent calls naturally use `prompt`.

Without alias handling, the client accepted the request but did not map the user prompt to the real workflow node. The new alias layer fixes that by resolving `prompt` back to the actual saved schema key when the mapping is unambiguous.

### 3. OpenClaw session behavior

OpenClaw only keeps a compact skill list in prompt space until the model decides to read the actual skill body. The skill description therefore needed to be explicit that the model must:

1. read `SKILL.md`
2. run the registry
3. run the client
4. only claim success after a real command returns an `images` array

Using `{baseDir}` also removed path ambiguity during OpenClaw execution.

## Verification Performed

### Direct CLI verification

The following commands were verified locally:

```bash
python3 scripts/registry.py list --agent
python3 scripts/comfyui_client.py --workflow local/文生图 --args '{"prompt":"A premium product photo"}'
python3 scripts/comfyui_client.py --workflow local/文生图 --args '{}'
python3 scripts/comfyui_client.py --workflow local/文生图 --args '{"foo":"bar"}'
```

Observed outcomes:

- `registry.py list --agent` returned `prompt` instead of `prompt_23`
- valid generation returned `status: success` and a real image path
- missing required args returned a structured error
- unknown args returned a structured error

### OpenClaw end-to-end verification

A fresh OpenClaw session was used to avoid stale skill snapshots. In that run, OpenClaw:

1. read the updated `SKILL.md`
2. executed the registry command
3. executed the ComfyUI client command
4. returned the generated image path

Observed generated file:

```text
/Users/imac_beijing/.openclaw/workspace/skills/comfyui-skill-openclaw/outputs/image_20260316-161705-587_01.png
```

## Session Cache Note

OpenClaw session snapshots cache the eligible skills list and its descriptions. Existing sessions created before this fix may continue to behave like the old skill until a new session is started.

If behavior looks stale:

- start a new OpenClaw session, or
- use `/new`, or
- test with `openclaw agent --session-id <new-id> ...`

## Recommended Commit Message

```text
Fix OpenClaw ComfyUI skill E2E execution and parameter alias handling
```
