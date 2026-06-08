#!/usr/bin/env python3
"""
薄弱分析算法 + 推荐学习路径

功能：
1. 识别薄弱概念（正确率 < 60%）
2. 计算概念依赖度（基于 wiki-links 和共现）
3. 生成推荐学习路径（先修 → 薄弱 → 延伸）

用法:
    python weak_analyzer.py <vault_path> [--top-n 5]

输出 (JSON):
    {
      "weak_concepts": [...],
      "learning_path": [...],
      "domain_weakness": {...}
    }

完整规格见 DEV_SPEC 6.3 Phase 3 / 8.4.3
"""

import json
import re
import sys
from pathlib import Path
from collections import defaultdict


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """解析 Markdown 文件的 YAML frontmatter"""
    if not content.startswith("---"):
        return {}, content

    end = content.find("---", 3)
    if end == -1:
        return {}, content

    fm = {}
    for line in content[3:end].splitlines():
        line = line.strip()
        if ":" in line and not line.startswith("#"):
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip().strip('"\'')
            fm[key] = val

    body = content[end + 3:]
    return fm, body


def extract_wikilinks(body: str) -> list[str]:
    """提取 [[wiki-links]]"""
    pattern = r"\[\[([^\]|]+)(?:\|[^\]]*)?\]\]"
    return re.findall(pattern, body)


def analyze_weakness(vault_path: str, top_n: int = 5) -> dict:
    """
    分析薄弱概念并生成学习路径

    Returns:
        {
          "weak_concepts": [{note_id, concept, correct_rate, domain, reasons}],
          "learning_path": [{step, concept, action, prerequisite, next_steps}],
          "domain_weakness": {domain: {avg_rate, weak_count, total_count}}
        }
    """
    root = Path(vault_path)

    # 1. 读取所有笔记
    notes_dir = root / "01-Notes"
    notes = {}
    note_bodies = {}
    if notes_dir.exists():
        for nf in notes_dir.rglob("*.md"):
            with open(nf, "r", encoding="utf-8") as f:
                content = f.read()
            fm, body = parse_frontmatter(content)
            if fm and fm.get("id"):
                notes[fm["id"]] = {**fm, "_file": str(nf.relative_to(root))}
                note_bodies[fm["id"]] = body

    # 2. 读取 schedule
    schedule_path = root / ".progress" / "schedule.json"
    schedule_items = {}
    if schedule_path.exists():
        with open(schedule_path, "r", encoding="utf-8") as f:
            schedule = json.load(f)
        schedule_items = schedule.get("items", {})

    # 3. 按概念聚合统计
    concept_stats = defaultdict(lambda: {
        "note_id": "", "concept": "", "domain": "",
        "total_attempts": 0, "total_correct": 0,
        "scores": [], "status": "learning"
    })

    for qid, item in schedule_items.items():
        nid = item.get("note_id", "")
        if nid not in notes:
            continue

        note = notes[nid]
        stats = concept_stats[nid]
        stats["note_id"] = nid
        stats["concept"] = note.get("concept", nid)
        stats["domain"] = note.get("domain", "Unknown")
        stats["total_attempts"] += item.get("total_attempts", 0)
        stats["total_correct"] += item.get("total_correct", 0)
        stats["status"] = item.get("status", "learning")

    # 4. 计算正确率，识别薄弱概念
    weak_concepts = []
    for nid, stats in concept_stats.items():
        if stats["total_attempts"] == 0:
            rate = 0.0
        else:
            rate = stats["total_correct"] / stats["total_attempts"]

        reasons = []
        if rate < 0.6:
            reasons.append("正确率低于60%")
        if stats["status"] == "weak":
            reasons.append("状态标记为薄弱")

        if reasons:
            weak_concepts.append({
                "note_id": nid,
                "concept": stats["concept"],
                "correct_rate": round(rate, 2),
                "domain": stats["domain"],
                "total_attempts": stats["total_attempts"],
                "reasons": reasons,
                "file_path": notes.get(nid, {}).get("_file", "")
            })

    weak_concepts.sort(key=lambda x: x["correct_rate"])

    # 5. 构建概念关系图（基于 wiki-links）
    concept_links = defaultdict(set)
    for nid, body in note_bodies.items():
        links = extract_wikilinks(body)
        for link in links:
            # 从链接路径提取 note_id
            # 例如 "01-Notes/High-Frequency/Java/JVM-GC.md" -> java-jvm-gc
            link_clean = link.split("#")[0].split("|")[0].strip()
            # 尝试匹配到已知 note
            for other_id, other_note in notes.items():
                if other_id != nid:
                    other_file = other_note.get("_file", "")
                    if link_clean in other_file or other_note.get("concept", "") in link_clean:
                        concept_links[nid].add(other_id)
                        break

    # 6. 生成学习路径
    learning_path = []
    for i, wc in enumerate(weak_concepts[:top_n], 1):
        nid = wc["note_id"]

        # 先修概念：链接到该薄弱概念的其他概念
        prerequisites = []
        for other_id, links in concept_links.items():
            if nid in links and other_id in notes:
                prerequisites.append({
                    "note_id": other_id,
                    "concept": notes[other_id].get("concept", other_id),
                    "file_path": notes[other_id].get("_file", "")
                })

        # 延伸概念：该薄弱概念链接到的其他概念
        next_steps = []
        for other_id in concept_links.get(nid, set()):
            if other_id in notes:
                next_steps.append({
                    "note_id": other_id,
                    "concept": notes[other_id].get("concept", other_id),
                    "file_path": notes[other_id].get("_file", "")
                })

        learning_path.append({
            "step": i,
            "concept": wc["concept"],
            "note_id": nid,
            "action": "深度复习" if wc["correct_rate"] < 0.4 else "查漏补缺",
            "correct_rate": wc["correct_rate"],
            "prerequisites": prerequisites[:3],
            "next_steps": next_steps[:3],
            "file_path": wc["file_path"]
        })

    # 7. 按领域统计薄弱度
    domain_stats = defaultdict(lambda: {"total": 0, "weak": 0, "rates": []})
    for nid, stats in concept_stats.items():
        domain = stats["domain"]
        domain_stats[domain]["total"] += 1
        if stats["total_attempts"] > 0:
            rate = stats["total_correct"] / stats["total_attempts"]
            domain_stats[domain]["rates"].append(rate)
            if rate < 0.6:
                domain_stats[domain]["weak"] += 1

    domain_weakness = {}
    for domain, ds in domain_stats.items():
        avg_rate = round(sum(ds["rates"]) / len(ds["rates"]), 2) if ds["rates"] else 0.0
        domain_weakness[domain] = {
            "total_concepts": ds["total"],
            "weak_count": ds["weak"],
            "avg_correct_rate": avg_rate,
            "status": "🔴 薄弱" if avg_rate < 0.5 else "🟡 一般" if avg_rate < 0.7 else "🟢 良好"
        }

    return {
        "version": "1.0",
        "weak_concepts": weak_concepts[:top_n],
        "learning_path": learning_path,
        "domain_weakness": domain_weakness,
        "total_analyzed": len(concept_stats)
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python weak_analyzer.py <vault_path> [--top-n 5]", file=sys.stderr)
        sys.exit(1)

    vp = sys.argv[1]
    top_n = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    try:
        result = analyze_weakness(vp, top_n)
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)
