---
name: learn
description: >
  学习新概念，展示知识笔记，用户自评后初始化 SM-2 调度。
  触发词：学习、学新、学、learn、study、new
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Learn — 学习模块

> **完整规格**：[DEV_SPEC.md 第 8.2 节](../../../DEV_SPEC.md#82-学习模块-learn)
> **实现优先级**：P0

## 触发条件

用户消息包含以下关键词之一：学习、学新、学、learn、study、new、开始学

## CWD 边界

NEVER access files outside CWD。所有操作在 `{CWD}/InterviewVault/` 内完成。

## 前置检查

1. 检查 `InterviewVault/` 和 `01-Notes/` 是否存在。若不存在 → 提示先使用 `ingest` 导入。
2. 若 `01-Notes/` 为空 → 提示先导入内容。
3. 读取 `config.yaml` 获取配置。

## 主流程（P0 基础版）

### 步骤 1：推荐知识点

运行推荐脚本获取 Top-3：
```bash
python .claude/skills/learn/scripts/recommend.py InterviewVault 3
```

推荐优先级（由脚本计算）：
1. `status: draft` → 优先（得分最高）
2. `status: weak` → 次优
3. `status: learning` 且未学过 → 再次
4. `status: mastered` → 不推荐

### 步骤 2：展示推荐列表

向用户展示 Top-3 推荐：

```
🎯 今日推荐

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[1] {概念名称}
    📊 {频率} | {领域} > {子领域} | {状态}
    📎 相关面试题 {N} 道

[2] {概念名称}
    ...

[3] {概念名称}
    ...

请输入编号 (1-3) 选择要学习的内容，或输入 "换一批" 重新推荐。
```

### 步骤 3：展示笔记内容

用户选择后，Read 对应的笔记文件和 Q&A 文件：

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📖 {概念名称}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 {频率} | {领域} | 状态: {status}

{笔记正文 — 展示 Overview Table + 核心要点 + 详细笔记}

─────────────────────────────
📎 相关面试题（{N} 道）：
  • Q01: {问题摘要}
  • Q02: {问题摘要}
  • ...
─────────────────────────────

学习完毕后，请自评掌握程度：
[1] 完全不懂  [2] 部分理解  [3] 基本理解  [4] 很好  [5] 完美
```

### 步骤 4：处理用户自评

用户回复 1-5 的数字后：

| 自评 | 状态 | 初始间隔 | ease_factor | 加入调度 |
|------|------|---------|------------|---------|
| 1 | weak | - | - | 否 |
| 2 | learning | 1 天 | 2.5 | 是 |
| 3 | learning | 3 天 | 2.5 | 是 |
| 4 | learning | 6 天 | 2.5 | 是 |
| 5 | mastered | 10 天 | 2.5 | 是 |

### 步骤 5：更新笔记 frontmatter

Edit 笔记文件，更新：
- `status`: 根据自评结果
- `last_studied`: 当前日期 `YYYY-MM-DD`

### 步骤 6：初始化 SM-2 调度

为笔记关联的每个 Q&A 创建 schedule.json 条目：

1. Read `InterviewVault/.progress/schedule.json`
2. 找到该笔记对应的 Q&A 文件（通过 frontmatter `concept_id` 匹配）
3. 为每个问题创建条目：

```json
"{note-id}-q{NN}": {
  "question_id": "{note-id}-q{NN}",
  "note_id": "{note-id}",
  "last_reviewed": null,
  "next_review": "{YYYY-MM-DD}",
  "ease_factor": 2.5,
  "interval": {interval},
  "consecutive_correct": 0,
  "total_attempts": 0,
  "total_correct": 0,
  "status": "{weak|learning}"
}
```

4. Write 更新后的 schedule.json（使用原子写入）

### 步骤 7：更新统计

运行统计脚本重新计算：
```bash
python .claude/skills/dashboard/scripts/stats.py InterviewVault
```

将输出写入 `InterviewVault/.progress/stats.json`。

### 步骤 8：输出学习总结

```
✅ 学习完成 — {概念名称}

📊 自评：{score}/5 → 状态更新为：{status}
📅 已加入复习调度：{N} 道题目
   下次复习：{next_review 日期}

💡 提示：使用「复习」命令开始 SM-2 间隔复习。
```

## 数据读写

| 读 | 写 |
|----|-----|
| `01-Notes/**/*.md` | `01-Notes/` frontmatter 更新 |
| `02-Questions/**/*.md` | `.progress/schedule.json` |
| `.progress/schedule.json` | `.progress/stats.json` |
| `config.yaml` | |

## 错误处理

| 场景 | 处理方式 |
|------|---------|
| Vault 为空 | 提示先导入 |
| 用户选择无效 | 重新展示列表 |
| schedule.json 写入失败 | 报错，回滚 frontmatter 更新 |
| 无关联 Q&A | 仅更新笔记状态，不创建调度 |

## 脚本依赖

| 脚本 | 用途 | 调用时机 |
|------|------|---------|
| `scripts/recommend.py` | 推荐算法 | 步骤 1 |
| `scripts/atomic_write.py` | 原子写入 | 步骤 6-7 |
| `scripts/stats.py` | 统计重算 | 步骤 7 |
