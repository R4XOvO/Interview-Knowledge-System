# Interview Knowledge System — Project Context

> This file provides context for Claude Code when working on this project.
> Full specification: [DEV_SPEC.md](DEV_SPEC.md)

## What We're Building

A personal learning management system for interview knowledge (面试八股), built as four Claude Code Skills:

| Skill | Trigger | Responsibility |
|-------|---------|----------------|
| `ingest` | 注入、导入、import | Parse multi-source materials into structured Vault |
| `learn` | 学习、learn | Present new concepts, self-assess, init SM-2 schedule |
| `review` | 复习、review | Execute spaced-repetition review with multiple modes |
| `dashboard` | 面板、进度、统计 | Show progress stats + management commands |

## Architecture

```
User input → Skill match → LLM execution → File read/write → Output
```

- **Skills communicate ONLY through the Vault file system**
- No direct cross-module calls
- All data stored as Markdown + JSON files in `InterviewVault/`

## Key Files

| File | Purpose |
|------|---------|
| [DEV_SPEC.md](DEV_SPEC.md) | Complete specification — read this first |
| `InterviewVault/config.yaml` | User configuration |
| `InterviewVault/TAG-REGISTRY.md` | Global tag registry |
| `.claude/skills/*/SKILL.md` | Skill prompt definitions |

## Development Order

1. **P0**: `ingest` + `learn` + `review` (core learning loop)
2. **P1**: `dashboard` (visualization + management)
3. **P2**: Enhanced interactivity (DEEP/INTERVIEW modes)
4. **P3**: Agent mode + MCP integration

## Coding Conventions

- Python scripts: pure functions, no side effects
- File writes: atomic (`.tmp` → rename)
- All paths relative to CWD
- Skill prompts in Chinese, code comments in English
