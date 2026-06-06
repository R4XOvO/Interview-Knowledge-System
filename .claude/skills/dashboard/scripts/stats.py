#!/usr/bin/env python3
"""
统计数据重新计算

从原始数据（schedule.json + Notes/ + Questions/）重新计算所有统计指标，
输出符合 stats.json 格式的完整统计数据。

用法:
    python stats.py <vault_path>

输出:
    JSON 格式的 stats.json 内容

完整规格见 DEV_SPEC 8.4.3 统计计算
"""

import json
import sys
from datetime import datetime
from pathlib import Path


def parse_frontmatter(file_path: str) -> dict:
    """简单解析 Markdown 文件的 YAML frontmatter"""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    if not content.startswith("---"):
        return {}

    end = content.find("---", 3)
    if end == -1:
        return {}

    fm = {}
    for line in content[3:end].splitlines():
        line = line.strip()
        if ":" in line and not line.startswith("#"):
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip().strip('"\'')
            fm[key] = val
    return fm


def recalculate_stats(vault_path: str) -> dict:
    """
    从原始数据重新计算所有统计指标

    Args:
        vault_path: Vault 根目录路径

    Returns:
        符合 stats.json 格式的字典
    """
    root = Path(vault_path)
    today = datetime.now().strftime("%Y-%m-%d")

    # 1. 读取 schedule
    schedule_path = root / ".progress" / "schedule.json"
    schedule = {"items": {}}
    if schedule_path.exists():
        with open(schedule_path, "r", encoding="utf-8") as f:
            schedule = json.load(f)
    items = schedule.get("items", {})

    # 2. 读取所有 Notes
    notes_dir = root / "01-Notes"
    notes = []
    if notes_dir.exists():
        for nf in notes_dir.rglob("*.md"):
            fm = parse_frontmatter(str(nf))
            if fm:
                notes.append(fm)

    # 3. 读取所有 Questions (仅统计 frontmatter)
    questions_dir = root / "02-Questions"
    questions = []
    if questions_dir.exists():
        for qf in questions_dir.rglob("*.md"):
            fm = parse_frontmatter(str(qf))
            if fm:
                questions.append(fm)

    total_notes = len(notes)
    # total_questions 以 schedule.json 中的实际题目条目数为准
    total_questions = len(items)

    mastered_notes = sum(1 for n in notes if n.get("status") == "mastered")
    weak_notes = sum(1 for n in notes if n.get("status") == "weak")
    learning_notes = sum(1 for n in notes if n.get("status") == "learning")

    # schedule 中的状态统计
    mastered_q = sum(1 for i in items.values() if i.get("status") == "mastered")
    weak_q = sum(1 for i in items.values() if i.get("status") == "weak")
    learning_q = sum(1 for i in items.values() if i.get("status") == "learning")

    # 今日待复习
    today_due = sum(
        1 for i in items.values()
        if i.get("next_review", "9999-99-99") <= today
    )

    # 总体正确率
    total_attempts = sum(i.get("total_attempts", 0) for i in items.values())
    total_correct = sum(i.get("total_correct", 0) for i in items.values())
    overall_correct_rate = round(total_correct / total_attempts, 2) if total_attempts > 0 else 0.0

    # 按频率统计
    by_frequency = {"必问": {"total": 0, "mastered": 0},
                    "常问": {"total": 0, "mastered": 0},
                    "冷门": {"total": 0, "mastered": 0}}

    qid_to_freq = {}
    for q in questions:
        qid = q.get("id", "")
        freq = q.get("frequency", "常问")
        qid_to_freq[qid] = freq
        if freq in by_frequency:
            by_frequency[freq]["total"] += 1

    for qid, item in items.items():
        freq = qid_to_freq.get(qid, "常问")
        if freq in by_frequency and item.get("status") == "mastered":
            by_frequency[freq]["mastered"] += 1

    # 按领域统计
    domains = {}
    for n in notes:
        d = n.get("domain", "Unknown")
        if d not in domains:
            domains[d] = {"notes": 0, "questions": 0, "mastered": 0, "attempts": 0, "correct": 0}
        domains[d]["notes"] += 1

    for q in questions:
        d = q.get("domain", "Unknown")
        if d not in domains:
            domains[d] = {"notes": 0, "questions": 0, "mastered": 0, "attempts": 0, "correct": 0}
        domains[d]["questions"] += 1

    for qid, item in items.items():
        # 从 question_id 推断 note_id
        note_id = item.get("note_id", "")
        # 查找对应 note 的领域
        domain = "Unknown"
        for n in notes:
            if n.get("id") == note_id:
                domain = n.get("domain", "Unknown")
                break

        if domain in domains:
            domains[domain]["attempts"] += item.get("total_attempts", 0)
            domains[domain]["correct"] += item.get("total_correct", 0)
            if item.get("status") == "mastered":
                domains[domain]["mastered"] += 1

    by_domain = {}
    for d, v in domains.items():
        rate = round(v["correct"] / v["attempts"], 2) if v["attempts"] > 0 else 0.0
        by_domain[d] = {
            "notes": v["notes"],
            "questions": v["questions"],
            "mastered": v["mastered"],
            "correct_rate": rate,
            "status": "🟢 良好" if rate >= 0.7 else "🟡 一般" if rate >= 0.5 else "🔴 薄弱"
        }

    # 薄弱概念 Top N
    weak_concepts = []
    for n in notes:
        nid = n.get("id", "")
        note_items = [i for i in items.values() if i.get("note_id") == nid]
        if note_items:
            attempts = sum(i.get("total_attempts", 0) for i in note_items)
            correct = sum(i.get("total_correct", 0) for i in note_items)
            if attempts > 0:
                rate = correct / attempts
                if rate < 0.6:
                    weak_concepts.append({
                        "note_id": nid,
                        "concept": n.get("concept", nid),
                        "correct_rate": round(rate, 2),
                        "file_path": f"01-Notes/{n.get('frequency', '常问')}/{n.get('domain', 'Unknown')}/{n.get('concept', nid)}.md"
                    })

    weak_concepts.sort(key=lambda x: x["correct_rate"])

    return {
        "version": "1.0",
        "last_updated": datetime.now().isoformat(),
        "summary": {
            "total_notes": total_notes,
            "total_questions": total_questions,
            "mastered_notes": mastered_notes,
            "learning_notes": learning_notes,
            "weak_notes": weak_notes,
            "mastered_questions": mastered_q,
            "learning_questions": learning_q,
            "weak_questions": weak_q,
            "today_due": today_due,
            "overall_correct_rate": overall_correct_rate
        },
        "by_frequency": by_frequency,
        "by_domain": by_domain,
        "weak_concepts": weak_concepts[:10]  # 保留前10，dashboard 再按配置截取
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python stats.py <vault_path>", file=sys.stderr)
        sys.exit(1)

    vp = sys.argv[1]
    try:
        result = recalculate_stats(vp)
        # 兼容 Windows 终端编码
        import sys
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)
