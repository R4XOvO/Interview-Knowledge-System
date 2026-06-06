#!/usr/bin/env python3
"""
学习推荐算法

计算每个待学习笔记的推荐得分：
    推荐得分 = 基础优先级 × 频率权重 × 时间衰减

输出 Top-N 推荐结果。

完整规格见 DEV_SPEC 8.2.1 推荐算法
"""

import json
import sys
from datetime import datetime, timedelta
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


def calculate_score(note_fm: dict, today: datetime | None = None) -> float:
    """
    计算单篇笔记的推荐得分

    Args:
        note_fm: 笔记 frontmatter 字典
        today: 当前日期，None 则使用系统日期

    Returns:
        推荐得分 (float)
    """
    if today is None:
        today = datetime.now()

    status = note_fm.get("status", "draft")
    frequency = note_fm.get("frequency", "常问")
    last_studied = note_fm.get("last_studied")

    # 基础优先级
    base_priority = {
        "draft": 100,
        "weak": 80,
        "learning": 60,
        "mastered": 0
    }.get(status, 50)

    if base_priority == 0:
        return 0.0

    # 频率权重
    freq_weight = {
        "必问": 1.5,
        "常问": 1.2,
        "冷门": 1.0
    }.get(frequency, 1.0)

    # 时间衰减
    if last_studied and last_studied != "null" and last_studied != "None":
        try:
            last_date = datetime.strptime(last_studied, "%Y-%m-%d")
            days_since = (today - last_date).days
        except ValueError:
            days_since = 0
    else:
        days_since = 0

    time_decay = 1 + days_since / 30.0

    return base_priority * freq_weight * time_decay


def recommend(vault_path: str, top_n: int = 3) -> list[dict]:
    """
    推荐 Top-N 学习笔记

    Args:
        vault_path: Vault 根目录路径
        top_n: 返回数量

    Returns:
        推荐列表，每项包含 file_path, frontmatter, score
    """
    notes_dir = Path(vault_path) / "01-Notes"
    if not notes_dir.exists():
        return []

    today = datetime.now()
    candidates = []

    for note_file in notes_dir.rglob("*.md"):
        fm = parse_frontmatter(str(note_file))
        if not fm:
            continue
        score = calculate_score(fm, today)
        if score > 0:
            candidates.append({
                "file_path": str(note_file.relative_to(vault_path)),
                "frontmatter": fm,
                "score": round(score, 2)
            })

    candidates.sort(key=lambda x: x["score"], reverse=True)
    return candidates[:top_n]


def recommend_json(vault_path: str, top_n: int = 3) -> str:
    """返回 JSON 格式的推荐结果"""
    result = recommend(vault_path, top_n)
    return json.dumps(result, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python recommend.py <vault_path> [top_n]", file=sys.stderr)
        sys.exit(1)

    vp = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    print(recommend_json(vp, n))
