#!/usr/bin/env python3
"""
SM-2 间隔重复算法实现

完整规格见 DEV_SPEC 第 5.2 节 SM-2 算法规格
以及 .claude/skills/review/SKILL.md 中的 SM-2 更新规则表

用法（CLI）:
    python sm2.py <schedule.json> <question_id> <score>

用法（库）:
    from sm2 import SM2Engine, SM2Item
    engine = SM2Engine()
    updated = engine.review(item, score=4)
"""

from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Optional
import json
import sys


@dataclass
class SM2Item:
    """SM-2 调度条目，对应 schedule.json 中的 items 条目"""
    question_id: str
    note_id: str
    last_reviewed: Optional[str]  # YYYY-MM-DD
    next_review: str              # YYYY-MM-DD
    ease_factor: float
    interval: int                 # 天数
    consecutive_correct: int
    total_attempts: int
    total_correct: int
    status: str                   # "learning" | "weak" | "mastered"


class SM2Engine:
    """
    SM-2 算法引擎

    Properties:
        EASE_FACTOR_MIN: float = 1.3
        EASE_FACTOR_MAX: float = 3.0
        INTERVAL_MAX: int = 365
    """

    EASE_FACTOR_MIN = 1.3
    EASE_FACTOR_MAX = 3.0
    INTERVAL_MAX = 365

    def __init__(self, ease_factor_min: float = 1.3,
                 ease_factor_max: float = 3.0, interval_max: int = 365):
        self.EASE_FACTOR_MIN = ease_factor_min
        self.EASE_FACTOR_MAX = ease_factor_max
        self.INTERVAL_MAX = interval_max

    def review(self, item: SM2Item, score: int) -> SM2Item:
        """
        执行一次复习评分，返回更新后的条目

        Args:
            item: 当前调度条目
            score: 用户评分 (1-5)
                5 = 完美回忆
                4 = 正确但犹豫
                3 = 部分忘记
                2 = 错误
                1 = 完全不记得

        Returns:
            更新后的 SM2Item（直接修改原对象并返回）
        """
        if score < 1 or score > 5:
            raise ValueError(f"Score must be 1-5, got {score}")

        item.total_attempts += 1
        if score >= 3:
            item.total_correct += 1
            item.consecutive_correct += 1
        else:
            item.consecutive_correct = 0

        # 更新 ease_factor
        if score < 3:
            adjustments = {1: -0.5, 2: -0.3, 3: -0.2}
            item.ease_factor += adjustments[score]

        item.ease_factor = max(self.EASE_FACTOR_MIN,
                               min(self.EASE_FACTOR_MAX, item.ease_factor))

        # 更新 interval
        if score >= 3:
            if item.interval == 0:
                item.interval = {3: 1, 4: 6, 5: 10}[score]
            else:
                item.interval = int(item.interval * item.ease_factor)
        else:
            multipliers = {1: 0, 2: 0.3, 3: 0.5}
            item.interval = max(1, int(item.interval * multipliers[score]))

        item.interval = min(self.INTERVAL_MAX, item.interval)

        # 更新日期
        today = datetime.now().strftime("%Y-%m-%d")
        item.last_reviewed = today
        next_date = datetime.now() + timedelta(days=item.interval)
        item.next_review = next_date.strftime("%Y-%m-%d")

        # 更新状态
        if item.consecutive_correct >= 5 and item.ease_factor >= 2.5:
            item.status = "mastered"
        elif score <= 2:
            item.status = "weak"
        else:
            item.status = "learning"

        return item

    def init_schedule(self, note_id: str, question_id: str,
                      self_assessment: int) -> SM2Item:
        """
        根据首次学习自评初始化调度

        Args:
            note_id: 笔记 ID
            question_id: 问题 ID
            self_assessment: 自评 (1-5)

        Returns:
            初始化的 SM2Item
        """
        intervals = {1: 0, 2: 1, 3: 3, 4: 6, 5: 10}
        interval = intervals.get(self_assessment, 1)

        today = datetime.now()
        next_review = today + timedelta(days=interval) if interval > 0 else today

        return SM2Item(
            question_id=question_id,
            note_id=note_id,
            last_reviewed=None,
            next_review=next_review.strftime("%Y-%m-%d"),
            ease_factor=2.5,
            interval=interval,
            consecutive_correct=0,
            total_attempts=0,
            total_correct=0,
            status="weak" if self_assessment <= 1 else "learning"
        )

    def to_dict(self, item: SM2Item) -> dict:
        """将 SM2Item 转为 schedule.json 兼容的字典"""
        return asdict(item)

    @classmethod
    def from_dict(cls, data: dict) -> SM2Item:
        """从 schedule.json 条目字典创建 SM2Item"""
        return SM2Item(**{k: data.get(k) for k in [
            "question_id", "note_id", "last_reviewed", "next_review",
            "ease_factor", "interval", "consecutive_correct",
            "total_attempts", "total_correct", "status"
        ]})


if __name__ == "__main__":
    # CLI 模式：python sm2.py <schedule.json> <question_id> <score>
    if len(sys.argv) != 4:
        print("Usage: python sm2.py <schedule.json> <question_id> <score>")
        sys.exit(1)

    schedule_path, qid, score = sys.argv[1], sys.argv[2], int(sys.argv[3])

    with open(schedule_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if qid not in data.get("items", {}):
        print(f"[ERROR] Question ID '{qid}' not found in schedule", file=sys.stderr)
        print(f"        Available IDs: {list(data.get('items', {}).keys())}", file=sys.stderr)
        sys.exit(1)

    engine = SM2Engine()
    item = SM2Engine.from_dict(data["items"][qid])
    updated = engine.review(item, score)
    data["items"][qid] = engine.to_dict(updated)
    data["last_updated"] = datetime.now().isoformat()

    print(json.dumps(data, ensure_ascii=False, indent=2))
