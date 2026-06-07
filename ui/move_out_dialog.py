from PySide6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QDateEdit, QPushButton, QHBoxLayout
from PySide6.QtCore import QDate
import qtawesome as qta

class MoveOutDialog(QDialog):
    def __init__(self, tenant_name, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Move Out: {tenant_name}")
        self.setMinimumWidth(300)
        
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setDisplayFormat("dd/MM/yyyy")
        self.date_edit.setStyleSheet("padding: 5px; font-size: 14pt;")
        
        form.addRow("Move-Out Date:", self.date_edit)
        layout.addLayout(form)
        
        btn_layout = QHBoxLayout()
        self.btn_confirm = QPushButton(" Confirm Move Out")
        self.btn_confirm.setIcon(qta.icon('fa5s.door-open', color='white'))
        self.btn_confirm.setStyleSheet("background-color: #f59e0b;") # Orange for move out
        
        self.btn_cancel = QPushButton(" Cancel")
        self.btn_cancel.setIcon(qta.icon('fa5s.times', color='white'))
        self.btn_cancel.setStyleSheet("background-color: #6b7280;")
        
        self.btn_confirm.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.btn_confirm)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

    def get_date(self):
        return self.date_edit.date().toPython()
