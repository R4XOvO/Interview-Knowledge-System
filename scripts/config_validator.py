#!/usr/bin/env python3
"""
配置验证工具

验证 InterviewVault/config.yaml 的完整性和有效性：
- 必填字段是否存在
- 值是否在有效范围内
- 路径配置是否合法
- 提供默认值填充

用法:
    python config_validator.py <vault_path>

输出:
    验证通过 → 打印有效配置 JSON
    验证失败 → 打印错误列表，返回码 1

完整规格见 DEV_SPEC 6.3 Phase 3 / 3.4
"""

import json
import sys
from pathlib import Path


# 配置schema定义
CONFIG_SCHEMA = {
    "version": {"type": str, "required": True, "default": "1.0"},
    "review": {
        "type": dict,
        "required": True,
        "children": {
            "default_mode": {"type": str, "required": True, "default": "DEEP",
                             "choices": ["FAST", "DEEP", "INTERVIEW"]},
            "questions_per_session": {"type": int, "required": True, "default": 10,
                                       "min": 1, "max": 50},
            "sm2": {
                "type": dict,
                "required": False,
                "children": {
                    "ease_factor_min": {"type": float, "required": False, "default": 1.3,
                                         "min": 1.0, "max": 2.0},
                    "ease_factor_max": {"type": float, "required": False, "default": 3.0,
                                         "min": 2.0, "max": 5.0},
                    "interval_max": {"type": int, "required": False, "default": 365,
                                    "min": 30, "max": 999}
                }
            }
        }
    },
    "ingest": {
        "type": dict,
        "required": False,
        "children": {
            "auto_draft": {"type": bool, "required": False, "default": True},
            "duplicate_threshold": {"type": float, "required": False, "default": 0.85,
                                   "min": 0.5, "max": 1.0}
        }
    },
    "dashboard": {
        "type": dict,
        "required": False,
        "children": {
            "show_weak_top_n": {"type": int, "required": False, "default": 5,
                               "min": 1, "max": 20},
            "show_due_preview": {"type": bool, "required": False, "default": True}
        }
    },
    "tracking": {
        "type": dict,
        "required": False,
        "children": {
            "granularity": {"type": str, "required": False, "default": "concept",
                           "choices": ["concept", "sub_topic"]}
        }
    },
    "paths": {
        "type": dict,
        "required": False,
        "children": {
            "vault_root": {"type": str, "required": False, "default": "./InterviewVault"},
            "notes_dir": {"type": str, "required": False, "default": "01-Notes"},
            "questions_dir": {"type": str, "required": False, "default": "02-Questions"},
            "exam_traps_dir": {"type": str, "required": False, "default": "03-Exam-Traps"},
            "sessions_dir": {"type": str, "required": False, "default": "04-Sessions"},
            "progress_dir": {"type": str, "required": False, "default": ".progress"}
        }
    }
}


def validate_value(key: str, value, schema_node: dict, errors: list) -> any:
    """验证单个值，返回填充默认值后的值"""
    expected_type = schema_node.get("type")

    # 类型检查
    if expected_type and value is not None and not isinstance(value, expected_type):
        errors.append(f"{key}: expected {expected_type.__name__}, got {type(value).__name__}")
        return schema_node.get("default")

    # 缺失必填字段
    if value is None:
        if schema_node.get("required", False):
            default = schema_node.get("default")
            if default is not None:
                errors.append(f"{key}: missing, using default {default}")
                return default
            else:
                errors.append(f"{key}: missing and no default available")
        return schema_node.get("default")

    # 范围检查
    if expected_type in (int, float):
        min_val = schema_node.get("min")
        max_val = schema_node.get("max")
        if min_val is not None and value < min_val:
            errors.append(f"{key}: {value} below minimum {min_val}")
            return max(value, min_val)
        if max_val is not None and value > max_val:
            errors.append(f"{key}: {value} above maximum {max_val}")
            return min(value, max_val)

    # 枚举检查
    choices = schema_node.get("choices")
    if choices and value not in choices:
        errors.append(f"{key}: '{value}' not in valid choices {choices}")
        return schema_node.get("default")

    return value


