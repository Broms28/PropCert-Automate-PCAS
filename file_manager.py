import os
import shutil
from datetime import date
from typing import Optional
from db import get_session, CertificateType
from config_manager import get_base_dir

BASE_DIR = get_base_dir()

def get_safe_name(name: str) -> str:
    return "".join(c for c in name if c.isalnum() or c in " -_,").strip()

def save_certificate(temp_pdf_path: str, comp_name: str, prop_address: str, flat_name: str, type_name: str, expiry_date: Optional[date]) -> str:
    """
    Resolves the folder hierarchy dynamically.
    The root folder is the Certificate Type's custom folder (if set), otherwise defaults to C:\Office Workfiles\[Type].
    Inside it: Company -> Property -> Flat (if not General).
    """
    session = get_session()
    
    cert_type = session.query(CertificateType).filter_by(name=type_name).first()
    
    if cert_type and cert_type.folder_path:
        root_dir = cert_type.folder_path
    else:
        root_dir = os.path.join(BASE_DIR, get_safe_name(type_name))
        
    company_dir = os.path.join(root_dir, get_safe_name(comp_name))
    property_dir = os.path.join(company_dir, get_safe_name(prop_address))
    
    if flat_name == "General":
        folder_path = property_dir
        flat_str = ""
    else:
        flat_safe = get_safe_name(flat_name)
        folder_path = os.path.join(property_dir, flat_safe)
        flat_str = flat_safe + " - "

    os.makedirs(folder_path, exist_ok=True)
    
    date_str = expiry_date.strftime("%d%m%y") if expiry_date else "NoExpiry"
    
    # Construct filename e.g. "GSC Flat 1 - 72 TCR 131223.pdf"
    filename = f"{get_safe_name(type_name)} {flat_str}{get_safe_name(prop_address)} {date_str}.pdf"
    
    destination_path = os.path.join(folder_path, filename)
    shutil.copy2(temp_pdf_path, destination_path)
    
    return destination_path
