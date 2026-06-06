---
name: dashboard
description: >
  展示学习进度面板与处理管理操作。支持统计查询、薄弱分析、草稿审核。
  触发词：面板、dashboard、进度、统计、状态
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Dashboard — 面板模块

> **完整规格**：[DEV_SPEC.md 第 8.4 节](../../../DEV_SPEC.md#84-面板模块-dashboard)
> **实现优先级**：P0

## 触发条件

用户消息包含以下关键词之一：面板、dashboard、进度、统计、状态、看看进度、学得怎么样

## CWD 边界

NEVER access files outside CWD。所有操作在 `{CWD}/InterviewVault/` 内完成。

## 前置检查

1. 检查 `.progress/stats.json` 和 `.progress/schedule.json` 是否存在。
2. 若不存在 → 提示先使用 `ingest` 和 `learn` 建立数据。
3. 读取 `config.yaml` 获取 `dashboard.show_weak_top_n` 等配置。

## 主流程（P0 — 文本面板）

### 步骤 1：读取数据

1. Read `InterviewVault/.progress/stats.json`
2. Read `InterviewVault/.progress/schedule.json`
3. 若 `stats.json` 为空或明显过时，先重新计算：
   ```bash
   python .claude/skills/dashboard/scripts/stats.py InterviewVault
   ```

### 步骤 2：渲染面板

输出 Markdown 格式的文本面板：

```
📊 学习面板（更新于 {YYYY-MM-DD}）

═══════════════════════════════════════
📈 总体进度
═══════════════════════════════════════

📚 笔记：{total_notes} | 已学：{learning_notes + weak_notes + mastered_notes} | 掌握：{mastered_notes} | 薄弱：{weak_notes} | 草稿：{draft_notes}
❓ 题目：{total_questions} | 已练：{total_attempts} | 掌握：{mastered_q} | 学习中：{learning_q} | 薄弱：{weak_q}

⏰ 今日待复习：{today_due} 题
  🔴 {qid} {概念名} (已过期 {N} 天) → [[02-Questions/...]]
  🟡 {qid} {概念名} (今日到期) → [[02-Questions/...]]
  ...

═══════════════════════════════════════
📊 按频率统计
═══════════════════════════════════════

| 频率 | 总数 | 已掌握 | 正确率 |
|------|------|--------|--------|
| 必问 | {N} | {M} | {X}% |
| 常问 | {N} | {M} | {X}% |
| 冷门 | {N} | {M} | {X}% |

═══════════════════════════════════════
📊 按领域统计
═══════════════════════════════════════

| 领域 | 笔记数 | 题目数 | 已掌握 | 正确率 | 状态 |
|------|--------|--------|--------|--------|------|
| Java | {N} | {M} | {K} | {X}% | 🟢 良好 |
| ... | ... | ... | ... | ... | ... |

═══════════════════════════════════════
🔴 薄弱概念 Top {N}
═══════════════════════════════════════

1. {概念名} (正确率 {rate}%) → [[01-Notes/...]]
2. ...

═══════════════════════════════════════
⚙️ 管理命令
═══════════════════════════════════════

可用命令：
- 标记 [题目ID] 为掌握
- 调整 [题目ID] 复习日期到 [YYYY-MM-DD]
- 审核草稿（{draft_count} 条待审核）
- 重新计算统计
- 导出复习报告
```

**颜色/状态规则**：
- 🟢 良好：正确率 >= 70%
- 🟡 一般：正确率 >= 50%
- 🔴 薄弱：正确率 < 50%

### 步骤 3：处理管理命令（如有）

若用户输入包含管理命令，执行对应操作：

#### 命令：标记 [ID] 为掌握

1. Read `schedule.json`
2. 找到对应条目，更新：
   - `status`: "mastered"
   - `interval`: 365
   - `next_review`: 一年后
3. 同时更新对应笔记 frontmatter 的 `status` 为 "mastered"
4. Write 更新后的 schedule.json
5. 重新计算 stats.json
6. 输出确认

#### 命令：调整 [ID] 日期到 [日期]

1. Read `schedule.json`
2. 找到对应条目，更新 `next_review`
3. Write 更新
4. 输出确认

#### 命令：审核草稿

1. Glob 所有 `01-Notes/**/*.md` 中 `status: draft` 的文件
2. 列出草稿列表：
   ```
   📋 草稿审核（{N} 条待审核）
   
   [1] {概念名} — {domain} | {frequency}
       → {文件路径}
   [2] ...
   
   输入编号查看详情，或输入 "全部通过" 批量改为 learning
   ```
3. 用户选择后，更新对应 frontmatter `status` 为 "learning"
4. 为其关联的 Q&A 创建 schedule.json 条目（初始间隔 1 天）

#### 命令：重新计算统计

1. 运行 stats.py 重新计算
2. 写入 stats.json
3. 输出 "统计已重新计算"

#### 命令：导出复习报告

1. Glob `04-Sessions/*.md`，取最近 7 天的会话
2. 生成汇总报告：`04-Sessions/report-{YYYY-MM-DD}.md`
3. 输出报告路径

## 数据读写

| 读 | 写 |
|----|-----|
| `.progress/stats.json` | `.progress/stats.json`（重新计算时） |
| `.progress/schedule.json` | `.progress/schedule.json`（管理操作时） |
| `01-Notes/**/*.md` | `01-Notes/` frontmatter（审核草稿时） |
| `02-Questions/**/*.md` | `04-Sessions/report-*.md`（导出时） |
| `03-Exam-Traps/*.md` | |
| `config.yaml` | |

## 错误处理

| 场景 | 处理方式 |
|------|---------|
| 无数据 | 提示先导入和学习 |
| stats.json 损坏 | 自动重新计算 |
| 管理命令 ID 不存在 | 报错提示可用 ID |
| 日期格式错误 | 提示使用 YYYY-MM-DD 格式 |

## 脚本依赖

| 脚本 | 用途 | 调用时机 |
|------|------|---------|
| `scripts/stats.py` | 统计重新计算 | 面板渲染前 / 重新计算命令 |
| `scripts/atomic_write.py` | 原子写入 | 所有写操作 |
