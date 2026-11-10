from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, flash

from database import get_connection


app = Flask(__name__)
app.secret_key = "academic-integrity-demo-key"


def current_timestamp():
    """Return a consistent timestamp for events and audit records."""
    return datetime.now().isoformat(timespec="seconds")


def add_case_event(cur, case_id, actor, action, details, event_time):
    cur.execute(
        """
        INSERT INTO case_events
        (case_id, actor, action, details, event_time)
        VALUES (?, ?, ?, ?, ?)
        """,
        (case_id, actor, action, details, event_time),
    )


def add_audit_log(cur, actor, action, entity_type, entity_id, details, created_at):
    cur.execute(
        """
        INSERT INTO audit_logs
        (actor, action, entity_type, entity_id, details, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (actor, action, entity_type, entity_id, details, created_at),
    )


@app.route("/")
def dashboard():
    conn = get_connection()
    cur = conn.cursor()

    stats = {
        "submissions": cur.execute(
            "SELECT COUNT(*) FROM submissions"
        ).fetchone()[0],
        "reports": cur.execute(
            "SELECT COUNT(*) FROM similarity_reports"
        ).fetchone()[0],
        "cases": cur.execute(
            "SELECT COUNT(*) FROM cases"
        ).fetchone()[0],
        "appeals": cur.execute(
            "SELECT COUNT(*) FROM appeals"
        ).fetchone()[0],
    }

    cases = cur.execute(
        """
        SELECT c.case_id, c.status, c.reason, c.created_at,
               s.submission_id, sr.similarity_score,
               l.name AS learner_name
        FROM cases c
        JOIN submissions s ON c.submission_id = s.submission_id
        JOIN learners l ON s.learner_id = l.learner_id
        JOIN similarity_reports sr ON c.report_id = sr.report_id
        ORDER BY c.created_at DESC
        LIMIT 50
        """
    ).fetchall()

    conn.close()
    return render_template("dashboard.html", stats=stats, cases=cases)


@app.route("/case/<case_id>")
def case_detail(case_id):
    conn = get_connection()
    cur = conn.cursor()

    case = cur.execute(
        """
        SELECT c.*, s.submission_id, s.content,
               l.name AS learner_name, sr.similarity_score
        FROM cases c
        JOIN submissions s ON c.submission_id = s.submission_id
        JOIN learners l ON s.learner_id = l.learner_id
        JOIN similarity_reports sr ON c.report_id = sr.report_id
        WHERE c.case_id = ?
        """,
        (case_id,),
    ).fetchone()

    if not case:
        conn.close()
        return "Case not found", 404

    evidence = cur.execute(
        """
        SELECT * FROM evidence_items
        WHERE case_id = ?
        ORDER BY added_at DESC
        """,
        (case_id,),
    ).fetchall()

    reviewers = cur.execute(
        """
        SELECT r.reviewer_id, r.name, cr.conflict_of_interest
        FROM case_reviewers cr
        JOIN reviewers r ON cr.reviewer_id = r.reviewer_id
        WHERE cr.case_id = ?
        """,
        (case_id,),
    ).fetchall()

    available_reviewers = cur.execute(
        """
        SELECT reviewer_id, name, role, department
        FROM reviewers
        WHERE available = 1
        ORDER BY name
        """
    ).fetchall()

    decisions = cur.execute(
        """
        SELECT d.*, r.name AS reviewer_name
        FROM decisions d
        JOIN reviewers r ON d.reviewer_id = r.reviewer_id
        WHERE d.case_id = ?
        ORDER BY d.decided_at DESC
        """,
        (case_id,),
    ).fetchall()

    appeals = cur.execute(
        """
        SELECT a.*, r.name AS independent_reviewer
        FROM appeals a
        LEFT JOIN reviewers r
        ON a.independent_reviewer_id = r.reviewer_id
        WHERE a.case_id = ?
        ORDER BY a.submitted_at DESC
        """,
        (case_id,),
    ).fetchall()

    events = cur.execute(
        """
        SELECT * FROM case_events
        WHERE case_id = ?
        ORDER BY event_time DESC
        """,
        (case_id,),
    ).fetchall()

    conn.close()

    return render_template(
        "case_detail.html",
        case=case,
        evidence=evidence,
        reviewers=reviewers,
        available_reviewers=available_reviewers,
        decisions=decisions,
        appeals=appeals,
        events=events,
    )


@app.route("/assign-reviewer/<case_id>", methods=["POST"])
def assign_reviewer(case_id):
    reviewer_id = request.form.get("reviewer_id", "").strip()

    conn = get_connection()
    cur = conn.cursor()

    case = cur.execute("""
        SELECT l.department AS learner_department
        FROM cases c
        JOIN submissions s ON c.submission_id = s.submission_id
        JOIN learners l ON s.learner_id = l.learner_id
        WHERE c.case_id = ?
    """, (case_id,)).fetchone()

    reviewer = cur.execute("""
        SELECT reviewer_id, department
        FROM reviewers
        WHERE reviewer_id = ? AND available = 1
    """, (reviewer_id,)).fetchone()

    if not case or not reviewer:
        conn.close()
        flash("Case or available reviewer not found.")
        return redirect(url_for("case_detail", case_id=case_id))

    if reviewer["department"] == case["learner_department"]:
        conn.close()
        flash("Reviewer assignment blocked: department conflict of interest.")
        return redirect(url_for("case_detail", case_id=case_id))

    exists = cur.execute("""
        SELECT 1 FROM case_reviewers
        WHERE case_id = ? AND reviewer_id = ?
    """, (case_id, reviewer_id)).fetchone()

    if exists:
        conn.close()
        flash("Reviewer is already assigned.")
        return redirect(url_for("case_detail", case_id=case_id))

    now = current_timestamp()

    cur.execute("""
        INSERT INTO case_reviewers
        (case_id, reviewer_id, assigned_at, conflict_of_interest)
        VALUES (?, ?, ?, 0)
    """, (case_id, reviewer_id, now))

    add_case_event(
        cur, case_id, "Administrator",
        "Reviewer Assigned",
        f"Reviewer {reviewer_id} assigned after department conflict check.",
        now
    )

    add_audit_log(
        cur, "Administrator", "Reviewer Assigned",
        "Case", case_id,
        f"Reviewer {reviewer_id} assigned after department conflict check.",
        now
    )

    conn.commit()
    conn.close()

    flash("Reviewer assigned successfully.")
    return redirect(url_for("case_detail", case_id=case_id))


@app.route("/add-evidence/<case_id>", methods=["POST"])
def add_evidence(case_id):
    description = request.form.get("description", "").strip()
    evidence_type = request.form.get("evidence_type", "").strip()

    if not description or not evidence_type:
        flash("Enter evidence description and type.")
        return redirect(url_for("case_detail", case_id=case_id))

    conn = get_connection()
    cur = conn.cursor()

    case_exists = cur.execute(
        "SELECT 1 FROM cases WHERE case_id = ?", (case_id,)
    ).fetchone()

    if not case_exists:
        conn.close()
        return "Case not found", 404

    count = cur.execute(
        "SELECT COUNT(*) FROM evidence_items WHERE case_id = ?",
        (case_id,),
    ).fetchone()[0]

    evidence_id = f"EVD-{case_id}-{count + 1:03d}"
    now = current_timestamp()

    cur.execute(
        """
        INSERT INTO evidence_items
        (evidence_id, case_id, description, evidence_type,
            reference, added_by, added_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            evidence_id,
            case_id,
            description,
            evidence_type,
            "",
            "Administrator",
            now,
        ),
    )

    cur.execute(
        """
        INSERT INTO evidence_events
        (evidence_id, action, actor, event_time)
        VALUES (?, ?, ?, ?)
        """,
        (evidence_id, "Evidence Added", "Administrator", now),
    )

    add_case_event(
        cur,
        case_id,
        "Administrator",
        "Evidence Added",
        f"New evidence {evidence_id} added.",
        now,
    )

    add_audit_log(
        cur,
        "Administrator",
        "Evidence Added",
        "Evidence",
        evidence_id,
        description,
        now,
    )

    conn.commit()
    conn.close()

    flash("Evidence added and history recorded.")
    return redirect(url_for("case_detail", case_id=case_id))


