import json
import os
import sys
from PySide6.QtWidgets import QMessageBox, QFileDialog

def get_app_data_dir():
    app_data = os.getenv('LOCALAPPDATA') or os.path.expanduser('~')
    folder = os.path.join(app_data, 'PCAS')
    os.makedirs(folder, exist_ok=True)
    return folder

CONFIG_FILE = os.path.join(get_app_data_dir(), 'config.json')

def get_base_dir():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            try:
                config = json.load(f)
                if 'BASE_DIR' in config and config['BASE_DIR']:
                    return config['BASE_DIR']
            except:
                pass
    return r"C:\Office Workfiles"

def ensure_configured(parent=None):
    if not os.path.exists(CONFIG_FILE):
        reply = QMessageBox.information(parent, "Setup Required", 
            "Welcome! To ensure all computers in your office share the same data, "
            "please select your main 'Office Workfiles' network folder where the database and certificates will be stored.",
            QMessageBox.Ok)
        
        folder = QFileDialog.getExistingDirectory(parent, "Select Office Workfiles Directory")
        if not folder:
            folder = r"C:\Office Workfiles"
            QMessageBox.warning(parent, "Default Chosen", f"No folder selected. Defaulting to {folder}")
        
        os.makedirs(folder, exist_ok=True)
            
        with open(CONFIG_FILE, 'w') as f:
            json.dump({'BASE_DIR': folder}, f)
        
        return True # newly configured
    return False
