import pandas as pd
from db import engine

def export_to_excel(filepath: str):
    query = """
    SELECT 
        c.name AS Company,
        p.address AS Property,
        f.name AS Flat,
        cert.cert_type AS Certificate_Type,
        cert.expiry_date AS Expiry_Date,
        cert.file_path AS File_Path
    FROM certificates cert
    JOIN flats f ON cert.flat_id = f.id
    JOIN properties p ON f.property_id = p.id
    JOIN companies c ON p.company_id = c.id
    ORDER BY cert.expiry_date ASC
    """
    df = pd.read_sql_query(query, engine)
    df.to_excel(filepath, index=False)