@app.route("/add-decision/<case_id>", methods=["POST"])
def add_decision(case_id):
    reviewer_id = request.form.get("reviewer_id", "").strip()
    decision = request.form.get("decision", "").strip()
    rationale = request.form.get("rationale", "").strip()

    allowed = [
        "No Violation",
        "Violation Confirmed",
        "Inconclusive",
        "Warning",
    ]

    if decision not in allowed or not rationale:
        flash("Select a valid decision and provide a rationale.")
        return redirect(url_for("case_detail", case_id=case_id))

    conn = get_connection()
    cur = conn.cursor()

    assigned = cur.execute(
        """
        SELECT 1 FROM case_reviewers
        WHERE case_id = ? AND reviewer_id = ?
        AND conflict_of_interest = 0
        """,
        (case_id, reviewer_id),
    ).fetchone()

    if not assigned:
        conn.close()
        flash("Only an assigned, non-conflicted reviewer can decide.")
        return redirect(url_for("case_detail", case_id=case_id))

    count = cur.execute(
        "SELECT COUNT(*) FROM decisions WHERE case_id = ?",
        (case_id,),
    ).fetchone()[0]

    decision_id = f"DEC-{case_id}-{count + 1:02d}"
    now = current_timestamp()

    cur.execute(
        """
        INSERT INTO decisions
        (decision_id, case_id, reviewer_id, decision, rationale, decided_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (decision_id, case_id, reviewer_id, decision, rationale, now),
    )

    cur.execute(
        """
        UPDATE cases SET status = 'Decision Made'
        WHERE case_id = ?
        """,
        (case_id,),
    )

    add_case_event(
        cur, case_id, reviewer_id, "Decision Recorded", rationale, now
    )

    add_audit_log(
        cur,
        reviewer_id,
        "Decision Recorded",
        "Decision",
        decision_id,
        f"{decision}: {rationale}",
        now,
    )

    conn.commit()
    conn.close()

    flash("Human decision recorded successfully.")
    return redirect(url_for("case_detail", case_id=case_id))


@app.route("/appeal/<case_id>", methods=["POST"])
def submit_appeal(case_id):
    reason = request.form.get("reason", "").strip()

    if not reason:
        flash("Please provide an appeal reason.")
        return redirect(url_for("case_detail", case_id=case_id))

    conn = get_connection()
    cur = conn.cursor()

    decision = cur.execute(
        """
        SELECT decision_id FROM decisions
        WHERE case_id = ?
        ORDER BY decided_at DESC LIMIT 1
        """,
        (case_id,),
    ).fetchone()

    if not decision:
        conn.close()
        flash("An appeal requires an existing decision.")
        return redirect(url_for("case_detail", case_id=case_id))

    number = cur.execute(
        "SELECT COUNT(*) FROM appeals WHERE case_id = ?",
        (case_id,),
    ).fetchone()[0] + 1

    appeal_id = f"APL-{case_id}-{number:02d}"
    now = current_timestamp()

    cur.execute(
        """
        INSERT INTO appeals
        (appeal_id, case_id, original_decision_id, reason, status, submitted_at)
        VALUES (?, ?, ?, ?, 'Submitted', ?)
        """,
        (appeal_id, case_id, decision["decision_id"], reason, now),
    )

    cur.execute(
        """
        UPDATE cases SET status = 'Appeal Pending'
        WHERE case_id = ?
        """,
        (case_id,),
    )

    add_case_event(
        cur, case_id, "Learner", "Appeal Submitted", reason, now
    )

    add_audit_log(
        cur,
        "Learner",
        "Appeal Submitted",
        "Appeal",
        appeal_id,
        reason,
        now,
    )

    conn.commit()
    conn.close()

    flash("Appeal submitted. Independent review is pending.")
    return redirect(url_for("case_detail", case_id=case_id))


@app.route("/assign-appeal-reviewer/<appeal_id>", methods=["POST"])
def assign_appeal_reviewer(appeal_id):
    reviewer_id = request.form.get("reviewer_id", "").strip()

    conn = get_connection()
    cur = conn.cursor()

    appeal = cur.execute(
        """
        SELECT a.appeal_id, a.case_id, a.status,
               a.independent_reviewer_id,
               d.reviewer_id AS original_reviewer
        FROM appeals a
        JOIN decisions d ON a.original_decision_id = d.decision_id
        WHERE a.appeal_id = ?
        """,
        (appeal_id,),
    ).fetchone()

    if not appeal:
        conn.close()
        flash("Appeal not found.")
        return redirect(url_for("dashboard"))

    reviewer = cur.execute(
        """
        SELECT reviewer_id, name
        FROM reviewers
        WHERE reviewer_id = ? AND available = 1
        """,
        (reviewer_id,),
    ).fetchone()

    if not reviewer:
        conn.close()
        flash("Select an available reviewer.")
        return redirect(url_for("case_detail", case_id=appeal["case_id"]))

    if reviewer_id == appeal["original_reviewer"]:
        conn.close()
        flash("The original decision-maker cannot review this appeal.")
        return redirect(url_for("case_detail", case_id=appeal["case_id"]))

    if appeal["status"] != "Submitted" or appeal["independent_reviewer_id"]:
        conn.close()
        flash("This appeal is not awaiting reviewer assignment.")
        return redirect(url_for("case_detail", case_id=appeal["case_id"]))

    # An appeal reviewer must not have participated in the original case.
    case_assignment = cur.execute(
        """
        SELECT conflict_of_interest
        FROM case_reviewers
        WHERE case_id = ? AND reviewer_id = ?
        """,
        (appeal["case_id"], reviewer_id),
    ).fetchone()

    if case_assignment:
        conn.close()
        flash("A case-assigned reviewer cannot independently review this appeal.")
        return redirect(url_for("case_detail", case_id=appeal["case_id"]))

    now = current_timestamp()

    cur.execute(
        """
        UPDATE appeals
        SET independent_reviewer_id = ?
        WHERE appeal_id = ?
          AND status = 'Submitted'
          AND independent_reviewer_id IS NULL
        """,
        (reviewer_id, appeal_id),
    )

    if cur.rowcount != 1:
        conn.rollback()
        conn.close()
        flash("Reviewer assignment could not be completed. Refresh and try again.")
        return redirect(url_for("case_detail", case_id=appeal["case_id"]))

    add_case_event(
        cur,
        appeal["case_id"],
        "Administrator",
        "Independent Reviewer Assigned",
        f"{reviewer['name']} ({reviewer_id}) assigned to appeal {appeal_id}.",
        now,
    )

    add_audit_log(
        cur,
        "Administrator",
        "Appeal Reviewer Assigned",
        "Appeal",
        appeal_id,
        f"Independent reviewer assigned: {reviewer_id}",
        now,
    )

    conn.commit()
    conn.close()

    flash("Independent reviewer assigned successfully.")
    return redirect(url_for("case_detail", case_id=appeal["case_id"]))


@app.route("/review-appeal/<appeal_id>", methods=["POST"])
def review_appeal(appeal_id):
    outcome = request.form.get("outcome", "").strip()
    rationale = request.form.get("rationale", "").strip()

    allowed_outcomes = ["Appeal Upheld", "Appeal Rejected"]

    if outcome not in allowed_outcomes or not rationale:
        flash("Select a valid appeal outcome and provide a review rationale.")
        return redirect(url_for("dashboard"))

    conn = get_connection()
    cur = conn.cursor()

    appeal = cur.execute(
        """
        SELECT a.*, d.reviewer_id AS original_reviewer
        FROM appeals a
        JOIN decisions d ON a.original_decision_id = d.decision_id
        WHERE a.appeal_id = ?
        """,
        (appeal_id,),
    ).fetchone()

    if not appeal:
        conn.close()
        flash("Appeal not found.")
        return redirect(url_for("dashboard"))

    reviewer_id = appeal["independent_reviewer_id"]

    if not reviewer_id or reviewer_id == appeal["original_reviewer"]:
        conn.close()
        flash("A valid independent reviewer must be assigned first.")
        return redirect(url_for("case_detail", case_id=appeal["case_id"]))

    if appeal["status"] != "Submitted" or appeal["reviewed_at"]:
        conn.close()
        flash("This appeal has already been reviewed.")
        return redirect(url_for("case_detail", case_id=appeal["case_id"]))

    # Recheck independence at the time of review, not only at assignment.
    case_assignment = cur.execute(
        """
        SELECT 1 FROM case_reviewers
        WHERE case_id = ? AND reviewer_id = ?
        """,
        (appeal["case_id"], reviewer_id),
    ).fetchone()

    if case_assignment:
        conn.close()
        flash("The assigned reviewer is not independent of this case.")
        return redirect(url_for("case_detail", case_id=appeal["case_id"]))

    now = current_timestamp()
    outcome_details = f"{outcome}: {rationale}"

    appeal_status = (
        "Accepted" if outcome == "Appeal Upheld" else "Rejected"
    )

    cur.execute(
        """
        UPDATE appeals
        SET status = ?,
            outcome_reason = ?,
            reviewed_at = ?
        WHERE appeal_id = ?
          AND status = 'Submitted'
          AND reviewed_at IS NULL
        """,
        (appeal_status, outcome_details, now, appeal_id),
    )

    if cur.rowcount != 1:
        conn.rollback()
        conn.close()
        flash("Appeal review could not be saved. Refresh and try again.")
        return redirect(url_for("case_detail", case_id=appeal["case_id"]))

    # Keep the case open if another appeal for this case is still pending.
    pending_appeal = cur.execute(
        """
        SELECT 1 FROM appeals
        WHERE case_id = ? AND appeal_id != ? AND status = 'Submitted'
        LIMIT 1
        """,
        (appeal["case_id"], appeal_id),
    ).fetchone()

    new_case_status = "Appeal Pending" if pending_appeal else "Closed"

    cur.execute(
        """
        UPDATE cases SET status = ?
        WHERE case_id = ?
        """,
        (new_case_status, appeal["case_id"]),
    )

    add_case_event(
        cur,
        appeal["case_id"],
        reviewer_id,
        "Appeal Reviewed",
        outcome_details,
        now,
    )

    add_audit_log(
        cur,
        reviewer_id,
        "Appeal Reviewed",
        "Appeal",
        appeal_id,
        outcome_details,
        now,
    )

    conn.commit()
    conn.close()

    flash("Independent appeal review completed successfully.")
    return redirect(url_for("case_detail", case_id=appeal["case_id"]))


if __name__ == "__main__":
    app.run(debug=True)

