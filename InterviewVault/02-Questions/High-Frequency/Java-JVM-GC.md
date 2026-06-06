---
id: "java-jvm-gc"
concept_id: "java-jvm-gc"
frequency: "必问"
domain: "Java"
total_questions: 2
created_at: "2026-06-06"
---

# JVM 垃圾回收机制 — 面试问答

#java #practice

## Related Concepts

- [[01-Notes/High-Frequency/Java/JVM-GC.md]]

---

## Q01 — 判断对象存活 [recall]

**难度**：⭐  **频率**：必问

### 问题

如何判断对象可以被回收？

> [!answer]- 查看参考答案
> 通过可达性分析，从 GC Roots 出发...

---

## Q02 — CMS vs G1 [analysis]

**难度**：⭐⭐  **频率**：必问

### 问题

CMS 和 G1 垃圾收集器有什么区别？

> [!answer]- 查看参考答案
> CMS 使用标记-清除算法...
