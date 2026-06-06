---
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
