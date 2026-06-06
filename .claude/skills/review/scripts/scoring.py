#!/usr/bin/env python3
"""
INTERVIEW 模式多维度评分计算

评分维度：
- 准确性 (Accuracy)：事实正确性 (0-10)
- 深度 (Depth)：是否触及原理层面 (0-10)
- 代码关联 (Code Relevance)：是否结合代码/实现细节 (0-10)
- 设计思维 (Design Thinking)：是否有对比/权衡/扩展思考 (0-10)

综合评分 = 四维度平均，保留一位小数

完整规格见 DEV_SPEC 8.3.4 评分规则
"""

import json
import sys


def calculate_score(dimensions: dict[str, int]) -> dict:
    """
    计算多维度评分

    Args:
        dimensions: {"accuracy": int, "depth": int, "code_relevance": int, "design_thinking": int}
            每个维度为 0-10 的整数

    Returns:
        {
            "accuracy": int,
            "depth": int,
            "code_relevance": int,
            "design_thinking": int,
            "overall": float,
            "grade": str   # A+/A/B/C/D
        }
    """
    keys = ["accuracy", "depth", "code_relevance", "design_thinking"]
    values = []
    for k in keys:
        v = dimensions.get(k, 0)
        v = max(0, min(10, v))
        values.append(v)

    overall = round(sum(values) / len(values), 1)

    # 等级划分
    if overall >= 9:
        grade = "A+"
    elif overall >= 8:
        grade = "A"
    elif overall >= 7:
        grade = "B"
    elif overall >= 5:
        grade = "C"
    else:
        grade = "D"

    return {
        "accuracy": values[0],
        "depth": values[1],
        "code_relevance": values[2],
        "design_thinking": values[3],
        "overall": overall,
        "grade": grade
    }


def convert_sm2_to_interview(sm2_score: int) -> dict:
    """
    将 SM-2 的 1-5 分映射为 INTERVIEW 模式的四维度评分

    用于 FAST 模式切换到 INTERVIEW 模式时的兼容处理
    """
    mapping = {
        5: {"accuracy": 10, "depth": 9, "code_relevance": 8, "design_thinking": 9},
        4: {"accuracy": 9, "depth": 7, "code_relevance": 6, "design_thinking": 7},
        3: {"accuracy": 6, "depth": 5, "code_relevance": 4, "design_thinking": 5},
        2: {"accuracy": 3, "depth": 2, "code_relevance": 1, "design_thinking": 2},
        1: {"accuracy": 1, "depth": 0, "code_relevance": 0, "design_thinking": 0},
    }
    dims = mapping.get(sm2_score, mapping[3])
    return calculate_score(dims)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scoring.py '{\"accuracy\":8,\"depth\":7,...}'", file=sys.stderr)
        sys.exit(1)

    try:
        dims = json.loads(sys.argv[1])
        result = calculate_score(dims)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)
