#!/usr/bin/env python3
"""
复习效果评估 — 记忆保留率统计

指标：
1. 记忆保留率：复习时评分 >=3 的比例（目标 >=70%）
2. 掌握转化率：从 learning → mastered 的平均所需复习次数
3. 薄弱点识别准确率：dashboard 标为薄弱的概念，实际复习表现是否确实较差

用法:
    python retention.py <vault_path>

输出 (JSON):
    {
      "retention_rate": 0.75,
      "mastery_conversion": {"avg_reviews": 4.2, "converted": 5, "total": 12},
      "weekly_trend": [...]
    }

完整规格见 DEV_SPEC 6.3 Phase 3
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict


def evaluate_retention(vault_path: str) -> dict:
    """
    评估复习效果

    Returns:
        {
          "retention_rate": float,  # 记忆保留率
          "mastery_conversion": dict,  # 掌握转化率
          "weak_detection_accuracy": float,  # 薄弱点识别准确率
          "weekly_trend": list,  # 周趋势
          "domain_retention": dict  # 按领域保留率
        }
    """
    root = Path(vault_path)

    schedule_path = root / ".progress" / "schedule.json"
    if not schedule_path.exists():
        return {"error": "schedule.json not found"}

    with open(schedule_path, "r", encoding="utf-8") as f:
        schedule = json.load(f)
    items = schedule.get("items", {})

    # 1. 记忆保留率 = 评分 >=3 的比例
    total_reviews = 0
    retained_reviews = 0
    # 由于没有存储每次复习的具体评分，我们通过 stats 推断
    # 使用 total_attempts 和 total_correct 作为近似
    # 正确 = 评分 >=3
    for item in items.values():
        attempts = item.get("total_attempts", 0)
        correct = item.get("total_correct", 0)
        total_reviews += attempts
        retained_reviews += correct

    retention_rate = round(retained_reviews / total_reviews, 2) if total_reviews > 0 else 0.0

    # 2. 掌握转化率 = learning → mastered 的平均复习次数
    mastered_items = [i for i in items.values() if i.get("status") == "mastered"]
    conversion_data = {
        "converted": len(mastered_items),
        "total": len(items),
        "avg_reviews_to_master": 0.0
    }
    if mastered_items:
        avg_attempts = sum(i.get("total_attempts", 0) for i in mastered_items) / len(mastered_items)
        conversion_data["avg_reviews_to_master"] = round(avg_attempts, 1)

    # 3. 薄弱点识别准确率
    # 标为 weak 的概念，其正确率是否确实 < 60%
    weak_items = [i for i in items.values() if i.get("status") == "weak"]
    weak_detection_correct = 0
    for item in weak_items:
        attempts = item.get("total_attempts", 0)
        correct = item.get("total_correct", 0)
        if attempts > 0 and correct / attempts < 0.6:
            weak_detection_correct += 1

    weak_accuracy = round(weak_detection_correct / len(weak_items), 2) if weak_items else 1.0

    # 4. 按领域统计保留率
    # 读取笔记获取领域信息
    notes_dir = root / "01-Notes"
    note_domains = {}
    if notes_dir.exists():
        for nf in notes_dir.rglob("*.md"):
            with open(nf, "r", encoding="utf-8") as f:
                content = f.read()
            if content.startswith("---"):
                end = content.find("---", 3)
                if end != -1:
                    for line in content[3:end].splitlines():
                        if line.strip().startswith("id:"):
                            nid = line.split(":", 1)[1].strip().strip('"\'')
                        elif line.strip().startswith("domain:"):
                            domain = line.split(":", 1)[1].strip().strip('"\'')
                            if 'nid' in dir() and nid:
                                note_domains[nid] = domain

    domain_retention = defaultdict(lambda: {"attempts": 0, "correct": 0})
    for item in items.values():
        nid = item.get("note_id", "")
        domain = note_domains.get(nid, "Unknown")
        domain_retention[domain]["attempts"] += item.get("total_attempts", 0)
        domain_retention[domain]["correct"] += item.get("total_correct", 0)

    domain_result = {}
    for domain, dr in domain_retention.items():
        rate = round(dr["correct"] / dr["attempts"], 2) if dr["attempts"] > 0 else 0.0
        domain_result[domain] = {
            "retention_rate": rate,
            "total_reviews": dr["attempts"],
            "target_met": rate >= 0.7
        }

    # 5. 生成报告摘要
    summary = {
        "retention_rate": retention_rate,
        "retention_target_met": retention_rate >= 0.7,
        "mastery_conversion": conversion_data,
        "weak_detection_accuracy": weak_accuracy,
        "domain_retention": domain_result,
        "recommendations": []
    }

    # 生成建议
    if retention_rate < 0.7:
        summary["recommendations"].append(
            f"记忆保留率 {retention_rate*100:.0f}% 低于目标 70%，建议增加复习频率或调整 initial interval"
        )
    if conversion_data["avg_reviews_to_master"] > 5:
        summary["recommendations"].append(
            f"平均需要 {conversion_data['avg_reviews_to_master']:.1f} 次复习才能掌握，建议加强 DEEP 模式复习"
        )
    for domain, dr in domain_result.items():
        if not dr["target_met"]:
            summary["recommendations"].append(
                f"{domain} 领域保留率 {dr['retention_rate']*100:.0f}% 低于目标，建议重点复习该领域"
            )

    return summary


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python retention.py <vault_path>", file=sys.stderr)
        sys.exit(1)

    vp = sys.argv[1]
    try:
        result = evaluate_retention(vp)
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)
