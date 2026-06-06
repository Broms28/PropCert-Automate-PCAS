import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
import config_manager

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(__file__)
    return os.path.join(base_path, relative_path)

def main():
    try:
        os.chdir(sys._MEIPASS)
    except Exception:
        pass

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(resource_path('icon.ico')))
    
    # Ensure network folder is configured before DB load
    config_manager.ensure_configured()
    
    # Initialize database
    from db import init_db
    from ui.main_window import MainWindow
    
    init_db()

    # Load modern stylesheet
    style_path = resource_path('style.qss')
    if os.path.exists(style_path):
        with open(style_path, 'r') as f:
            app.setStyleSheet(f.read())
    else:
        app.setStyleSheet("* { font-size: 14pt; }")
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
