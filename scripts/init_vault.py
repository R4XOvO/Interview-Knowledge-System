#!/usr/bin/env python3
"""
初始化 InterviewVault 目录结构

在 CWD 下创建完整的 Vault 目录树和初始数据文件。
已存在的文件不会被覆盖。

用法（CLI）:
    python init_vault.py [vault_root_path]

默认 vault_root_path = "./InterviewVault"

完整规格见 DEV_SPEC 10.3 Vault 初始化模板
"""

import os
import json
import sys
from datetime import datetime
from pathlib import Path


# Vault 目录结构 (相对路径，不含文件)
VAULT_DIRS = [
    "00-Dashboard",
    "01-Notes/High-Frequency",
    "01-Notes/Medium-Frequency",
    "01-Notes/Low-Frequency",
    "02-Questions/High-Frequency",
    "02-Questions/Medium-Frequency",
    "02-Questions/Low-Frequency",
    "03-Exam-Traps",
    "04-Sessions",
    ".progress",
]

# 初始 schedule.json
INITIAL_SCHEDULE = {
    "version": "1.0",
    "last_updated": "",
    "items": {}
}

# 初始 ingestion_history.json
INITIAL_INGESTION_HISTORY = {
    "version": "1.0",
    "last_updated": "",
    "entries": []
}

# 初始 stats.json
INITIAL_STATS = {
    "version": "1.0",
    "last_updated": "",
    "summary": {
        "total_notes": 0,
        "total_questions": 0,
        "mastered_notes": 0,
        "learning_notes": 0,
        "weak_notes": 0,
        "mastered_questions": 0,
        "learning_questions": 0,
        "weak_questions": 0,
        "today_due": 0,
        "overall_correct_rate": 0.0
    },
    "by_frequency": {
        "必问": {"total": 0, "mastered": 0},
        "常问": {"total": 0, "mastered": 0},
        "冷门": {"total": 0, "mastered": 0}
    },
    "by_domain": {},
    "weak_concepts": []
}

# 初始 TAG-REGISTRY.md
TAG_REGISTRY_TEMPLATE = """# Tag Registry

> 全局标签规范。所有标签必须来自本注册表，kebab-case 格式。
> 注入新内容时自动检查并注册新标签。

## 层级规则

| 层级 | 前缀 | 示例 | 规则 |
|------|------|------|------|
| 领域 (Domain) | 无 | `#java`, `#os`, `#network` | 每篇笔记必须带所属领域标签 |
| 子领域 (Sub) | 无 | `#jvm`, `#garbage-collection` | 细分主题，必须同时带父领域标签 |
| 题型 (Type) | `#type-` | `#type-recall`, `#type-analysis` | Q&A 文件题型标注 |
| 笔记类型 (Note) | `#note-` | `#note-concept`, `#note-trap` | 笔记分类 |
| 状态 (Status) | `#status-` | `#status-draft`, `#status-weak` | 学习状态（可选） |

## 已注册标签

| 标签 | 层级 | 说明 |
|------|------|------|
| `#interview-trap` | 笔记类型 | 面试陷阱笔记 |
| `#practice` | 笔记类型 | 练习题 |
"""


def init_vault(vault_path: str = "./InterviewVault") -> dict:
    """
    初始化 Vault 目录结构

    Args:
        vault_path: Vault 根目录路径

    Returns:
        { "created": [...], "skipped": [...], "error": None | str }
    """
    result = {"created": [], "skipped": [], "error": None}
    root = Path(vault_path).resolve()

    # 创建 CWD 安全线（不在 root 以外的目录操作）
    cwd = Path.cwd().resolve()
    if not str(root).startswith(str(cwd)):
        result["error"] = f"Vault path {root} is outside CWD ({cwd}). Refusing."
        return result

    # 1. 创建目录
    for d in VAULT_DIRS:
        dir_path = root / d
        dir_path.mkdir(parents=True, exist_ok=True)
        result["created"].append(str(dir_path))

    # 2. 创建初始 JSON 文件
    timestamp = datetime.now().isoformat()
    init_files = {
        ".progress/schedule.json": INITIAL_SCHEDULE,
        ".progress/stats.json": INITIAL_STATS,
        ".progress/ingestion_history.json": INITIAL_INGESTION_HISTORY,
    }
    for rel_path, content in init_files.items():
        file_path = root / rel_path
        if not file_path.exists():
            content["last_updated"] = timestamp
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(content, f, ensure_ascii=False, indent=2)
            result["created"].append(str(file_path))
        else:
            result["skipped"].append(str(file_path))

    # 3. 创建 TAG-REGISTRY.md
    tag_reg_path = root / "TAG-REGISTRY.md"
    if not tag_reg_path.exists():
        with open(tag_reg_path, "w", encoding="utf-8") as f:
            f.write(TAG_REGISTRY_TEMPLATE)
        result["created"].append(str(tag_reg_path))
    else:
        result["skipped"].append(str(tag_reg_path))

    # 4. 创建 Dashboard 入口文件
    dashboard_path = root / "00-Dashboard" / "dashboard.md"
    if not dashboard_path.exists():
        dashboard_content = """---
tags: [dashboard, meta]
---

# 📊 学习面板

> 本文件由 dashboard Skill 动态更新。
> 使用 Obsidian Dataview 插件可获得更佳体验。

## 总体进度

```dataview
TABLE concept AS 概念, status AS 状态, frequency AS 频率, domain AS 领域
FROM "01-Notes"
SORT status DESC
```

## 今日待复习

```dataview
TABLE question_id AS 题目, note_id AS 笔记, next_review AS 下次复习
FROM json(".progress/schedule.json")
WHERE next_review <= date(today)
SORT next_review ASC
```

## 薄弱概念

```dataview
TABLE concept AS 概念, status AS 状态
FROM "01-Notes"
WHERE status = "weak"
SORT file.mtime DESC
```
"""
        with open(dashboard_path, "w", encoding="utf-8") as f:
            f.write(dashboard_content)
        result["created"].append(str(dashboard_path))
    else:
        result["skipped"].append(str(dashboard_path))

    return result


if __name__ == "__main__":
    vault = sys.argv[1] if len(sys.argv) > 1 else "./InterviewVault"
    r = init_vault(vault)
    if r["error"]:
        print(f"ERROR: {r['error']}", file=sys.stderr)
        sys.exit(1)
    print(f"[OK] Vault initialized at {vault}")
    print(f"   Created: {len(r['created'])} items")
    if r["skipped"]:
        print(f"   Skipped (exist): {len(r['skipped'])} items")
