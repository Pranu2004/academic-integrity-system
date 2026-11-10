# Database Schema


## appeals

```sql
CREATE TABLE appeals (
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
```


## assessments

```sql
CREATE TABLE assessments (
        assessment_id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        subject TEXT NOT NULL,
        deadline TEXT NOT NULL,
        instructor TEXT NOT NULL
    )
```


## audit_logs

```sql
CREATE TABLE audit_logs (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        actor TEXT NOT NULL,
        action TEXT NOT NULL,
        entity_type TEXT NOT NULL,
        entity_id TEXT NOT NULL,
        details TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
```


## case_events

```sql
CREATE TABLE case_events (
        event_id INTEGER PRIMARY KEY AUTOINCREMENT,
        case_id TEXT NOT NULL,
        actor TEXT NOT NULL,
        action TEXT NOT NULL,
        details TEXT NOT NULL,
        event_time TEXT NOT NULL,
        FOREIGN KEY (case_id) REFERENCES cases(case_id)
    )
```


## case_reviewers

```sql
CREATE TABLE case_reviewers (
        case_id TEXT NOT NULL,
        reviewer_id TEXT NOT NULL,
        assigned_at TEXT NOT NULL,
        conflict_of_interest INTEGER NOT NULL DEFAULT 0
            CHECK(conflict_of_interest IN (0, 1)),
        PRIMARY KEY (case_id, reviewer_id),
        FOREIGN KEY (case_id) REFERENCES cases(case_id),
        FOREIGN KEY (reviewer_id) REFERENCES reviewers(reviewer_id)
    )
```


## cases

```sql
CREATE TABLE cases (
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
```


## decisions

```sql
CREATE TABLE decisions (
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
```


## evidence_events

```sql
CREATE TABLE evidence_events (
        event_id INTEGER PRIMARY KEY AUTOINCREMENT,
        evidence_id TEXT NOT NULL,
        action TEXT NOT NULL,
        actor TEXT NOT NULL,
        event_time TEXT NOT NULL,
        FOREIGN KEY (evidence_id) REFERENCES evidence_items(evidence_id)
    )
```


## evidence_items

```sql
CREATE TABLE evidence_items (
        evidence_id TEXT PRIMARY KEY,
        case_id TEXT NOT NULL,
        description TEXT NOT NULL,
        evidence_type TEXT NOT NULL,
        reference TEXT,
        added_by TEXT NOT NULL,
        added_at TEXT NOT NULL,
        FOREIGN KEY (case_id) REFERENCES cases(case_id)
    )
```


## integrity_rules

```sql
CREATE TABLE integrity_rules (
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
```


## learners

```sql
CREATE TABLE learners (
        learner_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        department TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
```


## reviewers

```sql
CREATE TABLE reviewers (
        reviewer_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        role TEXT NOT NULL
            CHECK(role IN ('Instructor', 'Administrator', 'Support')),
        department TEXT NOT NULL,
        available INTEGER NOT NULL DEFAULT 1
            CHECK(available IN (0, 1))
    )
```


## similarity_reports

```sql
CREATE TABLE similarity_reports (
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
```


## submissions

```sql
CREATE TABLE submissions (
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
```
