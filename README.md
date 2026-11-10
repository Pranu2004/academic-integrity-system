# Academic Integrity Management System

A Flask and SQLite-based application for managing academic integrity cases through transparent, evidence-based human review, reviewer assignment, evidence tracking, audit trails, and independent appeals.

## GitHub Repository

[Academic Integrity Management System](https://github.com/Pranu2004/academic-integrity-system)

## Features

- **Dashboard:** View submissions, similarity reports, cases, and appeals.
- **Similarity-Based Flagging:** Identify submissions that require further review.
- **Reviewer Assignment:** Assign reviewers while preventing conflicts of interest.
- **Evidence Management:** Collect evidence and preserve its history.
- **Human Decision-Making:** Record decisions with clear explanations and rationale.
- **Independent Appeals:** Support independent review of appealed decisions.
- **Case Timeline:** Track important events throughout the case lifecycle.
- **Audit Logs:** Maintain records of important system actions.
- **Synthetic Dataset Generation:** Generate reproducible test data.
- **Data Exports:** Export database records in JSON and SQL formats.

> **Important principle:** A similarity score is not proof of misconduct. A flagged submission must be evaluated by a human reviewer, with evidence and due process considered before a decision is made.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Backend development and data generation |
| Flask | Web application and routing |
| SQLite | Relational database |
| HTML | Application interface |
| CSS | Styling |
| Pytest | Automated testing |

## Dataset

The project uses a synthetic dataset generated with the fixed random seed `20261022`.

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

Ground-truth labels are stored separately in `data/ground_truth.csv` and are not used as input features for the application workflow.

All dataset records are synthetic and intended for educational and demonstration purposes.

## Project Structure

```text
academic-integrity-system/
│
├── app.py
├── database.py
├── generate_data.py
├── validate.py
├── export_data.py
├── generate_docs.py
├── requirements.txt
├── README.md
│
├── data/
│   └── ground_truth.csv
│
├── exports/
│   ├── seed_data.json
│   └── seed_data.sql
│
├── docs/
│   ├── schema.md
│   ├── data_dictionary.md
│   ├── source_manifest.md
│   └── validation_summary.md
│
├── templates/
│   ├── dashboard.html
│   └── case_detail.html
│
├── static/
│   └── style.css
│
└── tests/
    ├── test_app.py
    └── test_database.py
```

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/Pranu2004/academic-integrity-system.git
cd academic-integrity-system
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate the virtual environment

**Windows PowerShell:**

```powershell
.\venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Generate the database and synthetic dataset

```bash
python generate_data.py
```

### 6. Run the application

```bash
python app.py
```

Open the application in your browser:

http://127.0.0.1:5000/

## Validation

Run the validation script:

```bash
python validate.py
```

The validation process checks:

- Required dataset volumes.
- Primary key and foreign key integrity.
- Unique identifiers.
- Reviewer conflict-of-interest restrictions.
- Evidence history preservation.
- Independent appeal review.
- Case lifecycle and decision rules.
- Ground-truth dataset separation.

**Latest validation results:**

- Passed: 21
- Failed: 0

## Automated Tests

Run the automated test suite:

```bash
python -m pytest tests -v
```

**Latest test results:**

- Passed: 5
- Failed: 0

## Important Edge Cases

The application addresses the following scenarios:

1. **Similarity flag is not automatic guilt:** A flagged submission requires human review.
2. **Reviewer conflict of interest:** Conflicted reviewers cannot review assigned cases.
3. **Evidence added after a decision:** Evidence history is preserved through event records.
4. **Independent appeal review:** An appeal must be reviewed by an independent reviewer, not the original decision-maker.

## Additional Deliverables

### Data Exports

- `exports/seed_data.json` – Database records exported in JSON format.
- `exports/seed_data.sql` – SQLite schema and data export.

### Technical Documentation

- `docs/schema.md` – Database schema and table definitions.
- `docs/data_dictionary.md` – Column names, data types, and relationships.
- `docs/source_manifest.md` – Synthetic data source, generation details, and reproducibility information.
- `docs/validation_summary.md` – Validation results and edge-case checks.

### Data Reproducibility

The synthetic dataset uses a fixed random seed (`20261022`).

The following commands regenerate the dataset, validate it, export database records, and generate technical documentation:

```bash
python generate_data.py
python validate.py
python export_data.py
python generate_docs.py
```

**Note:** Running `generate_data.py` regenerates the database. Back up any manually created demonstration records before running it.

## Future Enhancements

- User authentication and role-based access control.
- Advanced reviewer workload management.
- Improved reporting and analytics dashboard.
- Automated integration testing.
- Deployment to a cloud hosting platform.

## Disclaimer

This project uses synthetic data and is intended for educational, academic, and demonstration purposes. It is not a production-ready disciplinary system. Real-world deployment would require appropriate security, privacy, authorization, and institutional governance controls.

