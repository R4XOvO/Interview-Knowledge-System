#!/usr/bin/env python3
"""
冒烟测试 — 快速验证系统基本功能

运行方式:
    python scripts/smoke_test.py [vault_path]
"""

import importlib.util
import json
import sys
from pathlib import Path

PASS = 0
FAIL = 0
ERRORS = []


def load_module(path: Path):
    """从文件路径加载模块"""
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test(name: str, fn):
    global PASS, FAIL
    try:
        fn()
        print(f"  [PASS] {name}")
        PASS += 1
    except Exception as e:
        print(f"  [FAIL] {name}: {type(e).__name__}: {e}")
        ERRORS.append(f"{name}: {type(e).__name__}: {e}")
        FAIL += 1


def run_smoke_tests(vault_path: str = "./InterviewVault"):
    root = Path(__file__).parent.parent
    vault = Path(vault_path)

    print("=" * 60)
    print("Smoke Test — Interview Knowledge System P2")
    print("=" * 60)

    # [1] Vault Structure
    print("\n[1] Vault Structure")
    test("Vault exists", lambda: (vault.exists() or (_ for _ in ()).throw(AssertionError(f"Vault not found at {vault}"))))

    for d in ["00-Dashboard", "01-Notes", "02-Questions", "03-Exam-Traps", "04-Sessions", ".progress"]:
        test(f"Dir {d}/", lambda d=d: assert_true((vault / d).exists(), f"Missing {d}"))

    for f in ["config.yaml", "TAG-REGISTRY.md", ".progress/schedule.json", ".progress/stats.json"]:
        test(f"File {f}", lambda f=f: assert_true((vault / f).exists(), f"Missing {f}"))

    # [2] Config
    print("\n[2] Configuration")
    def check_config():
        cv = load_module(root / "scripts" / "config_validator.py")
        r = cv.validate_config(str(vault))
        assert_true(r["valid"], f"Config invalid: {r['errors']}")
        assert "version" in r["config"]
        assert r["config"]["review"]["default_mode"] in ("FAST", "DEEP", "INTERVIEW")
    test("Config valid", check_config)

    # [3] Module imports
    print("\n[3] Core Scripts")
    scripts = [
        "scripts/atomic_write.py", "scripts/init_vault.py",
        "scripts/validate_consistency.py", "scripts/config_validator.py",
        ".claude/skills/ingest/scripts/dedup.py",
        ".claude/skills/ingest/scripts/pdf_extract.py",
        ".claude/skills/ingest/scripts/format_convert.py",
        ".claude/skills/learn/scripts/recommend.py",
        ".claude/skills/review/scripts/sm2.py",
        ".claude/skills/review/scripts/scoring.py",
        ".claude/skills/review/scripts/error_note.py",
        ".claude/skills/dashboard/scripts/stats.py",
        ".claude/skills/dashboard/scripts/weak_analyzer.py",
        ".claude/skills/dashboard/scripts/retention.py",
    ]
    for sp in scripts:
        def check(sp=sp): load_module(root / sp)
        test(f"Import {Path(sp).stem}", check)

    # [4] Algorithm tests
    print("\n[4] Algorithm Tests")

    def sm2_score4():
        sm2 = load_module(root / ".claude" / "skills" / "review" / "scripts" / "sm2.py")
        e = sm2.SM2Engine()
        item = sm2.SM2Item("t", "t", None, "2026-01-01", 2.5, 1, 0, 0, 0, "learning")
        u = e.review(item, 4)
        assert u.interval > 1 and u.consecutive_correct == 1
    test("SM-2 score=4", sm2_score4)

    def sm2_score1():
        sm2 = load_module(root / ".claude" / "skills" / "review" / "scripts" / "sm2.py")
        e = sm2.SM2Engine()
        item = sm2.SM2Item("t", "t", None, "2026-01-01", 2.5, 5, 3, 5, 4, "learning")
        u = e.review(item, 1)
        assert u.status == "weak" and u.consecutive_correct == 0
    test("SM-2 score=1 -> weak", sm2_score1)

    def scoring():
        sc = load_module(root / ".claude" / "skills" / "review" / "scripts" / "scoring.py")
        r = sc.calculate_score({"accuracy": 8, "depth": 7, "code_relevance": 6, "design_thinking": 9})
        assert r["overall"] == 7.5 and r["grade"] == "B"
    test("4-dimension scoring", scoring)

    def recommend():
        rec = load_module(root / ".claude" / "skills" / "learn" / "scripts" / "recommend.py")
        r = rec.recommend(str(vault), 3)
        assert isinstance(r, list)
    test("Recommend algorithm", recommend)

    def stats():
        st = load_module(root / ".claude" / "skills" / "dashboard" / "scripts" / "stats.py")
        r = st.recalculate_stats(str(vault))
        assert "summary" in r and "retention" in r
    test("Stats recalc (P2)", stats)

    def weak():
        wa = load_module(root / ".claude" / "skills" / "dashboard" / "scripts" / "weak_analyzer.py")
        r = wa.analyze_weakness(str(vault), 5)
        assert "weak_concepts" in r and "learning_path" in r and "domain_weakness" in r
    test("Weak analyzer (P2)", weak)

    def retention():
        ret = load_module(root / ".claude" / "skills" / "dashboard" / "scripts" / "retention.py")
        r = ret.evaluate_retention(str(vault))
        assert "retention_rate" in r and "mastery_conversion" in r
    test("Retention eval (P2)", retention)

    # [5] Consistency
    print("\n[5] Data Consistency")
    def consistency():
        vc = load_module(root / "scripts" / "validate_consistency.py")
        errs = vc.validate(str(vault))
        assert len(errs) == 0, f"Errors: {errs}"
    test("schedule <-> stats consistent", consistency)

    # [6] Graph config
    print("\n[6] Obsidian Graph (P2)")
    def graph():
        gp = vault / ".obsidian" / "graph.json"
        assert gp.exists(), "graph.json not found"
        cfg = json.loads(gp.read_text(encoding="utf-8"))
        assert len(cfg.get("colorGroups", [])) >= 3
    test("Graph config exists", graph)

    # Summary
    print("\n" + "=" * 60)
    print(f"Results: {PASS} passed, {FAIL} failed")
    print("=" * 60)
    if ERRORS:
        print("\nFailed:")
        for e in ERRORS:
            print(f"  - {e}")
    return FAIL == 0


def assert_true(cond, msg=""):
    if not cond:
        raise AssertionError(msg)


if __name__ == "__main__":
    vp = sys.argv[1] if len(sys.argv) > 1 else "./InterviewVault"
    ok = run_smoke_tests(vp)
    sys.exit(0 if ok else 1)
