#!/usr/bin/env python3
"""
端到端测试 — 验证完整学习闭环

运行方式:
    python scripts/e2e_test.py [vault_path]
"""

import importlib.util
import json
import sys
from datetime import datetime
from pathlib import Path

PASS = 0
FAIL = 0


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def assert_eq(actual, expected, msg=""):
    global PASS, FAIL
    if actual == expected:
        PASS += 1
    else:
        FAIL += 1
        print(f"  [FAIL] {msg}: expected {expected}, got {actual}")


def assert_true(condition, msg=""):
    global PASS, FAIL
    if condition:
        PASS += 1
    else:
        FAIL += 1
        print(f"  [FAIL] {msg}")


def run_e2e_tests(vault_path: str = "./InterviewVault"):
    global PASS, FAIL
    root = Path(__file__).parent.parent
    vault = Path(vault_path)

    print("=" * 60)
    print("E2E Test — Full Learning Loop")
    print("=" * 60)

    # Setup: ensure Vault exists and reset test data
    print("\n[Setup] Ensure Vault exists + reset test data")
    init_vault = load_module(root / "scripts" / "init_vault.py")
    init_vault.init_vault(str(vault))
    assert_true(vault.exists(), "Vault initialized")

    # Reset schedule.json to clean baseline (only original Java items)
    baseline_schedule = {
        "version": "1.0", "last_updated": datetime.now().isoformat(),
        "items": {
            "java-jvm-gc-q01": {
                "question_id": "java-jvm-gc-q01", "note_id": "java-jvm-gc",
                "last_reviewed": None, "next_review": "2026-06-05",
                "ease_factor": 2.5, "interval": 1,
                "consecutive_correct": 0, "total_attempts": 0,
                "total_correct": 0, "status": "learning"
            },
            "java-jvm-gc-q02": {
                "question_id": "java-jvm-gc-q02", "note_id": "java-jvm-gc",
                "last_reviewed": None, "next_review": "2026-06-04",
                "ease_factor": 2.5, "interval": 1,
                "consecutive_correct": 0, "total_attempts": 0,
                "total_correct": 0, "status": "learning"
            }
        }
    }
    schedule_path = vault / ".progress" / "schedule.json"
    with open(schedule_path, "w", encoding="utf-8") as f:
        json.dump(baseline_schedule, f, ensure_ascii=False, indent=2)
    assert_true(schedule_path.exists(), "Schedule reset")

    # Step 1: Create mock note
    print("\n[Step 1] Create mock note + Q&A")
    note_dir = vault / "01-Notes" / "High-Frequency" / "OS"
    note_dir.mkdir(parents=True, exist_ok=True)
    note_path = note_dir / "Process-Thread.md"

    note_path.write_text("""---
id: "os-process-thread"
concept: "进程与线程"
frequency: "必问"
domain: "OS"
tags: [os, process, thread]
status: "draft"
last_studied: null
created_at: "2026-06-07"
---

# 进程与线程

## 核心要点

- 进程是资源分配的基本单位
- 线程是 CPU 调度的基本单位

## 面试陷阱

- [[03-Exam-Traps/OS.md#process-thread]]
""", encoding="utf-8")
    assert_true(note_path.exists(), "Note file created")

    q_dir = vault / "02-Questions" / "High-Frequency"
    q_dir.mkdir(parents=True, exist_ok=True)
    q_path = q_dir / "OS-Process-Thread.md"
    q_path.write_text("""---
id: "os-process-thread"
concept_id: "os-process-thread"
frequency: "必问"
domain: "OS"
total_questions: 1
created_at: "2026-06-07"
---

# 进程与线程 — 面试问答

## Q01 — 区别 [recall]

**难度**：⭐  **频率**：必问

### 问题

进程和线程有什么区别？

> [!answer]- 查看参考答案
> 1. 进程有独立地址空间，线程共享进程地址空间
""", encoding="utf-8")
    assert_true(q_path.exists(), "Q&A file created")

    # Step 2: Simulate learning
    print("\n[Step 2] Simulate learning (self-assessment=4)")
    sm2 = load_module(root / ".claude" / "skills" / "review" / "scripts" / "sm2.py")
    engine = sm2.SM2Engine()
    item = engine.init_schedule("os-process-thread", "os-process-thread-q01", 4)
    assert_eq(item.status, "learning", "Self-assessment 4 -> learning")
    assert_eq(item.interval, 6, "Initial interval for score 4")

    # Load current schedule for mutation
    with open(schedule_path, "r", encoding="utf-8") as f:
        schedule = json.load(f)
    schedule["items"]["os-process-thread-q01"] = {
        "question_id": "os-process-thread-q01",
        "note_id": "os-process-thread",
        "last_reviewed": None,
        "next_review": item.next_review,
        "ease_factor": item.ease_factor,
        "interval": item.interval,
        "consecutive_correct": item.consecutive_correct,
        "total_attempts": item.total_attempts,
        "total_correct": item.total_correct,
        "status": item.status
    }
    schedule["last_updated"] = datetime.now().isoformat()
    with open(schedule_path, "w", encoding="utf-8") as f:
        json.dump(schedule, f, ensure_ascii=False, indent=2)

    note_text = note_path.read_text(encoding="utf-8")
    note_text = note_text.replace('status: "draft"', 'status: "learning"')
    note_text = note_text.replace('last_studied: null', f'last_studied: "{datetime.now().strftime("%Y-%m-%d")}"')
    note_path.write_text(note_text, encoding="utf-8")
    assert_true("os-process-thread-q01" in schedule["items"], "Schedule item created")

    # Step 3: Simulate review (score=4)
    print("\n[Step 3] Simulate review (score=4)")
    old_item = sm2.SM2Item(**schedule["items"]["os-process-thread-q01"])
    old_interval = old_item.interval
    updated = engine.review(old_item, 4)
    assert_eq(updated.status, "learning", "Score 4 keeps learning")
    assert_eq(updated.consecutive_correct, 1, "Consecutive correct +1")
    assert_true(updated.interval > old_interval, f"Interval increased: {updated.interval} > {old_interval}")

    schedule["items"]["os-process-thread-q01"] = {
        "question_id": updated.question_id, "note_id": updated.note_id,
        "last_reviewed": updated.last_reviewed, "next_review": updated.next_review,
        "ease_factor": updated.ease_factor, "interval": updated.interval,
        "consecutive_correct": updated.consecutive_correct,
        "total_attempts": updated.total_attempts, "total_correct": updated.total_correct,
        "status": updated.status
    }
    with open(schedule_path, "w", encoding="utf-8") as f:
        json.dump(schedule, f, ensure_ascii=False, indent=2)

    # Step 4: Simulate review (score=2 -> weak)
    print("\n[Step 4] Simulate review (score=2 -> weak)")
    old_item2 = sm2.SM2Item(**schedule["items"]["os-process-thread-q01"])
    old_ef2 = old_item2.ease_factor
    updated2 = engine.review(old_item2, 2)
    assert_eq(updated2.status, "weak", "Score 2 -> weak")
    assert_eq(updated2.consecutive_correct, 0, "Consecutive reset")
    assert_true(updated2.ease_factor < old_ef2, f"EF decreased: {updated2.ease_factor} < {old_ef2}")

    schedule["items"]["os-process-thread-q01"] = {
        "question_id": updated2.question_id, "note_id": updated2.note_id,
        "last_reviewed": updated2.last_reviewed, "next_review": updated2.next_review,
        "ease_factor": updated2.ease_factor, "interval": updated2.interval,
        "consecutive_correct": updated2.consecutive_correct,
        "total_attempts": updated2.total_attempts, "total_correct": updated2.total_correct,
        "status": updated2.status
    }
    with open(schedule_path, "w", encoding="utf-8") as f:
        json.dump(schedule, f, ensure_ascii=False, indent=2)

    note_text = note_path.read_text(encoding="utf-8")
    note_text = note_text.replace('status: "learning"', 'status: "weak"')
    note_path.write_text(note_text, encoding="utf-8")

    # Step 5: Verify stats (recalculate first)
    print("\n[Step 5] Verify stats recalculation")
    # Recalculate stats from schedule
    stats_mod = load_module(root / ".claude" / "skills" / "dashboard" / "scripts" / "stats.py")
    stats = stats_mod.recalculate_stats(str(vault))
    with open(vault / ".progress" / "stats.json", "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    assert_true("summary" in stats, "Stats has summary")
    assert_true("retention" in stats, "P2 retention data present")

    # Step 6: Verify P2 features
    print("\n[Step 6] Verify P2 features")
    wa = load_module(root / ".claude" / "skills" / "dashboard" / "scripts" / "weak_analyzer.py")
    weak = wa.analyze_weakness(str(vault), 5)
    assert_true(len(weak["weak_concepts"]) >= 1, "Weak concepts identified")
    assert_true("learning_path" in weak, "Learning path generated")

    ret = load_module(root / ".claude" / "skills" / "dashboard" / "scripts" / "retention.py")
    retention = ret.evaluate_retention(str(vault))
    assert_true("retention_rate" in retention, "Retention rate calculated")

    cv = load_module(root / "scripts" / "config_validator.py")
    cfg = cv.validate_config(str(vault))
    assert_true(cfg["valid"], "Config is valid")

    vc = load_module(root / "scripts" / "validate_consistency.py")
    errs = vc.validate(str(vault))
    assert_eq(len(errs), 0, f"Data consistency errors: {errs}")

    # Step 7: Error note system
    print("\n[Step 7] Error note system (score=2)")
    en = load_module(root / ".claude" / "skills" / "review" / "scripts" / "error_note.py")
    err_result = en.record_error(
        str(vault), "os-process-thread-q01", 2,
        user_answer="进程和线程没有区别",
        misconception="认为进程和线程完全一样",
        correct="进程有独立地址空间，线程共享进程资源",
        question_text="进程和线程有什么区别？"
    )
    assert_true(err_result["success"], "Error note recorded")

    # Summary
    print("\n" + "=" * 60)
    print(f"Results: {PASS} passed, {FAIL} failed")
    print("=" * 60)
    return FAIL == 0


if __name__ == "__main__":
    vp = sys.argv[1] if len(sys.argv) > 1 else "./InterviewVault"
    ok = run_e2e_tests(vp)
    sys.exit(0 if ok else 1)
