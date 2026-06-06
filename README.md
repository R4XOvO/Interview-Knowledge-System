# Interview Knowledge System

> 你的私人面试八股教练 — 基于 Obsidian + Claude Code Skill 的个人学习管理系统。

## 功能概览

| 模块 | 触发词 | 功能 |
|------|--------|------|
| **ingest** | 注入、导入、import | 将 PDF/Word/Markdown/文本导入 Vault |
| **learn** | 学习、learn | 推荐新概念，自评后初始化 SM-2 调度 |
| **review** | 复习、review | 间隔重复复习（FAST / DEEP / INTERVIEW）|
| **dashboard** | 面板、进度 | 统计面板、薄弱分析、管理操作 |

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

> macOS 用户还需要 `brew install poppler` 以支持 PDF 导入。

### 2. 初始化 Vault

```bash
python scripts/init_vault.py
```

这会在当前目录创建 `InterviewVault/` 目录结构。

### 3. 开始使用

在 Claude Code 中：

- 输入 `导入一份面经` → 启动 **ingest** 流程
- 输入 `开始学习` → 启动 **learn** 流程
- 输入 `复习` → 启动 **review** 流程
- 输入 `看看进度` → 启动 **dashboard** 面板

## 目录结构

```
InterviewVault/
├── 00-Dashboard/
│   └── dashboard.md          # 面板主文件
├── 01-Notes/                 # 知识笔记
│   ├── High-Frequency/
│   ├── Medium-Frequency/
│   └── Low-Frequency/
├── 02-Questions/             # 面试问答
│   ├── High-Frequency/
│   ├── Medium-Frequency/
│   └── Low-Frequency/
├── 03-Exam-Traps/            # 面试陷阱
├── 04-Sessions/              # 复习会话记录
├── .progress/
│   ├── schedule.json         # SM-2 调度数据
│   ├── stats.json            # 统计缓存
│   └── ingestion_history.json # 导入历史
├── TAG-REGISTRY.md           # 标签注册表
└── config.yaml               # 用户配置
```

## 开发文档

- [DEV_SPEC.md](DEV_SPEC.md) — 完整开发规范
- [CLAUDE.md](CLAUDE.md) — Claude Code 项目上下文

## P0 开发进度

- [x] Vault 目录结构 + 文件格式规范
- [x] ingest Skill 基础版
- [x] learn Skill 基础版
- [x] review Skill 基础版 (FAST 模式)
- [x] dashboard Skill 基础版
- [x] 数据一致性验证脚本

## 技术栈

- **Obsidian** — Markdown 文件管理、双向链接、图谱视图
- **Claude Code Skills** — 用户交互层
- **Python 脚本** — 算法与数据处理（SM-2、去重、统计等）
- **YAML/JSON** — 配置与调度数据

## License

MIT
