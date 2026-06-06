import sys
import os
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from db import init_db

def main():
    # Initialize database
    init_db()

    app = QApplication(sys.argv)
    
    # Load modern stylesheet
    style_path = os.path.join(os.path.dirname(__file__), 'style.qss')
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
