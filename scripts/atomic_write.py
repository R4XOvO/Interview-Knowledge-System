#!/usr/bin/env python3
"""
原子文件写入工具

所有 Vault 文件写入都应通过此模块完成，避免写入中断导致数据损坏。
策略：先写入临时文件，再重命名替换目标文件。

用法:
    from atomic_write import atomic_write_json, atomic_write_text
    atomic_write_json("path/to/file.json", {"key": "value"})
    atomic_write_text("path/to/file.md", "# Hello")
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Any


def atomic_write_text(path: str, content: str, encoding: str = "utf-8") -> None:
    """
    原子写入文本文件

    Args:
        path: 目标文件路径
        content: 要写入的文本内容
        encoding: 文件编码
    """
    target = Path(path).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)

    fd, tmp_path = tempfile.mkstemp(dir=str(target.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding=encoding) as f:
            f.write(content)
        os.replace(tmp_path, target)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


def atomic_write_json(path: str, data: Any, indent: int = 2) -> None:
    """
    原子写入 JSON 文件

    Args:
        path: 目标文件路径
        data: 要序列化的 Python 对象
        indent: JSON 缩进
    """
    content = json.dumps(data, ensure_ascii=False, indent=indent)
    # 末尾追加换行，符合 POSIX 规范
    if not content.endswith("\n"):
        content += "\n"
    atomic_write_text(path, content)


def read_json(path: str, default: Any = None) -> Any:
    """
    安全读取 JSON 文件，文件不存在时返回默认值

    Args:
        path: 文件路径
        default: 文件不存在时的返回值

    Returns:
        解析后的 JSON 数据，或 default
    """
    target = Path(path)
    if not target.exists():
        return default
    with open(target, "r", encoding="utf-8") as f:
        return json.load(f)
