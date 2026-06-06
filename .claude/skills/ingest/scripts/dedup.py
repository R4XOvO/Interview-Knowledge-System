#!/usr/bin/env python3
"""
去重检测工具

两层去重：
1. 文件级：计算 SHA256，查询 ingestion_history.json
2. 内容级：概念标题字符串相似度比对

用法:
    python dedup.py <file_path> <vault_path>

输出 (JSON):
    {"is_duplicate": false, "level": null, "matched_id": null, "similarity": 0.0}
    {"is_duplicate": true, "level": "file", "matched_id": "sha256", "similarity": 1.0}
    {"is_duplicate": true, "level": "content", "matched_id": "java-jvm-gc", "similarity": 0.92}

完整规格见 DEV_SPEC 8.1.2 去重机制
"""

import hashlib
import json
import sys
from difflib import SequenceMatcher
from pathlib import Path


def sha256_file(file_path: str) -> str:
    """计算文件 SHA256 哈希"""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    """计算文本 SHA256 哈希"""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def file_level_dedup(file_path: str, vault_path: str) -> dict | None:
    """
    文件级去重：比对 SHA256 与 ingestion_history.json

    Returns:
        若重复返回 {"matched_id": sha256}, 否则返回 None
    """
    history_path = Path(vault_path) / ".progress" / "ingestion_history.json"
    if not history_path.exists():
        return None

    with open(history_path, "r", encoding="utf-8") as f:
        history = json.load(f)

    file_hash = sha256_file(file_path)
    for entry in history.get("entries", []):
        if entry.get("sha256") == file_hash and entry.get("status") == "success":
            return {"matched_id": file_hash}
    return None


def content_level_dedup(concept_title: str, vault_path: str,
                        threshold: float = 0.85) -> dict | None:
    """
    内容级去重：比对概念标题与现有 Notes 的 concept 字段

    Args:
        concept_title: 要检查的概念标题
        vault_path: Vault 根目录
        threshold: 相似度阈值 (默认 0.85)

    Returns:
        若重复返回 {"matched_id": note_id, "similarity": score}, 否则返回 None
    """
    notes_dir = Path(vault_path) / "01-Notes"
    if not notes_dir.exists():
        return None

    best_match = None
    best_score = 0.0

    for note_file in notes_dir.rglob("*.md"):
        try:
            with open(note_file, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            continue

        # 简单提取 frontmatter 中的 concept 字段
        concept = None
        if content.startswith("---"):
            try:
                fm_end = content.find("---", 3)
                if fm_end != -1:
                    fm = content[3:fm_end]
                    for line in fm.splitlines():
                        if line.strip().startswith("concept:"):
                            concept = line.split(":", 1)[1].strip().strip('"\'')
                            break
            except Exception:
                pass

        if concept:
            score = SequenceMatcher(None, concept_title.lower(), concept.lower()).ratio()
            if score > best_score:
                best_score = score
                # 提取 id 作为 matched_id
                note_id = None
                for line in content[:fm_end].splitlines():
                    if line.strip().startswith("id:"):
                        note_id = line.split(":", 1)[1].strip().strip('"\'')
                        break
                best_match = {"matched_id": note_id or note_file.stem, "similarity": round(score, 3)}

    if best_match and best_match["similarity"] >= threshold:
        return best_match
    return None


def check_duplicate(file_path: str, vault_path: str,
                    concept_title: str | None = None,
                    threshold: float = 0.85) -> dict:
    """
    综合去重检测

    Returns:
        {
            "is_duplicate": bool,
            "level": "file" | "content" | None,
            "matched_id": str | None,
            "similarity": float
        }
    """
    # 先文件级
    file_dup = file_level_dedup(file_path, vault_path)
    if file_dup:
        return {
            "is_duplicate": True,
            "level": "file",
            "matched_id": file_dup["matched_id"],
            "similarity": 1.0
        }

    # 再内容级
    if concept_title:
        content_dup = content_level_dedup(concept_title, vault_path, threshold)
        if content_dup:
            return {
                "is_duplicate": True,
                "level": "content",
                "matched_id": content_dup["matched_id"],
                "similarity": content_dup["similarity"]
            }

    return {
        "is_duplicate": False,
        "level": None,
        "matched_id": None,
        "similarity": 0.0
    }


def add_ingestion_history(file_path: str, vault_path: str,
                          note_ids: list[str], status: str = "success") -> None:
    """
    将成功导入记录追加到 ingestion_history.json

    Args:
        file_path: 原始输入文件路径
        vault_path: Vault 根目录
        note_ids: 本次导入生成的笔记 ID 列表
        status: "success" | "duplicate" | "draft"
    """
    history_path = Path(vault_path) / ".progress" / "ingestion_history.json"

    history = {"version": "1.0", "entries": []}
    if history_path.exists():
        with open(history_path, "r", encoding="utf-8") as f:
            history = json.load(f)

    entry = {
        "sha256": sha256_file(file_path),
        "filename": Path(file_path).name,
        "note_ids": note_ids,
        "status": status,
        "timestamp": __import__("datetime").datetime.now().isoformat()
    }

    history["entries"].append(entry)
    history["last_updated"] = entry["timestamp"]

    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python dedup.py <file_path> <vault_path> [concept_title] [threshold]",
              file=sys.stderr)
        sys.exit(1)

    fp, vp = sys.argv[1], sys.argv[2]
    ct = sys.argv[3] if len(sys.argv) > 3 else None
    thr = float(sys.argv[4]) if len(sys.argv) > 4 else 0.85

    result = check_duplicate(fp, vp, ct, thr)
    print(json.dumps(result, ensure_ascii=False, indent=2))
