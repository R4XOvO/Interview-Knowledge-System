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

| 你想做什么 | 说什么 | 模式 |
|-----------|--------|------|
| 导入材料 | `导入一份面经` / `导入 PDF` | **ingest** |
| 学习新概念 | `开始学习` | **learn** |
| 快速复习 | `复习` / `来几题` | **review** → FAST |
| 深度复习 | `深度复习` / `详细点评` | **review** → DEEP |
| 模拟面试 | `模拟面试` / `面试模式` | **review** → INTERVIEW |
| 查看进度 | `看看进度` / `统计` | **dashboard** |

### 复习模式对比

| 模式 | 追问 | 评分方式 | 适用场景 |
|------|------|---------|---------|
| **FAST** | 0 轮 | 1-5 分 + 简短补充 | 快速过题 |
| **DEEP** | ≤1 轮 | 1-5 分 + "你说对了/需补充/完整答案" | 查漏补缺 |
| **INTERVIEW** | ≤3 轮 | 四维度 0-10 分 + 综合评分 + 学习建议 | 实战演练 |

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
- [x] ingest Skill 基础版（Markdown + 粘贴文本）
- [x] learn Skill 基础版
- [x] review Skill 基础版（FAST 模式）
- [x] dashboard Skill 基础版（文本面板）
- [x] 数据一致性验证脚本

## P1 开发进度

- [x] review DEEP 模式（详细点评 + 单轮追问）
- [x] review INTERVIEW 模式（面试场景 + 多轮追问 + 四维度评分）
- [x] ingest PDF 支持（pdftotext 集成）
- [x] ingest Word 支持（python-docx 集成）
- [x] 错误笔记系统（自动记录到笔记 + Exam-Traps）
- [x] Dataview 面板增强（9 个动态查询区块）
- [x] mastered 自动判定（consecutive_correct ≥ 5 + ease_factor ≥ 2.5）

## P2 开发进度

- [x] 薄弱分析算法（正确率 + 概念依赖 + 学习路径）
- [x] 复习效果评估（记忆保留率 + 掌握转化率 + 领域分析）
- [x] Obsidian Graph View 配置（按状态/频率着色分组）
- [x] 配置验证系统（schema 校验 + 默认值填充）
- [x] 冒烟测试（35 项） + e2e 测试（21 项）

## 技术栈

- **Obsidian** — Markdown 文件管理、双向链接、图谱视图
- **Claude Code Skills** — 用户交互层
- **Python 脚本** — 算法与数据处理（SM-2、去重、统计等）
- **YAML/JSON** — 配置与调度数据

## License

MIT
