# Source Manifest

## Project
Academic Integrity Management System

## Data Source
All project datasets are synthetically generated.
No real student, learner, or institutional personal data is used.

## Generation Details
- Generator: generate_data.py
- Random seed: 20261022
- Database: SQLite
- Format: CSV, JSON and SQL

## Dataset Files

| Dataset | Description |
|---|---|
| learners.csv | Synthetic learner records |
| assessments.csv | Assessment details |
| submissions.csv | Learner submissions |
| similarity_reports.csv | Similarity analysis results |
| reviewers.csv | Reviewer information |
| cases.csv | Integrity review cases |
| case_reviewers.csv | Reviewer assignments |
| evidence_items.csv | Evidence records |
| evidence_events.csv | Evidence history |
| decisions.csv | Human review decisions |
| appeals.csv | Appeal records |
| case_events.csv | Case timeline events |
| audit_logs.csv | Audit trail |
| integrity_rules.csv | Integrity rules |
| ground_truth.csv | Separate synthetic reference labels |

## Reproducibility
Run the following command to regenerate the synthetic dataset:

```bash
python generate_data.py