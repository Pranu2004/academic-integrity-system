# Academic Integrity Management System

A Flask and SQLite-based application for managing academic integrity cases through transparent, evidence-based human review.

## GitHub Repository
https://github.com/Pranu2004/academic-integrity-system

## Features
- Dashboard for submissions, similarity reports, cases and appeals.
- Similarity-based case flagging.
- Reviewer assignment and conflict-of-interest prevention.
- Evidence collection and history tracking.
- Human decisions with rationale.
- Independent appeal review.
- Case timelines and audit logs.
- Synthetic dataset generation and CSV exports.

**Important:** A similarity score is not proof of misconduct. Every flagged case requires human review.

## Technology Stack
- Python
- Flask
- SQLite
- HTML and CSS
- Pytest

## Dataset

Generated using random seed `20261022`.

| Entity | Records |
|---|---:|
| Learners | 2,000 |
| Assessments | 20 |
| Submissions | 10,000 |
| Similarity Reports | 1,000 |
| Cases | 300 |
| Reviewers | 30 |
| Decisions | 240 |
| Generated Appeals | 30 |

Ground-truth labels are stored separately in `data/ground_truth.csv`. All records are synthetic.

## Installation

Clone the repository:

```bash
git clone https://github.com/Pranu2004/academic-integrity-system.git
cd academic-integrity-system
```

Create and activate a virtual environment:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Generate the database and dataset:

```bash
python generate_data.py
```

Run the application:

```bash
python app.py
```

Open http://127.0.0.1:5000/

## Validation

```bash
python validate.py
```

## Automated Tests

```bash
python -m pytest tests -v
```

## Important Edge Cases
1. Similarity flags are not automatically treated as guilt.
2. Conflicted reviewers cannot review assigned cases.
3. Evidence history is preserved.
4. Appeals require independent review.

## Disclaimer

This project uses synthetic data and is intended for educational and demonstration purposes. It is not a production-ready disciplinary system.