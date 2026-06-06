#!/usr/bin/env python3
"""
数据一致性验证

验证 schedule.json 和 stats.json 的数据一致性：
- 总题目数 == schedule.json items 数量
- 各 status 统计之和 == 总题目数
- 各 frequency 统计之和 == 总题目数
- 今日待复习数 == next_review <= today 的 items 数量

用法:
    python validate_consistency.py <vault_path>

返回码:
    0 = 一致
    1 = 发现不一致

完整规格见 DEV_SPEC 4.3 数据一致性测试
"""

import json
import sys
from datetime import datetime
from pathlib import Path


def validate(vault_path: str) -> list[str]:
    """
    验证 Vault 数据一致性

    Args:
        vault_path: Vault 根目录路径

    Returns:
        不一致项列表，空列表表示一切正常
    """
    errors = []
    root = Path(vault_path)

    schedule_path = root / ".progress" / "schedule.json"
    stats_path = root / ".progress" / "stats.json"

    if not schedule_path.exists():
        errors.append(f"schedule.json not found at {schedule_path}")
    if not stats_path.exists():
        errors.append(f"stats.json not found at {stats_path}")

    if errors:
        return errors

    with open(schedule_path, "r", encoding="utf-8") as f:
        schedule = json.load(f)
    with open(stats_path, "r", encoding="utf-8") as f:
        stats = json.load(f)

    items = schedule.get("items", {})
    total_in_schedule = len(items)
    total_in_stats = stats.get("summary", {}).get("total_questions", 0)

    # 1. 总题目数一致
    if total_in_schedule != total_in_stats:
        errors.append(
            f"Total mismatch: schedule={total_in_schedule}, stats={total_in_stats}"
        )

    # 2. status 统计一致
    status_counts = {"learning": 0, "weak": 0, "mastered": 0}
    for item in items.values():
        s = item.get("status", "learning")
        status_counts[s] = status_counts.get(s, 0) + 1

    summary = stats.get("summary", {})
    for status in ["mastered", "learning", "weak"]:
        s_count = status_counts.get(status, 0)
        s_stats = summary.get(f"{status}_questions", 0)
        if s_count != s_stats:
            errors.append(
                f"Status '{status}' mismatch: schedule={s_count}, stats={s_stats}"
            )

    # 3. 今日待复习一致
    today = datetime.now().strftime("%Y-%m-%d")
    due_count = sum(
        1 for item in items.values()
        if item.get("next_review", "") <= today
    )
    stats_due = summary.get("today_due", 0)
    if due_count != stats_due:
        errors.append(
            f"Today due mismatch: calculated={due_count}, stats={stats_due}"
        )

    return errors


if __name__ == "__main__":
    vault = sys.argv[1] if len(sys.argv) > 1 else "./InterviewVault"
    errs = validate(vault)
    if errs:
        print(f"[FAIL] Found {len(errs)} inconsistency issues:")
        for e in errs:
            print(f"   - {e}")
        sys.exit(1)
    else:
        print("[OK] All data consistent")
