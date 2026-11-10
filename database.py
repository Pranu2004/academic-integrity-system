
import sqlite3
from pathlib import Path

# Database file will be created in the project folder
DB_NAME = Path(__file__).parent / "academic_integrity.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # 1. LEARNER
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS learners (
        learner_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        department TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

    # 2. ASSESSMENT
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS assessments (
        assessment_id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        subject TEXT NOT NULL,
        deadline TEXT NOT NULL,
        instructor TEXT NOT NULL
    )
    """)

    # 3. SUBMISSION
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS submissions (
        submission_id TEXT PRIMARY KEY,
        learner_id TEXT NOT NULL,
        assessment_id TEXT NOT NULL,
        submitted_at TEXT NOT NULL,
        content TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Submitted'
            CHECK(status IN ('Submitted', 'Flagged', 'Under Review',
                             'Cleared', 'Violation Confirmed')),
        FOREIGN KEY (learner_id) REFERENCES learners(learner_id),
        FOREIGN KEY (assessment_id) REFERENCES assessments(assessment_id)
    )
    """)

    # 4. INTEGRITY RULE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS integrity_rules (
        rule_id TEXT PRIMARY KEY,
        rule_name TEXT NOT NULL,
        review_threshold REAL NOT NULL
            CHECK(review_threshold BETWEEN 0 AND 100),
        high_priority_threshold REAL NOT NULL
            CHECK(high_priority_threshold BETWEEN 0 AND 100),
        effective_from TEXT NOT NULL,
        active INTEGER NOT NULL DEFAULT 1
            CHECK(active IN (0, 1))
    )
    """)

    # 5. SIMILARITY REPORT
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS similarity_reports (
        report_id TEXT PRIMARY KEY,
        submission_id TEXT NOT NULL,
        rule_id TEXT NOT NULL,
        similarity_score REAL NOT NULL
            CHECK(similarity_score BETWEEN 0 AND 100),
        matched_reference TEXT,
        report_date TEXT NOT NULL,
        flag_status TEXT NOT NULL,
        FOREIGN KEY (submission_id) REFERENCES submissions(submission_id),
        FOREIGN KEY (rule_id) REFERENCES integrity_rules(rule_id)
    )
    """)

    # 6. REVIEWER
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reviewers (
        reviewer_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        role TEXT NOT NULL
            CHECK(role IN ('Instructor', 'Administrator', 'Support')),
        department TEXT NOT NULL,
        available INTEGER NOT NULL DEFAULT 1
            CHECK(available IN (0, 1))
    )
    """)

    # 7. CASE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cases (
        case_id TEXT PRIMARY KEY,
        submission_id TEXT NOT NULL UNIQUE,
        report_id TEXT NOT NULL,
        reason TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Open'
            CHECK(status IN ('Open', 'Under Review', 'Decision Made',
                             'Appeal Pending', 'Closed')),
        created_at TEXT NOT NULL,
        closed_at TEXT,
        FOREIGN KEY (submission_id) REFERENCES submissions(submission_id),
        FOREIGN KEY (report_id) REFERENCES similarity_reports(report_id)
    )
    """)

    # Bridge table: multiple reviewers can handle multiple cases
    # 8. CASE REVIEWER
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS case_reviewers (
        case_id TEXT NOT NULL,
        reviewer_id TEXT NOT NULL,
        assigned_at TEXT NOT NULL,
        conflict_of_interest INTEGER NOT NULL DEFAULT 0
            CHECK(conflict_of_interest IN (0, 1)),
        PRIMARY KEY (case_id, reviewer_id),
        FOREIGN KEY (case_id) REFERENCES cases(case_id),
        FOREIGN KEY (reviewer_id) REFERENCES reviewers(reviewer_id)
    )
    """)

    # 9. EVIDENCE ITEM
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS evidence_items (
        evidence_id TEXT PRIMARY KEY,
        case_id TEXT NOT NULL,
        description TEXT NOT NULL,
        evidence_type TEXT NOT NULL,
        reference TEXT,
        added_by TEXT NOT NULL,
        added_at TEXT NOT NULL,
        FOREIGN KEY (case_id) REFERENCES cases(case_id)
    )
    """)

    # 10. DECISION
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS decisions (
        decision_id TEXT PRIMARY KEY,
        case_id TEXT NOT NULL,
        reviewer_id TEXT NOT NULL,
        decision TEXT NOT NULL
            CHECK(decision IN ('No Violation', 'Violation Confirmed',
                               'Inconclusive', 'Warning')),
        rationale TEXT NOT NULL,
        decided_at TEXT NOT NULL,
        FOREIGN KEY (case_id) REFERENCES cases(case_id),
        FOREIGN KEY (reviewer_id) REFERENCES reviewers(reviewer_id)
    )
    """)

    # 11. APPEAL
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS appeals (
        appeal_id TEXT PRIMARY KEY,
        case_id TEXT NOT NULL,
        original_decision_id TEXT NOT NULL,
        independent_reviewer_id TEXT,
        reason TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Submitted'
            CHECK(status IN ('Submitted', 'Under Review',
                             'Accepted', 'Rejected')),
        outcome_reason TEXT,
        submitted_at TEXT NOT NULL,
        reviewed_at TEXT,
        FOREIGN KEY (case_id) REFERENCES cases(case_id),
        FOREIGN KEY (original_decision_id) REFERENCES decisions(decision_id),
        FOREIGN KEY (independent_reviewer_id) REFERENCES reviewers(reviewer_id)
    )
    """)

    # 12. CASE EVENTS: complete chronological history
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS case_events (
        event_id INTEGER PRIMARY KEY AUTOINCREMENT,
        case_id TEXT NOT NULL,
        actor TEXT NOT NULL,
        action TEXT NOT NULL,
        details TEXT NOT NULL,
        event_time TEXT NOT NULL,
        FOREIGN KEY (case_id) REFERENCES cases(case_id)
    )
    """)

    # 13. EVIDENCE EVENTS: preserve evidence history
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS evidence_events (
        event_id INTEGER PRIMARY KEY AUTOINCREMENT,
        evidence_id TEXT NOT NULL,
        action TEXT NOT NULL,
        actor TEXT NOT NULL,
        event_time TEXT NOT NULL,
        FOREIGN KEY (evidence_id) REFERENCES evidence_items(evidence_id)
    )
    """)

    # 14. AUDIT LOG
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        actor TEXT NOT NULL,
        action TEXT NOT NULL,
        entity_type TEXT NOT NULL,
        entity_id TEXT NOT NULL,
        details TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()

    print("Database created successfully!")
    print("All 10 core entities and supporting tables are ready.")


if __name__ == "__main__":
    init_db()
