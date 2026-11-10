import json
from pathlib import Path
from database import get_connection

# Create exports folder
export_dir = Path("exports")
export_dir.mkdir(exist_ok=True)

# Connect to the existing validated database
conn = get_connection()

try:
    # Get all project tables
    tables = [
        row["name"]
        for row in conn.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
    ]

    # Export all table records to JSON
    database_data = {}

    for table in tables:
        rows = conn.execute(f'SELECT * FROM "{table}"').fetchall()
        database_data[table] = [dict(row) for row in rows]

    json_path = export_dir / "seed_data.json"

    with open(json_path, "w", encoding="utf-8") as file:
        json.dump(database_data, file, indent=4, default=str)

    # Export complete SQL schema and data
    sql_path = export_dir / "seed_data.sql"

    with open(sql_path, "w", encoding="utf-8") as file:
        for statement in conn.iterdump():
            file.write(statement + "\n")

    print("EXPORT COMPLETED SUCCESSFULLY")
    print(f"Tables exported: {len(tables)}")
    print(f"JSON: {json_path}")
    print(f"SQL: {sql_path}")

finally:
    conn.close()