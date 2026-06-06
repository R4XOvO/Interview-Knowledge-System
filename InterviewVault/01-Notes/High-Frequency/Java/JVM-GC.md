---
id: "java-jvm-gc"
concept: "JVM 垃圾回收机制"
frequency: "必问"
domain: "Java"
source: ["test"]
tags: [java, jvm, garbage-collection]
status: "draft"
last_studied: null
created_at: "2026-06-06"
---

# JVM 垃圾回收机制

#java #jvm #garbage-collection

## Overview Table

| 项目 | 关键点 |
|------|--------|
| 判断对象存活 | 可达性分析 |
| GC 算法 | 标记-清除、标记-复制、标记-整理 |
| 收集器 | CMS、G1、ZGC |

## 核心要点

- 可达性分析通过 **GC Roots** 判断对象存活
- 引用计数无法解决循环引用问题
- 分代收集理论：新生代 vs 老年代

## 详细笔记

JVM 垃圾回收...

## 面试陷阱

- [[03-Exam-Traps/Java.md#jvm-gc]]
