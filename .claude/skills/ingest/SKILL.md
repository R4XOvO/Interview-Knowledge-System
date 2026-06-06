---
name: ingest
description: >
  将外部材料导入 InterviewVault 知识库。支持 Markdown 文件和粘贴文本（P0）。
  PDF/Word 支持在 P1 实现。
  触发词：注入、导入、添加、import、加入、ingest、新面经、新笔记
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Ingest — 知识注入模块

> **完整规格**：[DEV_SPEC.md 第 8.1 节](../../../DEV_SPEC.md#81-注入模块-ingest)
> **实现优先级**：P0

## 触发条件

用户消息包含以下关键词之一：注入、导入、添加、import、加入、ingest、新面经、新笔记

## CWD 边界

NEVER access files outside CWD。所有操作在 `{CWD}/InterviewVault/` 内完成。

## 前置检查

1. 检查 `InterviewVault/` 是否存在。若不存在，运行 `python scripts/init_vault.py` 初始化。
2. 读取 `InterviewVault/config.yaml` 获取 `ingest.auto_draft` 和 `ingest.duplicate_threshold`。
3. 读取 `InterviewVault/TAG-REGISTRY.md` 获取已注册标签。

## 输入识别（P0）

根据用户输入判断类型：

| 输入特征 | 类型 | 处理方式 |
|---------|------|---------|
| 文件路径以 `.md` 结尾 | Markdown 文件 | 直接读取 frontmatter + 正文 |
| 文件路径以 `.pdf`/`.docx` 结尾 | PDF/Word | 提示 P1 支持，当前仅支持 Markdown 和粘贴文本 |
| 无文件路径，用户直接输入大段文本 | 粘贴文本 | 直接作为内容源 |

## 主流程（P0 基础版）

### 步骤 1：获取内容

**Markdown 文件输入**：
- Read 文件内容
- 若含 frontmatter，提取 id/concept/frequency/domain/tags/status
- 正文作为知识内容

**粘贴文本输入**：
- 将用户输入的文本作为内容源

### 步骤 2：AI 结构化提取

分析内容，提取以下结构化数据：

```json
{
  "notes": [
    {
      "concept": "概念名称",
      "domain": "领域（Java/OS/Network/Database）",
      "frequency": "必问|常问|冷门",
      "key_points": ["要点1", "要点2", "要点3"],
      "summary": "简要总结（100字内）",
      "tags": ["tag1", "tag2"]
    }
  ],
  "questions": [
    {
      "concept": "关联概念名称",
      "question": "问题原文",
      "answer": "参考答案（分点）",
      "scoring_points": ["踩分点1", "踩分点2"],
      "difficulty": 1,
      "type": "recall|application|analysis"
    }
  ],
  "traps": [
    {
      "concept": "关联概念",
      "trap_title": "陷阱标题",
      "what": "具体是什么坑",
      "why_confusing": "为什么容易混淆",
      "correct": "正确理解",
      "scoring_answer": "踩分回答"
    }
  ]
}
```

**提取规则**：
1. 每个概念至少提取 3 个 Q&A
2. Q&A 题型分布：≥60% recall, ≥20% application, ≥2 analysis
3. 标签使用英文 kebab-case，必须包含领域标签
4. 频率评估基于内容中强调程度

### 步骤 3：去重检测

对每个提取的概念：
1. 读取现有 `01-Notes/**/*.md` 的 frontmatter
2. 比对 `concept` 字段相似度（使用 dedup.py）
3. 若相似度 ≥ `duplicate_threshold`（默认 0.85）：
   - 标记为 duplicate，跳过写入
   - 在摘要中提示用户

### 步骤 4：生成 Vault 文件

**笔记文件**：`01-Notes/{Frequency}/{Domain}/{Concept-Slug}.md`

```markdown
---
id: "{domain}-{concept-slug}"
concept: "{概念名称}"
frequency: "{必问|常问|冷门}"
domain: "{领域}"
source: ["{来源}"]
tags: [{tag1}, {tag2}]
status: "{draft|learning}"  # auto_draft=true 时为 draft
last_studied: null
created_at: "{YYYY-MM-DD}"
---

# {概念名称}

#{tag1} #{tag2}

## Overview Table

| 项目 | 关键点 |
|------|--------|
| {要点分类} | {内容} |

> [!tip] 记忆口诀
> {AI 生成的记忆口诀}

## 核心要点

{key_points，每条用 - 列表，关键术语加 **bold**}

## 详细笔记

{summary 和扩展内容}

> [!important] 面试常考
> {该概念最高频的 1-2 个要点}

> [!warning] 易混淆点
> {与相近概念的区分}

## 面试常考模式

| 关键词/场景 | 面试官关注点 | 踩分答案 |
|------------|-------------|---------|
| ... | ... | ... |

## 相关 Q&A

- [[02-Questions/{Frequency}/{Domain}-{Concept}.md]]

## 关联概念

- [[01-Notes/...]]

## 面试陷阱

- [[03-Exam-Traps/{Domain}.md#{concept-slug}]]
```

**Q&A 文件**：`02-Questions/{Frequency}/{Domain}-{Concept}.md`

```markdown
---
id: "{domain}-{concept-slug}"
concept_id: "{domain}-{concept-slug}"
frequency: "{频率}"
domain: "{领域}"
total_questions: {N}
created_at: "{YYYY-MM-DD}"
---

# {概念名称} — 面试问答

#{domain-tag} #practice

## Related Concepts

- [[01-Notes/{Frequency}/{Domain}/{Concept}.md]]
- [[03-Exam-Traps/{Domain}.md#{concept-slug}]]

> [!hint]- 核心模式速查
> | 关键词 | 答案要点 |
> |--------|---------|
> | ... | **...** |

---

## Q01 — {标签} [recall]

**难度**：{⭐}  **频率**：{频率}

### 问题

{问题原文}

> [!answer]- 查看参考答案
> {参考答案}

---

## Q02 ...
```

**Exam Traps 追加**：`03-Exam-Traps/{Domain}.md`
- 若文件不存在，先创建带 frontmatter 的模板
- 在末尾追加该概念的陷阱条目

### 步骤 5：更新注册表

检查提取的 tags：
- 若 TAG-REGISTRY.md 中不存在，追加新行（标记 `[待审核]`）
- 格式：`\n| #{tag} | {层级} | {说明} [待审核] |`

### 步骤 6：更新导入历史

将本次导入追加到 `.progress/ingestion_history.json`：
```json
{
  "sha256": "...",
  "filename": "...",
  "note_ids": ["..."],
  "status": "success",
  "timestamp": "..."
}
```

### 步骤 7：输出摘要

```
✅ 导入完成

📄 来源：{文件名或"粘贴文本"}

📚 新增笔记：{N}
  ├── 01-Notes/High-Frequency/Java/JVM-GC.md
  └── ...

❓ 新增 Q&A：{M} 个问题
  ├── 02-Questions/High-Frequency/Java-JVM-GC.md (3 题)
  └── ...

⏭️ 跳过（已存在）：{L}

⚠️ 草稿待审核：{K} 条
  请使用「面板」→「审核草稿」查看和确认
```

## 数据读写

| 读 | 写 |
|----|-----|
| 用户输入文件 / 粘贴文本 | `01-Notes/**/*.md` |
| `TAG-REGISTRY.md` | `02-Questions/**/*.md` |
| `config.yaml` | `03-Exam-Traps/*.md` |
| `.progress/ingestion_history.json` | `TAG-REGISTRY.md` |
| `01-Notes/**/*.md`（去重比对） | `.progress/ingestion_history.json` |

## 错误处理

| 场景 | 处理方式 |
|------|---------|
| Vault 不存在 | 自动初始化 |
| 输入文件不存在 | 报错提示 |
| 全部内容重复 | 提示无需导入 |
| 标签冲突 | 追加为 `[待审核]` |
| 写入失败 | 报错，不更新历史 |

## 脚本依赖

| 脚本 | 用途 | 调用时机 |
|------|------|---------|
| `scripts/dedup.py` | 内容级去重检测 | 写入前 |
| `scripts/atomic_write.py` | 原子写入 | 所有文件写入 |
