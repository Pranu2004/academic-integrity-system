"""
Reproducible synthetic dataset generator for the Academic Integrity System.

Examples:
    python generate_data_v2.py --scale starter --seed 20261022
    python generate_data_v2.py --scale full --seed 20261022
    python generate_data_v2.py --scale starter --seed 20261022 --db-path starter_test.db

The default database is academic_integrity.db. The generator clears and rebuilds
the tables it owns in the selected database. Back up any database you need to keep.
"""
import argparse
import csv
import json
import random
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

import database


BASE = Path(__file__).resolve().parent

SCALES = {
    "starter": {
        "learners": 200,
        "assessments": 5,
        "reviewers": 6,
        "submissions": 1000,
        "reports": 100,
        "cases": 30,
        "decisions": 24,
        "appeals": 3,
    },
    "full": {
        "learners": 2000,
        "assessments": 20,
        "reviewers": 30,
        "submissions": 10000,
        "reports": 1000,
        "cases": 300,
        "decisions": 240,
        "appeals": 30,
    },
}

TABLES_TO_CLEAR = [
    "evidence_events", "case_events", "audit_logs", "appeals",
    "decisions", "evidence_items", "case_reviewers", "cases",
    "similarity_reports", "submissions", "integrity_rules",
    "reviewers", "assessments", "learners",
]

EXPORT_TABLES = [
    "learners", "assessments", "integrity_rules", "reviewers",
    "submissions", "similarity_reports", "cases", "case_reviewers",
    "evidence_items", "decisions", "appeals", "case_events",
    "evidence_events", "audit_logs",
]


def iso(dt):
    return dt.isoformat(timespec="seconds")


def make_date(rng, days_back=250):
    return datetime(2026, 1, 1) + timedelta(
        days=rng.randint(0, days_back),
        hours=rng.randint(8, 18),
        minutes=rng.randint(0, 59),
    )


def write_csv(path, headers, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)


