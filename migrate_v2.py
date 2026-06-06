import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'data.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

def add_column(table, column):
    try:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} VARCHAR")
        print(f"Added {column} to {table}")
    except sqlite3.OperationalError as e:
        print(f"Skipped {table}.{column}: {e}")

add_column('certificate_types', 'folder_path')
add_column('companies', 'folder_path')
add_column('properties', 'folder_path')
add_column('flats', 'folder_path')

conn.commit()
conn.close()
print("Migration v2 complete.")
