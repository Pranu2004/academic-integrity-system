from database import get_connection


def test_database_connection():
    conn = get_connection()
    assert conn is not None
    conn.close()


def test_foreign_keys_enabled():
    conn = get_connection()
    result = conn.execute("PRAGMA foreign_keys").fetchone()[0]
    conn.close()

    assert result == 1


def test_required_tables_exist():
    conn = get_connection()

    tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }

    conn.close()

    required_tables = {
        "learners",
        "assessments",
        "submissions",
        "similarity_reports",
        "reviewers",
        "cases",
        "evidence_items",
        "decisions",
        "appeals",
        "case_events",
        "evidence_events",
        "audit_logs",
    }

    assert required_tables.issubset(tables)
