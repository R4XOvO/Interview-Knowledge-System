---
name: review
description: >
  执行 SM-2 间隔复习，P0 支持 FAST 模式（快速评分）。
  DEEP/INTERVIEW 模式在 P1 实现。
  触发词：复习、review、考我、提问、quiz、test
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Review — 复习模块

> **完整规格**：[DEV_SPEC.md 第 8.3 节](../../../DEV_SPEC.md#83-复习模块-review)
> **实现优先级**：P0

## 触发条件

用户消息包含以下关键词之一：复习、review、考我、提问、quiz、test、抽题、来几题

## CWD 边界

NEVER access files outside CWD。所有操作在 `{CWD}/InterviewVault/` 内完成。

## 前置检查

1. 检查 `InterviewVault/.progress/schedule.json` 是否存在且有条目。
   - 若无条目 → 提示用户先使用 `learn` 学习内容。
2. 读取 `config.yaml` 获取：
   - `review.default_mode`（P0 忽略，固定 FAST）
   - `review.questions_per_session`（默认 10）

## 主流程（P0 — FAST 模式）

### 步骤 1：拉取待复习题目

1. Read `InterviewVault/.progress/schedule.json`
2. 筛选 `next_review <= today` 的条目
3. 排除 `status == "mastered"`（除非用户明确要求）
4. 排序规则：
   - 第一优先级：`frequency` = 必问 > 常问 > 冷门
   - 第二优先级：正确率低的优先
   - 第三优先级：过期天数多的优先
5. 取前 `questions_per_session` 道（默认 10，用户可临时指定）

若待复习不足：
- 提示剩余题目数
- 询问是否继续

### 步骤 2：逐个问答交互

对每道题，依次执行：

#### 2.1 展示问题

```
--- Q{current}/{total} ---
📚 {domain} | {frequency}

❓ {问题原文}

💭 请回答（直接输入答案）：
```

#### 2.2 收集回答

等待用户输入答案。

#### 2.3 AI 评估打分

根据用户回答与参考答案对比，给出 1-5 分：

| 分数 | 含义 | 判断标准 |
|------|------|---------|
| 5 | 完美 | 完全正确，要点齐全 |
| 4 | 正确但犹豫 | 正确但略有遗漏或表述不够精准 |
| 3 | 部分正确 | 部分要点正确，有明显遗漏 |
| 2 | 错误 | 关键概念错误 |
| 1 | 完全不记得 | 完全不会 |

**零提示原则**：评分必须基于用户实际回答，不暗示正确答案。

#### 2.4 展示评分

```
✅ 评分：{score}/5 — {评语}

💡 补充：{简要补充或纠正（1-2 句话）}

[Enter 继续下一题]
```

### 步骤 3：更新 SM-2 调度

每道题评分后，调用 sm2.py 更新：

```bash
python .claude/skills/review/scripts/sm2.py \
  InterviewVault/.progress/schedule.json \
  {question_id} \
  {score}
```

将 sm2.py 输出的 JSON 写回 `schedule.json`（原子写入）。

SM-2 更新规则（P0）：

| 评分 | interval | ease_factor | consecutive_correct | status |
|------|----------|------------|-------------------|--------|
| 5 完美 | × ease_factor | 不变 | +1 | learning |
| 4 正确 | × ease_factor | 不变 | +1 | learning |
| 3 部分 | max(1, × 0.5) | × 0.8 | 0 | learning |
| 2 错误 | max(1, × 0.3) | × 0.7 | 0 | weak |
| 1 全忘 | =1 | × 0.5 | 0 | weak |

**mastered 判定**（P0 暂不自动标记，P1 启用）：
- `consecutive_correct >= 5` 且 `ease_factor >= 2.5` → 可标记 mastered

### 步骤 4：记录错误笔记（评分 ≤2 时）

若评分 ≤2：
1. Read 对应笔记文件
2. 在文件末尾追加错误笔记：

```markdown
### 错误笔记

**{YYYY-MM-DD} — {question_id}**
- **问题**：{问题原文}
- **错误回答**：{用户回答摘要}
- **混淆点**：{AI 分析的用户误解}
- **正确理解**：{正确知识点}
- **关联概念**：[[...]]
```

3. 同时检查 `03-Exam-Traps/{Domain}.md`：
   - 若该概念无陷阱条目，追加一个
   - 若已有，在对应条目下追加错误记录

### 步骤 5：生成会话记录

全部题目完成后：

1. 计算统计：
   - 平均得分
   - 掌握题数（>= 4 分）
   - 需加强题数（< 4 分）

2. 生成会话文件：`04-Sessions/{YYYY-MM-DD}_review.md`

```markdown
---
date: "{YYYY-MM-DD}"
mode: "FAST"
total_questions: {N}
completed: {N}
---

# 复习会话 — {YYYY-MM-DD}

## 概览

- 模式：FAST
- 题目数：{N}
- 平均得分：{avg}/5
- 掌握：{X} 题（>= 4 分）
- 需加强：{Y} 题（< 4 分）

## 详细记录

### Q1: {question_id} — {概念}

- **得分**：{score}/5
- **用户回答摘要**：{摘要}
- **薄弱点**：{如有}
- **建议**：{如有}

### Q2: ...

## 更新计划

| 题目 | 下次复习 | 间隔 | ease_factor |
|------|---------|------|------------|
| {qid} | {date} | {interval} 天 | {ef} |
| ... | ... | ... | ... |

## 本次薄弱概念

1. {概念} — 平均得分 {avg} → [[01-Notes/...]]
2. ...
```

### 步骤 6：更新统计

运行统计脚本：
```bash
python .claude/skills/dashboard/scripts/stats.py InterviewVault
```

写入 `.progress/stats.json`。

### 步骤 7：输出复习总结

```
🏁 复习完成 — FAST 模式

📊 题目数：{N} | 平均得分：{avg}/5
✅ 掌握：{X} 题 | ⚠️ 需加强：{Y} 题

⏰ 下次复习：{next_due_date}，共 {next_due_count} 题待复习

💡 薄弱概念：
  1. {概念}（正确率 {rate}%）
  2. ...
```

## 数据读写

| 读 | 写 |
|----|-----|
| `.progress/schedule.json` | `.progress/schedule.json` |
| `02-Questions/**/*.md` | `.progress/stats.json` |
| `01-Notes/` frontmatter | `01-Notes/` 错误笔记追加 |
| `config.yaml` | `03-Exam-Traps/` 陷阱追加 |
| | `04-Sessions/YYYY-MM-DD_review.md` |

## 错误处理

| 场景 | 处理方式 |
|------|---------|
| 无待复习题目 | 提示"今日无复习任务，明天再来" |
| schedule.json 损坏 | 报错，建议从备份恢复 |
| 评分参数错误 | 拒绝非法评分（非 1-5） |
| 用户中途退出 | 已完成的题目仍更新，生成部分会话记录 |

## 脚本依赖

| 脚本 | 用途 | 调用时机 |
|------|------|---------|
| `scripts/sm2.py` | SM-2 算法计算 | 每题评分后 |
| `scripts/stats.py` | 统计重算 | 会话结束后 |
| `scripts/atomic_write.py` | 原子写入 | 所有文件写入 |
