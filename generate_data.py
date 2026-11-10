
import csv
import random
from pathlib import Path
from datetime import datetime, timedelta

from database import init_db, get_connection

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

SEED = 20261022
random.seed(SEED)

BASE = Path(__file__).parent
DATA_DIR = BASE / "data"
DATA_DIR.mkdir(exist_ok=True)


# --------------------------------------------------
# DATE GENERATION
# --------------------------------------------------

def make_date(days_back=300):
    """Generate a reproducible datetime in 2026."""
    return datetime(2026, 1, 1) + timedelta(
        days=random.randint(0, days_back),
        hours=random.randint(8, 18),
        minutes=random.randint(0, 59)
    )


def date_text(value):
    """Convert datetime into SQLite-compatible text."""
    return value.isoformat(timespec="seconds")


# --------------------------------------------------
# MAIN DATA GENERATOR
# --------------------------------------------------

def generate():

    init_db()

    conn = get_connection()
    cur = conn.cursor()

    # Start clean so every run produces the same dataset.
    cur.execute("PRAGMA foreign_keys = ON")

    tables_to_clear = [
        "evidence_events",
        "case_events",
        "audit_logs",
        "appeals",
        "decisions",
        "evidence_items",
        "case_reviewers",
        "cases",
        "similarity_reports",
        "submissions",
        "integrity_rules",
        "reviewers",
        "assessments",
        "learners"
    ]

    for table in tables_to_clear:
        cur.execute(f"DELETE FROM {table}")

    # Store submission and report timestamps for chronological records.
    submission_dates = {}
    report_dates = {}

    # --------------------------------------------------
    # 1. LEARNERS
    # --------------------------------------------------

    for i in range(1, 2001):

        cur.execute("""
            INSERT INTO learners
            VALUES (?, ?, ?, ?, ?)
        """, (
            f"LRN-{i:05d}",
            f"Learner {i}",
            f"learner{i}@example.edu",
            random.choice(["CSE", "AIML", "ECE", "IT"]),
            date_text(make_date())
        ))

    # --------------------------------------------------
    # 2. ASSESSMENTS
    # --------------------------------------------------

    for i in range(1, 21):

        cur.execute("""
            INSERT INTO assessments
            VALUES (?, ?, ?, ?, ?)
        """, (
            f"ASM-{i:03d}",
            f"Assessment {i}",
            random.choice([
                "Python",
                "Database Systems",
                "AI",
                "Networks"
            ]),
            "2026-12-15T23:59:00",
            f"Instructor {(i % 10) + 1}"
        ))

    # --------------------------------------------------
    # 3. INTEGRITY RULES
    # --------------------------------------------------

    rules = [
        ("RULE-001", "Standard Similarity Review", 30, 60),
        ("RULE-002", "Programming Similarity Review", 35, 70),
        ("RULE-003", "Written Assignment Review", 25, 55)
    ]

    for rule_id, name, threshold, high in rules:

        cur.execute("""
            INSERT INTO integrity_rules
            (rule_id, rule_name, review_threshold,
             high_priority_threshold, effective_from, active)
            VALUES (?, ?, ?, ?, ?, 1)
        """, (
            rule_id,
            name,
            threshold,
            high,
            "2026-01-01"
        ))

    # --------------------------------------------------
    # 4. REVIEWERS
    # --------------------------------------------------

    for i in range(1, 31):

        cur.execute("""
            INSERT INTO reviewers
            VALUES (?, ?, ?, ?, 1)
        """, (
            f"REV-{i:03d}",
            f"Reviewer {i}",
            random.choice([
                "Instructor",
                "Administrator",
                "Support"
            ]),
            random.choice(["CSE", "AIML", "ECE", "IT"])
        ))

    # --------------------------------------------------
    # 5. SUBMISSIONS
    # --------------------------------------------------

    for i in range(1, 10001):

        learner = random.randint(1, 2000)
        assessment = random.randint(1, 20)

        submitted = make_date()
        submission_id = f"SUB-{i:05d}"

        submission_dates[submission_id] = submitted

        cur.execute("""
            INSERT INTO submissions
            (submission_id, learner_id, assessment_id,
             submitted_at, content, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            submission_id,
            f"LRN-{learner:05d}",
            f"ASM-{assessment:03d}",
            date_text(submitted),
            f"Synthetic academic submission content number {i}. "
            f"This is generated sample text for assessment {assessment}.",
            "Flagged" if i <= 1000 else "Submitted"
        ))

    # --------------------------------------------------
    # 6. SIMILARITY REPORTS
    # --------------------------------------------------

    for i in range(1, 1001):

        rule = rules[(i - 1) % len(rules)]

        score = round(random.uniform(25, 98), 2)

        status = (
            "High Priority"
            if score >= rule[3]
            else "Review Required"
        )

        submission_id = f"SUB-{i:05d}"

        # Report must be generated after submission.
        report_date = (
            submission_dates[submission_id]
            + timedelta(hours=1)
        )

        report_id = f"SIM-{i:04d}"

        report_dates[report_id] = report_date

        cur.execute("""
            INSERT INTO similarity_reports
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            report_id,
            submission_id,
            rule[0],
            score,
            f"Reference-{random.randint(1, 500)}",
            date_text(report_date),
            status
        ))

    # --------------------------------------------------
    # 7. CASES, REVIEWERS, EVIDENCE, DECISIONS, APPEALS
    # --------------------------------------------------

    for i in range(1, 301):

        case_id = f"CASE-{i:04d}"
        submission_id = f"SUB-{i:05d}"
        report_id = f"SIM-{i:04d}"

        # Case is created after its similarity report.
        created = report_dates[report_id] + timedelta(hours=1)
        created_text = date_text(created)

        cur.execute("""
            INSERT INTO cases
            (case_id, submission_id, report_id, reason,
             status, created_at, closed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            case_id,
            submission_id,
            report_id,
            "Similarity threshold triggered human review",
            "Under Review",
            created_text,
            None
        ))

        # Reviewer assignment.
        # No conflicted reviewer is assigned.
        reviewer = ((i - 1) % 30) + 1
        reviewer_id = f"REV-{reviewer:03d}"

        cur.execute("""
            INSERT INTO case_reviewers
            VALUES (?, ?, ?, 0)
        """, (
            case_id,
            reviewer_id,
            created_text
        ))

        # Case creation timeline event.
        cur.execute("""
            INSERT INTO case_events
            (case_id, actor, action, details, event_time)
            VALUES (?, ?, ?, ?, ?)
        """, (
            case_id,
            "System",
            "Case Created",
            "Case created for human review; flag is not a finding of guilt.",
            created_text
        ))

        # --------------------------------------------------
        # EVIDENCE
        # --------------------------------------------------

        evidence_count = random.randint(1, 3)

        for e in range(1, evidence_count + 1):

            evidence_id = f"EVD-{case_id}-{e:03d}"

            # Evidence is added after case creation.
            evidence_time = created + timedelta(minutes=e)

            evidence_time_text = date_text(evidence_time)

            cur.execute("""
                INSERT INTO evidence_items
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                evidence_id,
                case_id,
                f"Synthetic evidence item {e} for {case_id}",
                random.choice([
                    "Similarity Report",
                    "Submission",
                    "Reference"
                ]),
                f"evidence/{evidence_id}.txt",
                "System",
                evidence_time_text
            ))

            # Preserve evidence history.
            cur.execute("""
                INSERT INTO evidence_events
                (evidence_id, action, actor, event_time)
                VALUES (?, ?, ?, ?)
            """, (
                evidence_id,
                "Evidence Added",
                "System",
                evidence_time_text
            ))

        # --------------------------------------------------
        # HUMAN DECISIONS
        # --------------------------------------------------

        if i <= 240:

            decision_id = f"DEC-{i:04d}"

            decision = random.choice([
                "No Violation",
                "Violation Confirmed",
                "Inconclusive",
                "Warning"
            ])

            # Decision happens after evidence collection.
            decision_time = created + timedelta(hours=1)

            decision_time_text = date_text(decision_time)

            cur.execute("""
                INSERT INTO decisions
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                decision_id,
                case_id,
                reviewer_id,
                decision,
                "Synthetic human-review rationale; decision requires evidence.",
                decision_time_text
            ))

            cur.execute("""
                UPDATE cases
                SET status = 'Decision Made'
                WHERE case_id = ?
            """, (case_id,))

            # Decision timeline event.
            cur.execute("""
                INSERT INTO case_events
                (case_id, actor, action, details, event_time)
                VALUES (?, ?, ?, ?, ?)
            """, (
                case_id,
                reviewer_id,
                "Decision Recorded",
                f"Human decision recorded: {decision}",
                decision_time_text
            ))

            # --------------------------------------------------
            # INDEPENDENT APPEAL REVIEW
            # --------------------------------------------------

            if i <= 30:

                appeal_id = f"APL-{case_id}-01"

                # Choose a different reviewer.
                independent = (reviewer % 30) + 1
                independent_id = f"REV-{independent:03d}"

                submitted_time = (
                    decision_time + timedelta(hours=1)
                )

                reviewed_time = (
                    submitted_time + timedelta(hours=1)
                )

                submitted_text = date_text(submitted_time)
                reviewed_text = date_text(reviewed_time)

                outcome = (
                    "Accepted"
                    if i % 2 == 0
                    else "Rejected"
                )

                cur.execute("""
                    INSERT INTO appeals
                    (appeal_id, case_id, original_decision_id,
                     independent_reviewer_id, reason, status,
                     outcome_reason, submitted_at, reviewed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    appeal_id,
                    case_id,
                    decision_id,
                    independent_id,
                    "Synthetic appeal requesting independent review",
                    outcome,
                    "Synthetic independent appeal review outcome.",
                    submitted_text,
                    reviewed_text
                ))

                # Close only after independent appeal review.
                cur.execute("""
                    UPDATE cases
                    SET status = 'Closed', closed_at = ?
                    WHERE case_id = ?
                """, (
                    reviewed_text,
                    case_id
                ))

    # --------------------------------------------------
    # 8. AUDIT LOGS
    # --------------------------------------------------

    # Record case creation.
    case_rows = cur.execute("""
        SELECT case_id, created_at
        FROM cases
    """).fetchall()

    for row in case_rows:

        cur.execute("""
            INSERT INTO audit_logs
            (actor, action, entity_type, entity_id, details, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            "System",
            "Case Created",
            "Case",
            row["case_id"],
            "Case created for human review",
            row["created_at"]
        ))

    # Record every human decision.
    decision_rows = cur.execute("""
        SELECT decision_id, case_id, reviewer_id, decided_at
        FROM decisions
    """).fetchall()

    for row in decision_rows:

        cur.execute("""
            INSERT INTO audit_logs
            (actor, action, entity_type, entity_id, details, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            row["reviewer_id"],
            "Decision Recorded",
            "Decision",
            row["decision_id"],
            f"Decision recorded for {row['case_id']}",
            row["decided_at"]
        ))

    # Record every appeal.
    appeal_rows = cur.execute("""
        SELECT appeal_id, case_id, status, submitted_at
        FROM appeals
    """).fetchall()

    for row in appeal_rows:

        cur.execute("""
            INSERT INTO audit_logs
            (actor, action, entity_type, entity_id, details, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            "System",
            "Appeal Recorded",
            "Appeal",
            row["appeal_id"],
            f"Appeal recorded for {row['case_id']}: {row['status']}",
            row["submitted_at"]
        ))

    conn.commit()

    # --------------------------------------------------
    # 9. EXPORT DATABASE TABLES AS CSV
    # --------------------------------------------------

    tables = [
        "learners",
        "assessments",
        "integrity_rules",
        "reviewers",
        "submissions",
        "similarity_reports",
        "cases",
        "case_reviewers",
        "evidence_items",
        "decisions",
        "appeals",
        "case_events",
        "evidence_events",
        "audit_logs"
    ]

    for table in tables:

        rows = cur.execute(
            f"SELECT * FROM {table}"
        ).fetchall()

        if rows:

            with open(
                DATA_DIR / f"{table}.csv",
                "w",
                newline="",
                encoding="utf-8"
            ) as file:

                writer = csv.writer(file)

                writer.writerow(rows[0].keys())

                writer.writerows([
                    tuple(row) for row in rows
                ])

    # --------------------------------------------------
    # 10. SEPARATE GROUND TRUTH FILE
    # --------------------------------------------------

    with open(
        DATA_DIR / "ground_truth.csv",
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            "case_id",
            "expected_label",
            "dataset_note"
        ])

        for i in range(1, 301):

            label = random.choice([
                "No Violation",
                "Violation"
            ])

            writer.writerow([
                f"CASE-{i:04d}",
                label,
                "Synthetic evaluation label; not an application feature"
            ])

    # --------------------------------------------------
    # 11. FINAL COUNTS
    # --------------------------------------------------

    print("\nDATA GENERATION COMPLETE")
    print("=" * 45)

    for table in tables:

        count = cur.execute(
            f"SELECT COUNT(*) FROM {table}"
        ).fetchone()[0]

        print(f"{table}: {count}")

    print("\nGround truth: data/ground_truth.csv")
    print("Random seed:", SEED)

    conn.close()


# --------------------------------------------------
# RUN
# --------------------------------------------------

if __name__ == "__main__":
    generate()
