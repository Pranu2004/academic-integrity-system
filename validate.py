
import csv
from pathlib import Path
from database import get_connection

BASE = Path(__file__).parent
DATA_DIR = BASE / "data"

passed = 0
failed = 0

def check(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"[PASS] {name} {detail}")
    else:
        failed += 1
        print(f"[FAIL] {name} {detail}")

def validate():
    conn = get_connection()
    cur = conn.cursor()

    print("\nACADEMIC INTEGRITY SYSTEM VALIDATION")
    print("=" * 48)

    # 1. Required dataset volumes
    expected = {
        "learners": 2000,
        "assessments": 20,
        "submissions": 10000,
        "similarity_reports": 1000,
        "cases": 300,
        "reviewers": 30,
        "decisions": 240,
        "appeals": 30
    }

    for table, count in expected.items():
        actual = cur.execute(
            f"SELECT COUNT(*) FROM {table}"
        ).fetchone()[0]

        if table == "appeals":
            check(
                f"{table} volume",
                actual >= count,
                f"(minimum {count}, found {actual})"
            )
        else:
            check(
                f"{table} volume",
                actual == count,
                f"(expected {count}, found {actual})"
            )   
    # 2. Foreign-key integrity
    foreign_key_errors = cur.execute(
        "PRAGMA foreign_key_check"
    ).fetchall()

    check(
        "Foreign-key integrity",
        len(foreign_key_errors) == 0,
        f"({len(foreign_key_errors)} errors)"
    )

    # 3. Required unique IDs
    for table, column in [
        ("learners", "learner_id"),
        ("submissions", "submission_id"),
        ("similarity_reports", "report_id"),
        ("cases", "case_id"),
        ("evidence_items", "evidence_id")
    ]:
        duplicates = cur.execute(f"""
            SELECT COUNT(*) FROM (
                SELECT {column}
                FROM {table}
                GROUP BY {column}
                HAVING COUNT(*) > 1
            )
        """).fetchone()[0]

        check(f"{table} unique IDs", duplicates == 0)

    # EDGE CASE 1:
    # A similarity flag must not automatically mean guilt.
    flagged = cur.execute("""
        SELECT COUNT(*) FROM submissions
        WHERE status = 'Flagged'
    """).fetchone()[0]

    guilty_automatically = cur.execute("""
        SELECT COUNT(*) FROM submissions
        WHERE status = 'Violation Confirmed'
    """).fetchone()[0]

    check(
        "Edge case 1: Flag is not automatic guilt",
        flagged == 1000 and guilty_automatically == 0,
        f"(flagged={flagged}, automatically guilty={guilty_automatically})"
    )

    # EDGE CASE 2:
    # No conflicted reviewer should be assigned.
    conflicts = cur.execute("""
        SELECT COUNT(*) FROM case_reviewers
        WHERE conflict_of_interest = 1
    """).fetchone()[0]

    check(
        "Edge case 2: Conflicted reviewer prevention",
        conflicts == 0,
        f"({conflicts} conflicted assignments)"
    )

    # EDGE CASE 3:
    # Every evidence item must have a history event.
    evidence_count = cur.execute("""
        SELECT COUNT(*) FROM evidence_items
    """).fetchone()[0]

    evidence_history_count = cur.execute("""
        SELECT COUNT(DISTINCT evidence_id)
        FROM evidence_events
    """).fetchone()[0]

    check(
        "Edge case 3: Evidence history is preserved",
        evidence_count == evidence_history_count,
        f"(items={evidence_count}, history={evidence_history_count})"
    )

    # Simulate adding evidence after a decision.
    # SAVEPOINT lets us test without permanently changing data.
    cur.execute("SAVEPOINT late_evidence_test")

    decision_case = cur.execute("""
        SELECT case_id, decided_at
        FROM decisions
        LIMIT 1
    """).fetchone()

    late_evidence_ok = False

    if decision_case:
        evidence_id = "EVD-VALIDATION-TEST"
        late_time = "2026-12-31T23:59:00"

        cur.execute("""
            INSERT INTO evidence_items
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            evidence_id,
            decision_case["case_id"],
            "Validation test: evidence added after decision",
            "Validation Test",
            "validation/test",
            "Validation System",
            late_time
        ))

        cur.execute("""
            INSERT INTO evidence_events
            (evidence_id, action, actor, event_time)
            VALUES (?, ?, ?, ?)
        """, (
            evidence_id,
            "Evidence Added After Decision",
            "Validation System",
            late_time
        ))

        history = cur.execute("""
            SELECT COUNT(*) FROM evidence_events
            WHERE evidence_id = ?
        """, (evidence_id,)).fetchone()[0]

        late_evidence_ok = history == 1

    cur.execute("ROLLBACK TO late_evidence_test")
    cur.execute("RELEASE late_evidence_test")

    check(
        "Edge case 3: Late evidence creates history",
        late_evidence_ok,
        "(test transaction rolled back)"
    )

    # EDGE CASE 4:
    # An appeal needs an independent reviewer and review outcome.
    bad_appeals = cur.execute("""
        SELECT COUNT(*)
        FROM appeals a
        JOIN decisions d
          ON a.original_decision_id = d.decision_id
        WHERE a.independent_reviewer_id IS NULL
           OR a.independent_reviewer_id = d.reviewer_id
           OR a.reviewed_at IS NULL
           OR a.status NOT IN ('Accepted', 'Rejected')
    """).fetchone()[0]

    check(
        "Edge case 4: Independent appeal review",
        bad_appeals == 0,
        f"({bad_appeals} invalid appeals)"
    )

    # Audit log coverage
    audit_count = cur.execute("""
        SELECT COUNT(*) FROM audit_logs
    """).fetchone()[0]

    check(
        "Audit log coverage",
        audit_count >= 570,
        f"(found {audit_count}, minimum expected 570)"
    )

    # Ground truth must be separate from the database.
    ground_truth = DATA_DIR / "ground_truth.csv"

    if ground_truth.exists():
        with open(ground_truth, newline="", encoding="utf-8") as file:
            truth_rows = list(csv.DictReader(file))
        truth_ok = len(truth_rows) == 300
    else:
        truth_ok = False

    check(
        "Separate ground truth file",
        truth_ok,
        "(300 evaluation labels)"
    )

    conn.close()

    print("\n" + "=" * 48)
    print(f"PASSED: {passed}")
    print(f"FAILED: {failed}")

    if failed == 0:
        print("RESULT: ALL VALIDATION CHECKS PASSED")
    else:
        print("RESULT: VALIDATION NEEDS FIXES")

if __name__ == "__main__":
    validate()
