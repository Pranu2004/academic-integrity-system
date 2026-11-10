from pathlib import Path
from database import get_connection

docs = Path("docs")
docs.mkdir(exist_ok=True)

conn = get_connection()

try:
    tables = [
        row["name"]
        for row in conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type = 'table'
            AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
    ]

    schema = ["# Database Schema\n"]
    dictionary = ["# Database Data Dictionary\n"]

    for table in tables:
        columns = conn.execute(
            f'PRAGMA table_info("{table}")'
        ).fetchall()

        foreign_keys = conn.execute(
            f'PRAGMA foreign_key_list("{table}")'
        ).fetchall()

        create_sql = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
            (table,)
        ).fetchone()["sql"]

        schema.append(f"\n## {table}\n\n```sql\n{create_sql}\n```\n")

        dictionary.append(f"\n## {table}\n")
        dictionary.append(
            "| Column | Data Type | Not Null | Primary Key | Default |"
        )
        dictionary.append("|---|---|---|---|---|")

        for col in columns:
            dictionary.append(
                f"| {col['name']} | {col['type']} | "
                f"{bool(col['notnull'])} | {bool(col['pk'])} | "
                f"{col['dflt_value']} |"
            )

        if foreign_keys:
            dictionary.append("\n**Foreign Keys:**\n")
            for fk in foreign_keys:
                dictionary.append(
                    f"- `{fk['from']}` references "
                    f"`{fk['table']}.{fk['to']}`"
                )

    (docs / "schema.md").write_text(
        "\n".join(schema), encoding="utf-8"
    )

    (docs / "data_dictionary.md").write_text(
        "\n".join(dictionary), encoding="utf-8"
    )

    print("DOCUMENTATION GENERATED SUCCESSFULLY")
    print(f"Tables documented: {len(tables)}")
    print("docs/schema.md")
    print("docs/data_dictionary.md")

finally:
    conn.close()