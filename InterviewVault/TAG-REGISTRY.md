# Tag Registry

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