def validate_dict(data: dict, schema: dict, prefix: str = "") -> tuple[dict, list]:
    """
    递归验证字典配置

    Returns:
        (填充默认值后的配置, 错误列表)
    """
    errors = []
    result = {}

    for key, node in schema.items():
        full_key = f"{prefix}.{key}" if prefix else key
        value = data.get(key) if isinstance(data, dict) else None

        if node.get("type") == dict and node.get("children"):
            # 递归验证子字典
            child_data = value if isinstance(value, dict) else {}
            child_result, child_errors = validate_dict(child_data, node["children"], full_key)
            result[key] = child_result
            errors.extend(child_errors)
        else:
            validated = validate_value(full_key, value, node, errors)
            if validated is not None or node.get("required"):
                result[key] = validated

    # 检查未知字段
    if isinstance(data, dict):
        for key in data:
            if key not in schema:
                errors.append(f"{prefix}.{key}: unknown field" if prefix else f"{key}: unknown field")

    return result, errors


def parse_yaml_simple(content: str) -> dict:
    """简单 YAML 解析（仅支持本项目配置格式）

    正确处理：
    - 行内注释（key: value  # comment）
    - 引号字符串（"value"）
    - 嵌套字典
    """
    result = {}
    stack = [(result, -1)]  # (dict, indent_level)

    for line in content.splitlines():
        # 跳过空行和纯注释行
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # 去掉行内注释（但保留引号内的内容）
        line = strip_inline_comment(line)
        stripped = line.strip()
        if not stripped:
            continue

        # 计算缩进
        indent = len(line) - len(line.lstrip())

        # 解析 key: value
        if ":" in stripped:
            key, val = stripped.split(":", 1)
            key = key.strip()
            val = val.strip()

            # 根据缩进调整层级
            while len(stack) > 1 and indent <= stack[-1][1]:
                stack.pop()

            if not val:
                # 子字典开始
                new_dict = {}
                stack[-1][0][key] = new_dict
                stack.append((new_dict, indent))
            else:
                # 解析值
                parsed = parse_yaml_value(val)
                stack[-1][0][key] = parsed

    return result


def strip_inline_comment(line: str) -> str:
    """去掉行内注释，但保留引号字符串内的 #"""
    result = []
    in_quote = None
    for i, ch in enumerate(line):
        if ch in ('"', "'") and (i == 0 or line[i-1] != "\\"):
            if in_quote == ch:
                in_quote = None
            elif in_quote is None:
                in_quote = ch
        elif ch == "#" and in_quote is None:
            break
        result.append(ch)
    return "".join(result)


def parse_yaml_value(val: str) -> any:
    """解析简单的 YAML 值"""
    val = val.strip()

    # 引号字符串：去掉引号，不解析内部内容
    if (val.startswith('"') and val.endswith('"')) or \
       (val.startswith("'") and val.endswith("'")):
        return val[1:-1]

    # bool
    if val.lower() in ("true", "yes", "on"):
        return True
    if val.lower() in ("false", "no", "off"):
        return False

    # null
    if val.lower() in ("null", "none", "~"):
        return None

    # int
    try:
        return int(val)
    except ValueError:
        pass

    # float
    try:
        return float(val)
    except ValueError:
        pass

    # list (简单解析 [a, b, c])
    if val.startswith("[") and val.endswith("]"):
        inner = val[1:-1]
        return [parse_yaml_value(v) for v in inner.split(",") if v.strip()]

    return val


def validate_config(vault_path: str) -> dict:
    """
    验证 Vault 配置

    Returns:
        {"valid": bool, "config": dict, "errors": list, "warnings": list}
    """
    config_path = Path(vault_path) / "config.yaml"
    errors = []
    warnings = []

    if not config_path.exists():
        errors.append(f"config.yaml not found at {config_path}")
        # 使用完整默认值
        return {"valid": False, "config": {}, "errors": errors, "warnings": warnings}

    with open(config_path, "r", encoding="utf-8") as f:
        raw_config = parse_yaml_simple(f.read())

    validated, errs = validate_dict(raw_config, CONFIG_SCHEMA)
    errors.extend(errs)

    # 路径验证
    paths = validated.get("paths", {})
    for key, rel_path in paths.items():
        if key == "vault_root":
            continue
        full = Path(vault_path) / rel_path
        if not full.exists():
            warnings.append(f"paths.{key}: directory '{rel_path}' does not exist yet (will be created on init)")

    # 检查 sm2 参数合理性
    sm2 = validated.get("review", {}).get("sm2", {})
    if sm2.get("ease_factor_min", 1.3) >= sm2.get("ease_factor_max", 3.0):
        errors.append("review.sm2.ease_factor_min must be less than ease_factor_max")

    return {
        "valid": len([e for e in errors if not e.endswith("using default")]) == 0,
        "config": validated,
        "errors": errors,
        "warnings": warnings
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python config_validator.py <vault_path>", file=sys.stderr)
        sys.exit(1)

    vp = sys.argv[1]
    try:
        result = validate_config(vp)
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0 if result["valid"] else 1)
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)
