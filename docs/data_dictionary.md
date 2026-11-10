# Database Data Dictionary


## appeals

| Column | Data Type | Not Null | Primary Key | Default |
|---|---|---|---|---|
| appeal_id | TEXT | False | True | None |
| case_id | TEXT | True | False | None |
| original_decision_id | TEXT | True | False | None |
| independent_reviewer_id | TEXT | False | False | None |
| reason | TEXT | True | False | None |
| status | TEXT | True | False | 'Submitted' |
| outcome_reason | TEXT | False | False | None |
| submitted_at | TEXT | True | False | None |
| reviewed_at | TEXT | False | False | None |

**Foreign Keys:**

- `independent_reviewer_id` references `reviewers.reviewer_id`
- `original_decision_id` references `decisions.decision_id`
- `case_id` references `cases.case_id`

## assessments

| Column | Data Type | Not Null | Primary Key | Default |
|---|---|---|---|---|
| assessment_id | TEXT | False | True | None |
| title | TEXT | True | False | None |
| subject | TEXT | True | False | None |
| deadline | TEXT | True | False | None |
| instructor | TEXT | True | False | None |

## audit_logs

| Column | Data Type | Not Null | Primary Key | Default |
|---|---|---|---|---|
| log_id | INTEGER | False | True | None |
| actor | TEXT | True | False | None |
| action | TEXT | True | False | None |
| entity_type | TEXT | True | False | None |
| entity_id | TEXT | True | False | None |
| details | TEXT | True | False | None |
| created_at | TEXT | True | False | None |

## case_events

| Column | Data Type | Not Null | Primary Key | Default |
|---|---|---|---|---|
| event_id | INTEGER | False | True | None |
| case_id | TEXT | True | False | None |
| actor | TEXT | True | False | None |
| action | TEXT | True | False | None |
| details | TEXT | True | False | None |
| event_time | TEXT | True | False | None |

**Foreign Keys:**

- `case_id` references `cases.case_id`

## case_reviewers

| Column | Data Type | Not Null | Primary Key | Default |
|---|---|---|---|---|
| case_id | TEXT | True | True | None |
| reviewer_id | TEXT | True | True | None |
| assigned_at | TEXT | True | False | None |
| conflict_of_interest | INTEGER | True | False | 0 |

**Foreign Keys:**

- `reviewer_id` references `reviewers.reviewer_id`
- `case_id` references `cases.case_id`

## cases

| Column | Data Type | Not Null | Primary Key | Default |
|---|---|---|---|---|
| case_id | TEXT | False | True | None |
| submission_id | TEXT | True | False | None |
| report_id | TEXT | True | False | None |
| reason | TEXT | True | False | None |
| status | TEXT | True | False | 'Open' |
| created_at | TEXT | True | False | None |
| closed_at | TEXT | False | False | None |

**Foreign Keys:**

- `report_id` references `similarity_reports.report_id`
- `submission_id` references `submissions.submission_id`

## decisions

| Column | Data Type | Not Null | Primary Key | Default |
|---|---|---|---|---|
| decision_id | TEXT | False | True | None |
| case_id | TEXT | True | False | None |
| reviewer_id | TEXT | True | False | None |
| decision | TEXT | True | False | None |
| rationale | TEXT | True | False | None |
| decided_at | TEXT | True | False | None |

**Foreign Keys:**

- `reviewer_id` references `reviewers.reviewer_id`
- `case_id` references `cases.case_id`

## evidence_events

| Column | Data Type | Not Null | Primary Key | Default |
|---|---|---|---|---|
| event_id | INTEGER | False | True | None |
| evidence_id | TEXT | True | False | None |
| action | TEXT | True | False | None |
| actor | TEXT | True | False | None |
| event_time | TEXT | True | False | None |

**Foreign Keys:**

- `evidence_id` references `evidence_items.evidence_id`

## evidence_items

| Column | Data Type | Not Null | Primary Key | Default |
|---|---|---|---|---|
| evidence_id | TEXT | False | True | None |
| case_id | TEXT | True | False | None |
| description | TEXT | True | False | None |
| evidence_type | TEXT | True | False | None |
| reference | TEXT | False | False | None |
| added_by | TEXT | True | False | None |
| added_at | TEXT | True | False | None |

**Foreign Keys:**

- `case_id` references `cases.case_id`

## integrity_rules

| Column | Data Type | Not Null | Primary Key | Default |
|---|---|---|---|---|
| rule_id | TEXT | False | True | None |
| rule_name | TEXT | True | False | None |
| review_threshold | REAL | True | False | None |
| high_priority_threshold | REAL | True | False | None |
| effective_from | TEXT | True | False | None |
| active | INTEGER | True | False | 1 |

## learners

| Column | Data Type | Not Null | Primary Key | Default |
|---|---|---|---|---|
| learner_id | TEXT | False | True | None |
| name | TEXT | True | False | None |
| email | TEXT | True | False | None |
| department | TEXT | True | False | None |
| created_at | TEXT | True | False | None |

## reviewers

| Column | Data Type | Not Null | Primary Key | Default |
|---|---|---|---|---|
| reviewer_id | TEXT | False | True | None |
| name | TEXT | True | False | None |
| role | TEXT | True | False | None |
| department | TEXT | True | False | None |
| available | INTEGER | True | False | 1 |

## similarity_reports

| Column | Data Type | Not Null | Primary Key | Default |
|---|---|---|---|---|
| report_id | TEXT | False | True | None |
| submission_id | TEXT | True | False | None |
| rule_id | TEXT | True | False | None |
| similarity_score | REAL | True | False | None |
| matched_reference | TEXT | False | False | None |
| report_date | TEXT | True | False | None |
| flag_status | TEXT | True | False | None |

**Foreign Keys:**

- `rule_id` references `integrity_rules.rule_id`
- `submission_id` references `submissions.submission_id`

## submissions

| Column | Data Type | Not Null | Primary Key | Default |
|---|---|---|---|---|
| submission_id | TEXT | False | True | None |
| learner_id | TEXT | True | False | None |
| assessment_id | TEXT | True | False | None |
| submitted_at | TEXT | True | False | None |
| content | TEXT | True | False | None |
| status | TEXT | True | False | 'Submitted' |

**Foreign Keys:**

- `assessment_id` references `assessments.assessment_id`
- `learner_id` references `learners.learner_id`