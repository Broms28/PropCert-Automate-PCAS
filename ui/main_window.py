from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QTableWidget, QTableWidgetItem, QTabWidget, QFileDialog, QMessageBox, QHeaderView, QInputDialog, QToolButton, QMenu
)
from PySide6.QtGui import QColor, QDesktopServices
from PySide6.QtCore import Qt, QUrl, QTimer
from db import engine, get_session, Certificate, CertificateType
import pandas as pd
import datetime
import subprocess
from ui.upload_dialog import UploadDialog
from ui.manage_properties import ManagePropertiesWidget
from ui.responsive_button import ResponsiveButton
from excel_exporter import export_to_excel
import os

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PCAS - Property Certificate Automation System")
        self.resize(1000, 700)
        self.session = get_session()
        # Dictionary to store tables for each cert type
        self.tables = {}
        self.setup_ui()
        
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.load_data)
        self.refresh_timer.start(600000) # 10 minutes

    def setup_ui(self):
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Dashboard Tab
        self.dashboard_tab = QWidget()
        self.setup_dashboard_tab()
        self.tabs.addTab(self.dashboard_tab, "Dashboard")

        # Manage Properties Tab
        self.manage_props_tab = ManagePropertiesWidget()
        self.tabs.addTab(self.manage_props_tab, "Manage Properties")
        
        self.tabs.currentChanged.connect(self.on_tab_changed)

    def setup_dashboard_tab(self):
        layout = QVBoxLayout(self.dashboard_tab)

        import qtawesome as qta
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_upload = ResponsiveButton(" Upload Certificate", icon=qta.icon('fa5s.file-upload', color='white'))
        self.btn_upload.clicked.connect(self.open_upload_dialog)
        
        self.btn_export = ResponsiveButton(" Export to Excel", icon=qta.icon('fa5s.file-excel', color='white'))
        self.btn_export.clicked.connect(self.export_data)

        self.btn_refresh = ResponsiveButton(" Refresh", icon=qta.icon('fa5s.sync', color='white'))
        self.btn_refresh.clicked.connect(self.load_data)

        btn_layout.addWidget(self.btn_upload)
        btn_layout.addWidget(self.btn_export)
        btn_layout.addWidget(self.btn_refresh)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Certificate Tabs
        self.cert_tabs = QTabWidget()
        layout.addWidget(self.cert_tabs)

        # Add '+' button to corner of cert tabs
        self.btn_add_type = QToolButton()
        self.btn_add_type.setIcon(qta.icon('fa5s.plus', color='#1d4ed8'))
        self.btn_add_type.setToolTip("Add new certificate type")
        self.btn_add_type.setStyleSheet("QToolButton { border: none; padding: 5px; background: transparent; } QToolButton:hover { background: #d1d5db; border-radius: 4px; }")
        self.btn_add_type.clicked.connect(self.add_certificate_type)
        
        corner_widget = QWidget()
        corner_layout = QHBoxLayout(corner_widget)
        corner_layout.setContentsMargins(0, 4, 10, 0)
        corner_layout.addWidget(self.btn_add_type)
        
        self.cert_tabs.setCornerWidget(corner_widget, Qt.TopRightCorner)

        # Context menu for tabs
        self.cert_tabs.tabBar().setContextMenuPolicy(Qt.CustomContextMenu)
        self.cert_tabs.tabBar().customContextMenuRequested.connect(self.show_tab_context_menu)

        self.refresh_cert_tabs()

    def refresh_cert_tabs(self):
        # Save current tab index if possible
        current_idx = self.cert_tabs.currentIndex()
        
        self.cert_tabs.clear()
        self.tables.clear()

        types = self.session.query(CertificateType).order_by(CertificateType.name).all()
        for ct in types:
            table = self.create_table()
            self.tables[ct.name] = table
            self.cert_tabs.addTab(table, ct.name)

        if current_idx >= 0 and current_idx < self.cert_tabs.count():
            self.cert_tabs.setCurrentIndex(current_idx)

        self.load_data()

    def add_certificate_type(self):
        name, ok = QInputDialog.getText(self, "Add Certificate Type", "Certificate Name (e.g. Fire Alarm):")
        if ok and name:
            name = name.strip()
            if not name: return
            
            existing = self.session.query(CertificateType).filter_by(name=name).first()
            if existing:
                QMessageBox.warning(self, "Exists", "This certificate type already exists.")
                return
            
            new_type = CertificateType(name=name)
            self.session.add(new_type)
            self.session.commit()
            
            self.refresh_cert_tabs()

    def show_tab_context_menu(self, position):
        import qtawesome as qta
        tab_index = self.cert_tabs.tabBar().tabAt(position)
        if tab_index < 0:
            return
        
        type_name = self.cert_tabs.tabText(tab_index)
        
        menu = QMenu()
        action_edit = menu.addAction(qta.icon('fa5s.edit'), "Edit Certificate Name")
        action_folder = menu.addAction(qta.icon('fa5s.folder-open'), "Set Folder Location")
        menu.addSeparator()
        action_delete = menu.addAction(qta.icon('fa5s.trash'), "Delete Certificate Type")
        
        action = menu.exec(self.cert_tabs.tabBar().mapToGlobal(position))
        
        if action == action_edit:
            self.edit_certificate_type(type_name)
        elif action == action_folder:
            self.set_type_folder(type_name)
        elif action == action_delete:
            self.delete_certificate_type(type_name)

    def edit_certificate_type(self, old_name):
        new_name, ok = QInputDialog.getText(self, "Edit Certificate Type", "New Name:", text=old_name)
        if ok and new_name and new_name.strip() != old_name:
            new_name = new_name.strip()
            cert_type = self.session.query(CertificateType).filter_by(name=old_name).first()
            if cert_type:
                cert_type.name = new_name
                # Also update all certificates that map to this string
                certs = self.session.query(Certificate).filter_by(cert_type=old_name).all()
                for c in certs:
                    c.cert_type = new_name
                self.session.commit()
                self.refresh_cert_tabs()

    def set_type_folder(self, type_name):
        cert_type = self.session.query(CertificateType).filter_by(name=type_name).first()
        if not cert_type: return
        
        folder = QFileDialog.getExistingDirectory(self, f"Select Folder for {type_name}")
        if folder:
            cert_type.folder_path = folder
            self.session.commit()
            QMessageBox.information(self, "Success", f"Folder for '{type_name}' set to:\n{folder}")

    def delete_certificate_type(self, type_name):
        reply = QMessageBox.question(self, 'Confirm Deletion', 
                                     f"Are you sure you want to delete the '{type_name}' certificate tab?\nThis will hide all associated certificates.",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            cert_type = self.session.query(CertificateType).filter_by(name=type_name).first()
            if cert_type:
                self.session.delete(cert_type)
                self.session.commit()
                self.refresh_cert_tabs()

    def create_table(self):
        from PySide6.QtWidgets import QAbstractItemView
        table = QTableWidget()
        table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["Property Address", "Flat", "Expiry date", "File", ""])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        # Fix the delete column width
        table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        table.setColumnWidth(4, 60)
        return table

    def on_tab_changed(self, index):
        if index == 0:
            self.load_data()
        elif index == 1:
            self.manage_props_tab.load_companies()

    def populate_table(self, table, df):
        import qtawesome as qta
        table.setRowCount(df.shape[0])
        today = datetime.date.today()
        warning_date = today + datetime.timedelta(days=30)

        for row_idx, row in df.reset_index(drop=True).iterrows():
            cert_id = row['CertID']
            prop = str(row['Property'])
            flat = str(row['Flat'])
            expiry_val = row['Expiry']
            file_path = str(row['Path'])

            # 0: Property
            item_prop = QTableWidgetItem(prop)
            item_prop.setFlags(item_prop.flags() & ~Qt.ItemIsEditable)
            table.setItem(row_idx, 0, item_prop)

            # 1: Flat
            item_flat = QTableWidgetItem(flat)
            item_flat.setFlags(item_flat.flags() & ~Qt.ItemIsEditable)
            table.setItem(row_idx, 1, item_flat)

            # 2: Expiry Date
            expiry_date_obj = None
            if pd.isna(expiry_val) or not expiry_val:
                display_date = "No Expiry"
            else:
                expiry_str = str(expiry_val)
                try:
                    expiry_date_obj = datetime.datetime.strptime(expiry_str, "%Y-%m-%d").date()
                    display_date = expiry_date_obj.strftime("%d/%m/%Y")
                except Exception:
                    display_date = expiry_str
                
            item_expiry = QTableWidgetItem(display_date)
            item_expiry.setFlags(item_expiry.flags() & ~Qt.ItemIsEditable)

            # Highlight logic
            if expiry_date_obj:
                if expiry_date_obj < today:
                    item_expiry.setBackground(QColor(255, 100, 100))
                    item_expiry.setForeground(QColor("white"))
                elif expiry_date_obj <= warning_date:
                    item_expiry.setBackground(QColor(255, 255, 150))
                    item_expiry.setForeground(QColor("black"))
            
            table.setItem(row_idx, 2, item_expiry)

            # 3: File Buttons
            widget_file = QWidget()
            layout_file = QHBoxLayout(widget_file)
            layout_file.setContentsMargins(5, 2, 5, 2)
            layout_file.setSpacing(10)

            btn_open = QPushButton(" Open PDF")
            btn_open.setIcon(qta.icon('fa5s.external-link-alt', color='white'))
            btn_open.clicked.connect(lambda checked=False, p=file_path: QDesktopServices.openUrl(QUrl.fromLocalFile(p)))

            btn_folder = QPushButton(" Show in Folder")
            btn_folder.setIcon(qta.icon('fa5s.folder-open', color='white'))
            btn_folder.clicked.connect(lambda checked=False, p=file_path: subprocess.Popen(f'explorer /select,"{os.path.normpath(p)}"'))

            layout_file.addWidget(btn_open)
            layout_file.addWidget(btn_folder)
            layout_file.addStretch()
            table.setCellWidget(row_idx, 3, widget_file)

            # 4: Delete Button
            btn_delete = QPushButton()
            btn_delete.setIcon(qta.icon('fa5s.trash', color='white'))
            btn_delete.setStyleSheet("background-color: #ef4444;") # Red delete button
            btn_delete.clicked.connect(lambda checked=False, cid=cert_id: self.delete_certificate(cid))
            
            widget_del = QWidget()
            layout_del = QHBoxLayout(widget_del)
            layout_del.setContentsMargins(5, 2, 5, 2)
            layout_del.addWidget(btn_delete)
            table.setCellWidget(row_idx, 4, widget_del)

            table.setRowHeight(row_idx, 65)

    def delete_certificate(self, cert_id):
        reply = QMessageBox.question(self, 'Confirm Deletion', 
                                     "Are you sure you want to delete this certificate record? The PDF file will remain in its folder on your computer.",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                cert = self.session.query(Certificate).get(cert_id)
                if cert:
                    self.session.delete(cert)
                    self.session.commit()
                    self.load_data()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not delete certificate:\n{e}")
                self.session.rollback()

    def load_data(self):
        query = """
        SELECT 
            cert.id AS CertID,
            c.name AS Company,
            p.address AS Property,
            f.name AS Flat,
            cert.cert_type AS Type,
            cert.expiry_date AS Expiry,
            cert.file_path AS Path
        FROM certificates cert
        JOIN flats f ON cert.flat_id = f.id
        JOIN properties p ON f.property_id = p.id
        JOIN companies c ON p.company_id = c.id
        ORDER BY cert.expiry_date ASC
        """
        try:
            df = pd.read_sql_query(query, engine)
            
            for type_name, table_widget in self.tables.items():
                df_type = df[df['Type'] == type_name]
                self.populate_table(table_widget, df_type)

        except Exception as e:
            print(f"Error loading data: {e}")

    def open_upload_dialog(self):
        dialog = UploadDialog(self)
        if dialog.exec():
            # If user added a new type somehow or just updated certs
            self.refresh_cert_tabs()

    def export_data(self):
        filepath, _ = QFileDialog.getSaveFileName(self, "Export Excel", "", "Excel Files (*.xlsx)")
        if filepath:
            try:
                export_to_excel(filepath)
                QMessageBox.information(self, "Success", f"Data exported to {filepath}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export data: {e}")
