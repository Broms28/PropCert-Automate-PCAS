from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QComboBox, QDateEdit, 
    QPushButton, QFileDialog, QMessageBox, QHBoxLayout, QLabel, QCheckBox
)
from PySide6.QtCore import QDate, Qt
from db import get_session, Company, Property, Flat, Certificate, CertificateType
from file_manager import save_certificate
import datetime

class DropLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setText("\nDrop PDF Here\n\n(Or click 'Browse' below)\n")
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #9ca3af;
                border-radius: 8px;
                background-color: #f9fafb;
                color: #6b7280;
                font-size: 14pt;
                padding: 20px;
            }
        """)
        self.parent_dialog = parent

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and urls[0].isLocalFile() and urls[0].toLocalFile().lower().endswith('.pdf'):
                event.acceptProposedAction()
                self.setStyleSheet("""
                    QLabel {
                        border: 2px dashed #3b82f6;
                        border-radius: 8px;
                        background-color: #eff6ff;
                        color: #1d4ed8;
                        font-size: 14pt;
                        padding: 20px;
                    }
                """)
                return
        event.ignore()

    def dragLeaveEvent(self, event):
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #9ca3af;
                border-radius: 8px;
                background-color: #f9fafb;
                color: #6b7280;
                font-size: 14pt;
                padding: 20px;
            }
        """)

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            self.parent_dialog.set_selected_file(file_path)

class UploadDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Upload Certificate")
        self.setMinimumWidth(400)
        self.session = get_session()
        self.selected_file_path = None
        self.setup_ui()
        self.load_companies()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        # Company
        self.cb_company = QComboBox()
        self.cb_company.currentIndexChanged.connect(self.on_company_changed)
        form.addRow("Company:", self.cb_company)

        # Property
        self.cb_property = QComboBox()
        self.cb_property.currentIndexChanged.connect(self.on_property_changed)
        form.addRow("Property:", self.cb_property)

        # Flat
        self.cb_flat = QComboBox()
        self.chk_general = QCheckBox("General")
        self.chk_general.setToolTip("Select if this certificate applies to the entire property rather than a specific flat.")
        self.chk_general.stateChanged.connect(self.on_general_changed)
        
        flat_layout = QHBoxLayout()
        flat_layout.addWidget(self.cb_flat)
        flat_layout.addWidget(self.chk_general)
        form.addRow("Flat:", flat_layout)

        # Type
        self.cb_type = QComboBox()
        form.addRow("Certificate Type:", self.cb_type)

        # Expiry Date
        self.date_expiry = QDateEdit()
        self.date_expiry.setCalendarPopup(True)
        self.date_expiry.setDate(QDate.currentDate())
        self.date_expiry.setDisplayFormat("dd/MM/yyyy")
        
        self.chk_no_expiry = QCheckBox("No Expiry Date")
        self.chk_no_expiry.stateChanged.connect(self.on_no_expiry_changed)

        date_layout = QHBoxLayout()
        date_layout.addWidget(self.date_expiry)
        date_layout.addWidget(self.chk_no_expiry)
        form.addRow("Expiry Date:", date_layout)

        layout.addLayout(form)

        import qtawesome as qta
        
        # File Selection Drop Zone
        self.drop_label = DropLabel(self)
        layout.addWidget(self.drop_label)

        # File Selection Browse Button (fallback)
        self.btn_browse = QPushButton(" Browse PDF...")
        self.btn_browse.setIcon(qta.icon('fa5s.folder-open', color='white'))
        self.btn_browse.clicked.connect(self.browse_file)
        layout.addWidget(self.btn_browse)

        layout.addSpacing(10)

        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_upload = QPushButton(" Upload")
        self.btn_upload.setIcon(qta.icon('fa5s.check', color='white'))
        self.btn_cancel = QPushButton(" Cancel")
        self.btn_cancel.setIcon(qta.icon('fa5s.times', color='white'))
        self.btn_cancel.setStyleSheet("background-color: #6b7280;") # Gray cancel button
        self.btn_upload.clicked.connect(self.upload_certificate)
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_upload)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

    def on_no_expiry_changed(self, state):
        if state == 2: # Qt.Checked is 2 in PySide6
            self.date_expiry.setEnabled(False)
        else:
            self.date_expiry.setEnabled(True)

    def on_general_changed(self, state):
        if state == 2:
            self.cb_flat.setEnabled(False)
        else:
            self.cb_flat.setEnabled(True)

    def load_companies(self):
        self.cb_company.clear()
        companies = self.session.query(Company).order_by(Company.name).all()
        for c in companies:
            self.cb_company.addItem(c.name, c.id)
            
        self.cb_type.clear()
        types = self.session.query(CertificateType).order_by(CertificateType.name).all()
        for ct in types:
            self.cb_type.addItem(ct.name)

    def on_company_changed(self):
        self.cb_property.clear()
        comp_id = self.cb_company.currentData()
        if comp_id is None: return
        properties = self.session.query(Property).filter(Property.company_id == comp_id).order_by(Property.address).all()
        for p in properties:
            self.cb_property.addItem(p.address, p.id)

    def on_property_changed(self):
        import re
        def natural_sort_key(flat):
            return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', flat.name)]

        self.cb_flat.clear()
        prop_id = self.cb_property.currentData()
        if prop_id is None: return
        flats = self.session.query(Flat).filter(Flat.property_id == prop_id).all()
        flats.sort(key=natural_sort_key)
        for f in flats:
            self.cb_flat.addItem(f.name, f.id)

    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select PDF File", "", "PDF Files (*.pdf)")
        if file_path:
            self.set_selected_file(file_path)

    def set_selected_file(self, file_path):
        if file_path.lower().endswith('.pdf'):
            self.selected_file_path = file_path
            filename = file_path.split("/")[-1] if "/" in file_path else file_path.split("\\")[-1]
            self.drop_label.setText(f"\nSelected PDF:\n{filename}\n")
            self.drop_label.setStyleSheet("""
                QLabel {
                    border: 2px solid #10b981;
                    border-radius: 8px;
                    background-color: #ecfdf5;
                    color: #047857;
                    font-size: 14pt;
                    font-weight: bold;
                    padding: 20px;
                }
            """)
        else:
            QMessageBox.warning(self, "Invalid File", "Please select a PDF file.")

    def upload_certificate(self):
        prop_id = self.cb_property.currentData()
        if prop_id is None:
            QMessageBox.warning(self, "Error", "Please select a Property.")
            return

        if self.chk_general.isChecked():
            # Find or create a "General" flat for this property
            general_flat = self.session.query(Flat).filter_by(property_id=prop_id, name="General").first()
            if not general_flat:
                general_flat = Flat(property_id=prop_id, name="General")
                self.session.add(general_flat)
                self.session.commit() # Commit to get the ID
            flat_id = general_flat.id
            flat_name = "General"
        else:
            flat_id = self.cb_flat.currentData()
            if flat_id is None:
                QMessageBox.warning(self, "Error", "Please select a Flat.")
                return
            flat_name = self.cb_flat.currentText()

        if not self.selected_file_path:
            QMessageBox.warning(self, "Error", "Please select a PDF file by dragging it or browsing.")
            return

        cert_type = self.cb_type.currentText()
        
        if self.chk_no_expiry.isChecked():
            expiry_date = None
        else:
            expiry_date = self.date_expiry.date().toPython()

        comp_name = self.cb_company.currentText()
        prop_address = self.cb_property.currentText()

        try:
            # Copy file to appropriate directory
            dest_path = save_certificate(
                self.selected_file_path, 
                comp_name, 
                prop_address, 
                flat_name, 
                cert_type, 
                expiry_date
            )

            # Check if a certificate of this type already exists for this flat
            existing_cert = self.session.query(Certificate).filter_by(flat_id=flat_id, cert_type=cert_type).first()
            if existing_cert:
                # Update existing record (old PDF remains in the folder automatically)
                existing_cert.expiry_date = expiry_date
                existing_cert.file_path = dest_path
            else:
                # Create a new record
                cert = Certificate(
                    flat_id=flat_id,
                    cert_type=cert_type,
                    expiry_date=expiry_date,
                    file_path=dest_path
                )
                self.session.add(cert)
                
            self.session.commit()

            QMessageBox.information(self, "Success", f"Certificate uploaded and saved to:\n{dest_path}")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to upload certificate:\n{e}")
            self.session.rollback()
