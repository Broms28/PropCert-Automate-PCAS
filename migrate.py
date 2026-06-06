import sqlite3
import os
from db import init_db

db_path = os.path.join(os.path.dirname(__file__), 'data.db')

# Connect to DB
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Drop certificates table to allow recreation with nullable expiry_date
cursor.execute("DROP TABLE IF EXISTS certificates")
cursor.execute("DROP TABLE IF EXISTS certificate_types")

conn.commit()
conn.close()

# Recreate tables and initialize default cert types
init_db()
print("Migration successful.")
