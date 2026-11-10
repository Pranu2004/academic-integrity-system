import shutil
from pathlib import Path

import pytest
import database
from app import app
from database import get_connection


@pytest.fixture(autouse=True)
def isolated_database(tmp_path, monkeypatch):
    original_db = Path(database.DB_NAME)
    test_db = tmp_path / "test_academic_integrity.db"

    shutil.copy2(original_db, test_db)
    monkeypatch.setattr(database, "DB_NAME", str(test_db))

    app.config["TESTING"] = True

    yield


def test_dashboard_loads():
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200


def test_case_detail_loads():
    client = app.test_client()

    response = client.get("/case/CASE-0115")

    assert response.status_code == 200
    assert b"CASE-0115" in response.data


def create_test_reviewers():
    conn = get_connection()

    case = conn.execute("""
        SELECT c.case_id, l.department
        FROM cases c
        JOIN submissions s ON c.submission_id = s.submission_id
        JOIN learners l ON s.learner_id = l.learner_id
        LIMIT 1
    """).fetchone()

    assert case is not None

    conn.execute("""
        INSERT INTO reviewers
        (reviewer_id, name, role, department, available)
        VALUES (?, ?, 'Instructor', ?, 1)
    """, (
        "TEST-REV-CONFLICT",
        "Conflict Test",
        case["department"]
    ))

    conn.execute("""
        INSERT INTO reviewers
        (reviewer_id, name, role, department, available)
        VALUES (?, ?, 'Instructor', ?, 1)
    """, (
        "TEST-REV-VALID",
        "Valid Test",
        "__OTHER_DEPARTMENT__"
    ))

    conn.commit()
    conn.close()

    return case["case_id"]


def test_same_department_reviewer_is_blocked():
    case_id = create_test_reviewers()
    client = app.test_client()

    response = client.post(
        f"/assign-reviewer/{case_id}",
        data={"reviewer_id": "TEST-REV-CONFLICT"}
    )

    conn = get_connection()

    assignment = conn.execute("""
        SELECT COUNT(*) FROM case_reviewers
        WHERE case_id = ? AND reviewer_id = ?
    """, (case_id, "TEST-REV-CONFLICT")).fetchone()[0]

    conn.close()

    assert response.status_code == 302
    assert assignment == 0


def test_different_department_reviewer_is_allowed():
    case_id = create_test_reviewers()
    client = app.test_client()

    response = client.post(
        f"/assign-reviewer/{case_id}",
        data={"reviewer_id": "TEST-REV-VALID"}
    )

    conn = get_connection()

    assignment = conn.execute("""
        SELECT conflict_of_interest
        FROM case_reviewers
        WHERE case_id = ? AND reviewer_id = ?
    """, (case_id, "TEST-REV-VALID")).fetchone()

    conn.close()

    assert response.status_code == 302
    assert assignment is not None
    assert assignment["conflict_of_interest"] == 0


def create_test_appeal():
    client = app.test_client()
    conn = get_connection()

    decision = conn.execute("""
        SELECT case_id, reviewer_id
        FROM decisions
        LIMIT 1
    """).fetchone()

    assert decision is not None

    case_id = decision["case_id"]
    original_reviewer = decision["reviewer_id"]
    conn.close()

    response = client.post(
        f"/appeal/{case_id}",
        data={"reason": "Testing independent appeal review."}
    )

    assert response.status_code == 302

    conn = get_connection()
    appeal = conn.execute("""
        SELECT appeal_id, case_id, original_decision_id
        FROM appeals
        WHERE case_id = ?
        ORDER BY rowid DESC
        LIMIT 1
    """, (case_id,)).fetchone()

    assert appeal is not None

    result = {
        "appeal_id": appeal["appeal_id"],
        "case_id": case_id,
        "original_reviewer": original_reviewer
    }

    conn.close()
    return result


def test_appeal_cannot_be_reviewed_without_independent_reviewer():
    appeal = create_test_appeal()
    client = app.test_client()

    response = client.post(
        f"/review-appeal/{appeal['appeal_id']}",
        data={
            "outcome": "Appeal Upheld",
            "rationale": "Testing missing reviewer protection."
        }
    )

    conn = get_connection()
    result = conn.execute("""
        SELECT status, reviewed_at
        FROM appeals
        WHERE appeal_id = ?
    """, (appeal["appeal_id"],)).fetchone()
    conn.close()

    assert response.status_code == 302
    assert result["status"] == "Submitted"
    assert result["reviewed_at"] is None


def test_original_decision_maker_cannot_review_appeal():
    appeal = create_test_appeal()
    client = app.test_client()

    response = client.post(
        f"/assign-appeal-reviewer/{appeal['appeal_id']}",
        data={"reviewer_id": appeal["original_reviewer"]}
    )

    conn = get_connection()
    result = conn.execute("""
        SELECT independent_reviewer_id
        FROM appeals
        WHERE appeal_id = ?
    """, (appeal["appeal_id"],)).fetchone()
    conn.close()

    assert response.status_code == 302
    assert result["independent_reviewer_id"] is None


def test_independent_reviewer_can_complete_appeal():
    appeal = create_test_appeal()
    client = app.test_client()

    conn = get_connection()

    conn.execute("""
        INSERT INTO reviewers
        (reviewer_id, name, role, department, available)
        VALUES (?, ?, 'Instructor', ?, 1)
    """, (
        "TEST-APPEAL-REV",
        "Independent Appeal Reviewer",
        "__INDEPENDENT__"
    ))

    conn.commit()
    conn.close()

    assignment_response = client.post(
        f"/assign-appeal-reviewer/{appeal['appeal_id']}",
        data={"reviewer_id": "TEST-APPEAL-REV"}
    )

    assert assignment_response.status_code == 302

    review_response = client.post(
        f"/review-appeal/{appeal['appeal_id']}",
        data={
            "outcome": "Appeal Upheld",
            "rationale": "Independent review completed successfully."
        }
    )

    conn = get_connection()

    result = conn.execute("""
        SELECT status, independent_reviewer_id, reviewed_at,
               outcome_reason
        FROM appeals
        WHERE appeal_id = ?
    """, (appeal["appeal_id"],)).fetchone()

    conn.close()

    assert review_response.status_code == 302
    assert result["status"] == "Accepted"
    assert result["independent_reviewer_id"] == "TEST-APPEAL-REV"
    assert result["reviewed_at"] is not None
    assert "Independent review completed successfully." in result["outcome_reason"]