def generate(scale="full", seed=20261022, db_path=None):
    if scale not in SCALES:
        raise ValueError(f"Unknown scale: {scale}")
    counts = SCALES[scale]
    rng = random.Random(seed)

    selected_db = Path(db_path) if db_path else BASE / "academic_integrity.db"
    if not selected_db.is_absolute():
        selected_db = BASE / selected_db
    selected_db.parent.mkdir(parents=True, exist_ok=True)

    # database.py uses this module-level path in get_connection().
    database.DB_NAME = selected_db
    database.init_db()

    conn = database.get_connection()
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON")

    try:
        cur.execute("BEGIN")
        for table in TABLES_TO_CLEAR:
            cur.execute(f"DELETE FROM {table}")

        n_learners = counts["learners"]
        n_assessments = counts["assessments"]
        n_reviewers = counts["reviewers"]
        n_submissions = counts["submissions"]
        n_reports = counts["reports"]
        n_cases = counts["cases"]
        n_decisions = counts["decisions"]
        n_appeals = counts["appeals"]

        # 1. Learners
        departments = ["CSE", "AIML", "ECE", "IT"]
        for i in range(1, n_learners + 1):
            cur.execute(
                "INSERT INTO learners VALUES (?, ?, ?, ?, ?)",
                (f"LRN-{i:05d}", f"Learner {i}",
                 f"learner{i}@example.edu", rng.choice(departments),
                 iso(make_date(rng))),
            )

        # 2. Assessments
        subjects = ["Python", "Database Systems", "AI", "Networks"]
        for i in range(1, n_assessments + 1):
            cur.execute(
                "INSERT INTO assessments VALUES (?, ?, ?, ?, ?)",
                (f"ASM-{i:03d}", f"Assessment {i}",
                 rng.choice(subjects), "2026-12-15T23:59:00",
                 f"Instructor {(i % 10) + 1}"),
            )

        # 3. Integrity rules: stable IDs and explicit thresholds.
        rules = [
            ("INT-2026-000001", "Standard Similarity Review", 30.0, 60.0),
            ("INT-2026-000002", "Programming Similarity Review", 35.0, 70.0),
            ("INT-2026-000003", "Written Assignment Review", 25.0, 55.0),
        ]
        for rule_id, name, threshold, high in rules:
            cur.execute(
                """INSERT INTO integrity_rules
                   (rule_id, rule_name, review_threshold,
                    high_priority_threshold, effective_from, active)
                   VALUES (?, ?, ?, ?, ?, 1)""",
                (rule_id, name, threshold, high, "2026-01-01"),
            )

        # 4. Reviewers
        for i in range(1, n_reviewers + 1):
            cur.execute(
                "INSERT INTO reviewers VALUES (?, ?, ?, ?, 1)",
                (f"REV-{i:03d}", f"Reviewer {i}",
                 ["Instructor", "Administrator", "Support"][(i - 1) % 3],
                 departments[(i - 1) % len(departments)]),
            )

        # 5. Submissions. Include legitimate quotations and shared templates.
        submission_dates = {}
        submission_statuses = {}
        for i in range(1, n_submissions + 1):
            learner_no = rng.randint(1, n_learners)
            assessment_no = rng.randint(1, n_assessments)
            submitted = make_date(rng)
            sid = f"SUB-2026-{i:06d}"
            submission_dates[sid] = submitted

            if i % 10 == 0:
                content = (
                    f"Synthetic submission {i}. Quoted material: "
                    '"Knowledge is built through careful observation." '
                    "The quotation is attributed and discussed by the learner."
                )
            elif i % 7 == 0:
                content = (
                    f"Synthetic submission {i}. Shared assignment template: "
                    "Introduction, Methodology, Results, Discussion, Conclusion. "
                    "The headings are common to the assessment."
                )
            else:
                content = (
                    f"Synthetic academic submission content number {i}. "
                    f"This is sample text for assessment {assessment_no}."
                )
            # Cases are the first n_cases reports; they are flagged below.
            status = "Flagged" if i <= n_cases else "Submitted"
            submission_statuses[sid] = status
            cur.execute(
                """INSERT INTO submissions
                   (submission_id, learner_id, assessment_id,
                    submitted_at, content, status)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (sid, f"LRN-{learner_no:05d}",
                 f"ASM-{assessment_no:03d}", iso(submitted), content, status),
            )

        # 6. Reports: scores are constructed against configured thresholds.
        report_dates = {}
        report_case_map = {}
        issue_types = {}
        ground_truth = {}
        for i in range(1, n_reports + 1):
            rule = rules[(i - 1) % len(rules)]
            rule_id, _, threshold, high_threshold = rule
            sid = f"SUB-2026-{i:06d}"
            if i <= n_cases:
                # Three deterministic cohorts: true violations, false positives,
                # and ambiguous cases. Scores trigger review, not guilt.
                cohort = (i - 1) % 3
                issue = ["documented_overlap", "shared_template_false_positive",
                         "legitimate_quotation"][cohort]
                issue_types[i] = issue
                expected = "Violation" if issue == "documented_overlap" else "No Violation"
                ground_truth[i] = expected
                score = round(max(threshold, min(99.0, threshold + 20 + (i % 17))), 2)
            else:
                issue = "below_threshold"
                score = round(max(0.0, threshold - 1 - (i % 15)), 2)

            flag_status = (
                "High Priority" if score >= high_threshold
                else "Review Required" if score >= threshold
                else "Not Flagged"
            )
            report_time = submission_dates[sid] + timedelta(hours=1)
            report_id = f"SIM-{sid}-01"
            report_dates[report_id] = report_time
            if i <= n_cases:
                report_case_map[i] = report_id

            cur.execute(
                """INSERT INTO similarity_reports
                   (report_id, submission_id, rule_id, similarity_score,
                    matched_reference, report_date, flag_status)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (report_id, sid, rule_id, score,
                 f"Reference-{((i - 1) % 50) + 1:03d}",
                 iso(report_time), flag_status),
            )

        # 7. Cases, assignments, evidence, decisions, appeals.
        # Assign two distinct non-conflicted reviewers per case where possible.
        ground_truth_rows = []
        for i in range(1, n_cases + 1):
            case_id = f"CASE-2026-{i:06d}"
            sid = f"SUB-2026-{i:06d}"
            report_id = f"SIM-{sid}-01"
            created = report_dates[report_id] + timedelta(hours=1)
            created_text = iso(created)

            learner_row = cur.execute(
                "SELECT department FROM learners WHERE learner_id = ?",
                (cur.execute(
                    "SELECT learner_id FROM submissions WHERE submission_id = ?",
                    (sid,),
                ).fetchone()["learner_id"],),
            ).fetchone()
            learner_department = learner_row["department"]

            # Primary reviewer must not share the learner's department.
            eligible = [
                r for r in range(1, n_reviewers + 1)
                if departments[(r - 1) % len(departments)] != learner_department
            ]
            if len(eligible) < 2:
                eligible = list(range(1, n_reviewers + 1))
            primary_no = eligible[(i - 1) % len(eligible)]
            secondary_no = eligible[i % len(eligible)]
            if secondary_no == primary_no:
                secondary_no = eligible[(eligible.index(primary_no) + 1) % len(eligible)]
            primary_id = f"REV-{primary_no:03d}"
            secondary_id = f"REV-{secondary_no:03d}"

            cur.execute(
                """INSERT INTO cases
                   (case_id, submission_id, report_id, reason,
                    status, created_at, closed_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (case_id, sid, report_id,
                 "Similarity threshold triggered human review; human assessment required.",
                 "Under Review", created_text, None),
            )
            for reviewer_id in (primary_id, secondary_id):
                cur.execute(
                    """INSERT INTO case_reviewers
                       (case_id, reviewer_id, assigned_at, conflict_of_interest)
                       VALUES (?, ?, ?, 0)""",
                    (case_id, reviewer_id, created_text),
                )

            cur.execute(
                """INSERT INTO case_events
                   (case_id, actor, action, details, event_time)
                   VALUES (?, ?, ?, ?, ?)""",
                (case_id, "System", "Case Created",
                 "Similarity flag triggered human review; it is not proof of misconduct.",
                 created_text),
            )

            evidence_count = 1 + (i % 3)
            for e in range(1, evidence_count + 1):
                evidence_id = f"EVD-{case_id}-{e:03d}"
                evidence_time = created + timedelta(minutes=e)
                evidence_type = ["Similarity Report", "Submission", "Reference"][(e - 1) % 3]
                cur.execute(
                    """INSERT INTO evidence_items
                       (evidence_id, case_id, description, evidence_type,
                        reference, added_by, added_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (evidence_id, case_id,
                     f"Synthetic {evidence_type.lower()} evidence for {case_id}",
                     evidence_type, f"evidence/{evidence_id}.txt",
                     "System", iso(evidence_time)),
                )
                cur.execute(
                    """INSERT INTO evidence_events
                       (evidence_id, action, actor, event_time)
                       VALUES (?, ?, ?, ?)""",
                    (evidence_id, "Evidence Added", "System", iso(evidence_time)),
                )

            issue = issue_types[i]
            expected = ground_truth[i]
            ground_truth_rows.append((
                case_id, expected, issue,
                "Synthetic label derived from documented scenario; excluded from application features."
            ))

            if i <= n_decisions:
                if expected == "Violation":
                    decision = "Violation Confirmed"
                elif issue == "shared_template_false_positive":
                    decision = "No Violation"
                else:
                    decision = "No Violation"
                decision_id = f"DEC-2026-{i:06d}"
                decision_time = created + timedelta(hours=1)
                decision_text = iso(decision_time)
                cur.execute(
                    """INSERT INTO decisions
                       (decision_id, case_id, reviewer_id, decision, rationale, decided_at)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (decision_id, case_id, primary_id, decision,
                     f"Human review considered the evidence and scenario category '{issue}'. "
                     "Similarity score alone was not treated as proof.",
                     decision_text),
                )
                cur.execute(
                    "UPDATE cases SET status = 'Decision Made' WHERE case_id = ?",
                    (case_id,),
                )
                cur.execute(
                    """INSERT INTO case_events
                       (case_id, actor, action, details, event_time)
                       VALUES (?, ?, ?, ?, ?)""",
                    (case_id, primary_id, "Decision Recorded",
                     f"Human decision recorded: {decision}", decision_text),
                )

                if i <= n_appeals:
                    appeal_id = f"APL-{case_id}-01"
                    # Third reviewer, not assigned to this case and not the decision maker.
                    appeal_candidates = [
                        r for r in range(1, n_reviewers + 1)
                        if r not in (primary_no, secondary_no)
                    ]
                    if not appeal_candidates:
                        raise ValueError("At least three reviewers are needed for independent appeals.")
                    independent_no = appeal_candidates[(i - 1) % len(appeal_candidates)]
                    independent_id = f"REV-{independent_no:03d}"
                    submitted = decision_time + timedelta(hours=1)
                    reviewed = submitted + timedelta(hours=1)

                    # Successful appeals are a deterministic subset of confirmed violations.
                    outcome = "Accepted" if expected == "Violation" and i % 2 == 1 else "Rejected"
                    cur.execute(
                        """INSERT INTO appeals
                           (appeal_id, case_id, original_decision_id,
                            independent_reviewer_id, reason, status,
                            outcome_reason, submitted_at, reviewed_at)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (appeal_id, case_id, decision_id, independent_id,
                         "Synthetic appeal requesting independent review",
                         outcome,
                         "Independent reviewer evaluated the recorded evidence and rationale.",
                         iso(submitted), iso(reviewed)),
                    )
                    cur.execute(
                        "UPDATE cases SET status = 'Closed', closed_at = ? WHERE case_id = ?",
                        (iso(reviewed), case_id),
                    )
                    cur.execute(
                        """INSERT INTO case_events
                           (case_id, actor, action, details, event_time)
                           VALUES (?, ?, ?, ?, ?)""",
                        (case_id, independent_id, "Appeal Reviewed",
                         f"Independent appeal outcome: {outcome}", iso(reviewed)),
                    )

        # 8. Audit logs from recorded workflow actions.
        for row in cur.execute("SELECT case_id, created_at FROM cases").fetchall():
            cur.execute(
                """INSERT INTO audit_logs
                   (actor, action, entity_type, entity_id, details, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                ("System", "Case Created", "Case", row["case_id"],
                 "Case created for human review", row["created_at"]),
            )
        for row in cur.execute(
            "SELECT decision_id, case_id, reviewer_id, decided_at FROM decisions"
        ).fetchall():
            cur.execute(
                """INSERT INTO audit_logs
                   (actor, action, entity_type, entity_id, details, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (row["reviewer_id"], "Decision Recorded", "Decision",
                 row["decision_id"], f"Decision recorded for {row['case_id']}",
                 row["decided_at"]),
            )
        for row in cur.execute(
            "SELECT appeal_id, case_id, status, submitted_at FROM appeals"
        ).fetchall():
            cur.execute(
                """INSERT INTO audit_logs
                   (actor, action, entity_type, entity_id, details, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                ("System", "Appeal Recorded", "Appeal", row["appeal_id"],
                 f"Appeal recorded for {row['case_id']}: {row['status']}",
                 row["submitted_at"]),
            )

        conn.commit()

        # Export CSV and JSON to a scale/seed-specific directory.
        export_dir = BASE / "data" / f"{scale}_seed_{seed}"
        export_dir.mkdir(parents=True, exist_ok=True)
        for table in EXPORT_TABLES:
            rows = cur.execute(f"SELECT * FROM {table}").fetchall()
            headers = list(rows[0].keys()) if rows else []
            csv_rows = [tuple(row) for row in rows]
            if headers:
                write_csv(export_dir / f"{table}.csv", headers, csv_rows)
            with (export_dir / f"{table}.json").open("w", encoding="utf-8") as f:
                json.dump([dict(row) for row in rows], f, indent=2)

        write_csv(
            export_dir / "ground_truth.csv",
            ["case_id", "expected_label", "issue_type", "dataset_note"],
            ground_truth_rows,
        )

        summary = {
            "scale": scale,
            "seed": seed,
            "database": str(selected_db),
            "counts": {
                table: cur.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                for table in EXPORT_TABLES
            },
            "ground_truth_rows": len(ground_truth_rows),
            "label_policy": "documented_overlap => Violation; shared-template and legitimate-quotation scenarios => No Violation",
        }
        (export_dir / "generation_summary.json").write_text(
            json.dumps(summary, indent=2), encoding="utf-8"
        )

        print("\nDATA GENERATION COMPLETE")
        print("=" * 45)
        print(f"Scale: {scale}")
        print(f"Seed: {seed}")
        print(f"Database: {selected_db}")
        for table, count in summary["counts"].items():
            print(f"{table}: {count}")
        print(f"Ground truth: {len(ground_truth_rows)} rows")
        print(f"Exports: {export_dir}")

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Generate reproducible academic integrity data.")
    parser.add_argument("--scale", choices=sorted(SCALES), default="full")
    parser.add_argument("--seed", type=int, default=20261022)
    parser.add_argument("--db-path", default=None,
                        help="Optional database path; use a separate path for safe testing.")
    args = parser.parse_args()
    generate(args.scale, args.seed, args.db_path)


if __name__ == "__main__":
    main()
