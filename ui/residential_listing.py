from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox, 
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QLabel, QDialog, QLineEdit, QDateEdit, QFormLayout, QTextEdit
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor, QFontMetrics
import qtawesome as qta
from db import get_session, Company, Property, Flat, ResidentialTenant
from utils import tenant_sort_key, property_sort_key, flat_sort_key
from ui.move_out_dialog import MoveOutDialog

class AddResTenantDialog(QDialog):
    def __init__(self, session, initial_comp_id=None, initial_prop_id=None, parent=None, edit_tenant=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Residential Tenant" if edit_tenant else "Add Residential Tenant")
        self.resize(400, 450)
        self.session = session
        self.edit_tenant = edit_tenant
        
        layout = QFormLayout(self)
        
        # Property Selection
        self.prop_combo = QComboBox()
        self.flat_combo = QComboBox()
        
        query = self.session.query(Property).filter_by(property_type="Residential")
        if initial_comp_id:
            query = query.filter_by(company_id=initial_comp_id)
        self.properties = query.order_by(Property.address).all()
        
        for p in self.properties:
            self.prop_combo.addItem(p.address, userData=p.id)
            
        self.prop_combo.currentIndexChanged.connect(self.update_flats)
        layout.addRow("Property:", self.prop_combo)
        layout.addRow("Flat / Unit:", self.flat_combo)
        
        # Details
        self.name_in = QLineEdit()
        self.phone_in = QLineEdit()
        self.email_in = QLineEdit()
        self.start_in = QDateEdit()
        self.start_in.setCalendarPopup(True)
        self.start_in.setDate(QDate.currentDate())
        self.rent_in = QLineEdit()
        self.notes_in = QTextEdit()
        self.notes_in.setMaximumHeight(80)
        
        layout.addRow("Tenant Name (*):", self.name_in)
        layout.addRow("Phone:", self.phone_in)
        layout.addRow("Email:", self.email_in)
        layout.addRow("Tenancy Start (*):", self.start_in)
        layout.addRow("Monthly Rent:", self.rent_in)
        layout.addRow("Notes:", self.notes_in)
        
        btn_layout = QHBoxLayout()
        self.btn_ok = QPushButton("Save Changes" if edit_tenant else "Add Tenant")
        self.btn_ok.clicked.connect(self.accept)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_ok)
        layout.addRow("", btn_layout)
        
        if initial_prop_id:
            idx = self.prop_combo.findData(initial_prop_id)
            if idx >= 0:
                self.prop_combo.setCurrentIndex(idx)
        self.update_flats()
        
        if self.edit_tenant:
            # Set flat
            idx = self.flat_combo.findData(self.edit_tenant.flat_id)
            if idx >= 0:
                self.flat_combo.setCurrentIndex(idx)
                
            self.name_in.setText(self.edit_tenant.name)
            self.phone_in.setText(self.edit_tenant.phone or "")
            self.email_in.setText(self.edit_tenant.email or "")
            self.start_in.setDate(self.edit_tenant.tenancy_start_date)
            self.rent_in.setText(self.edit_tenant.monthly_rent or "")
            self.notes_in.setPlainText(self.edit_tenant.notes or "")

    def update_flats(self):
        self.flat_combo.clear()
        prop_id = self.prop_combo.currentData()
        if not prop_id: return
        flats = self.session.query(Flat).filter(Flat.property_id == prop_id).all()
        for f in sorted(flats, key=flat_sort_key):
            self.flat_combo.addItem(f.name, userData=f.id)

    def get_data(self):
        rent_val = self.rent_in.text().replace("£", "").strip()
        if rent_val:
            rent_val = f"£{rent_val}"
            
        return {
            "flat_id": self.flat_combo.currentData(),
            "name": self.name_in.text().strip(),
            "phone": self.phone_in.text().strip(),
            "email": self.email_in.text().strip(),
            "tenancy_start_date": self.start_in.date().toPython(),
            "monthly_rent": rent_val,
            "notes": self.notes_in.toPlainText().strip()
        }

class ResidentialListingWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.session = get_session()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Top Bar
        top_bar = QHBoxLayout()
        
        top_bar.addWidget(QLabel("Company:"))
        self.comp_combo = QComboBox()
        self.comp_combo.setMinimumWidth(150)
        self.comp_combo.currentIndexChanged.connect(self.on_comp_changed)
        top_bar.addWidget(self.comp_combo)
        
        top_bar.addWidget(QLabel("Property:"))
        self.prop_combo = QComboBox()
        self.prop_combo.setMinimumWidth(200)
        self.prop_combo.currentIndexChanged.connect(self.load_data)
        top_bar.addWidget(self.prop_combo)
        
        self.btn_add = QPushButton(" Add Tenant")
        self.btn_add.setIcon(qta.icon('fa5s.user-plus', color='white'))
        self.btn_add.setStyleSheet("background-color: #2563eb; color: white;")
        self.btn_add.clicked.connect(self.add_tenant)
        top_bar.addWidget(self.btn_add)
        
        self.btn_refresh = QPushButton(" Refresh")
        self.btn_refresh.setIcon(qta.icon('fa5s.sync', color='black'))
        self.btn_refresh.clicked.connect(self.refresh_filters)
        top_bar.addWidget(self.btn_refresh)
        
        top_bar.addStretch()
        layout.addLayout(top_bar)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["Company", "Property Address", "Flat", "Tenant Name", "Email", "Notes", "Actions"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        # Fix actions column width
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Fixed)
        self.table.setColumnWidth(6, 120)
        self.table.setWordWrap(True)
        self.table.itemChanged.connect(self.on_item_changed)
        
        layout.addWidget(self.table)
        
    def refresh_filters(self):
        self.comp_combo.blockSignals(True)
        self.comp_combo.clear()
        self.comp_combo.addItem("All Companies", userData=None)
        companies = self.session.query(Company).order_by(Company.name).all()
        for c in companies:
            self.comp_combo.addItem(c.name, userData=c.id)
        self.comp_combo.blockSignals(False)
        self.on_comp_changed()

    def on_comp_changed(self):
        self.prop_combo.blockSignals(True)
        self.prop_combo.clear()
        self.prop_combo.addItem("All Properties", userData=None)
        
        comp_id = self.comp_combo.currentData()
        properties = self.session.query(Property).filter(Property.property_type == "Residential")
        if comp_id:
            properties = properties.filter(Property.company_id == comp_id)
            
        for p in sorted(properties.all(), key=property_sort_key):
            self.prop_combo.addItem(p.address, userData=p.id)
            
        self.prop_combo.blockSignals(False)
        self.load_data()

    def load_data(self):
        self.table.blockSignals(True)
        self.table.setRowCount(0)
        
        comp_id = self.comp_combo.currentData()
        prop_id = self.prop_combo.currentData()
        
        query = self.session.query(ResidentialTenant).join(Flat).join(Property)
        if comp_id:
            query = query.filter(Property.company_id == comp_id)
        if prop_id:
            query = query.filter(Property.id == prop_id)
            
        # Ensure we only show residential properties just in case
        query = query.filter(Property.property_type == "Residential")
        query = query.filter(ResidentialTenant.is_past == 0)
        
        tenants = query.all()
        tenants.sort(key=tenant_sort_key)
        
        self.table.setRowCount(len(tenants))
        for row, t in enumerate(tenants):
            # Company
            i_comp = QTableWidgetItem(t.flat.property.company.name)
            i_comp.setFlags(i_comp.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 0, i_comp)
            
            # Property
            i_prop = QTableWidgetItem(t.flat.property.address)
            i_prop.setFlags(i_prop.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 1, i_prop)
            
            # Flat
            i_flat = QTableWidgetItem(t.flat.name)
            i_flat.setFlags(i_flat.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 2, i_flat)
            
            # Name
            i_name = QTableWidgetItem(t.name)
            i_name.setFlags(i_name.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 3, i_name)
            
            # Email
            i_email = QTableWidgetItem(t.email or "")
            i_email.setFlags(i_email.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 4, i_email)
            
            # Notes (Editable)
            i_notes = QTableWidgetItem(t.notes or "")
            i_notes.setData(32, t.id) # Store ID for editing
            i_notes.setBackground(QColor("#fef3c7")) # Slight yellow background to indicate editable
            self.table.setItem(row, 5, i_notes)
            
            # Actions
            widget_actions = QWidget()
            layout_actions = QHBoxLayout(widget_actions)
            layout_actions.setContentsMargins(5, 2, 5, 2)
            layout_actions.setSpacing(5)

            btn_edit = QPushButton()
            btn_edit.setIcon(qta.icon('fa5s.pen', color='white'))
            btn_edit.setStyleSheet("background-color: #3b82f6; padding: 5px;")
            btn_edit.clicked.connect(lambda checked=False, tid=t.id: self.edit_tenant(tid))
            
            btn_moveout = QPushButton()
            btn_moveout.setIcon(qta.icon('fa5s.door-open', color='white'))
            btn_moveout.setStyleSheet("background-color: #f59e0b; padding: 5px;") # Orange
            btn_moveout.setToolTip("Move Out Tenant")
            btn_moveout.clicked.connect(lambda checked=False, tid=t.id: self.move_out_tenant(tid))

            btn_delete = QPushButton()
            btn_delete.setIcon(qta.icon('fa5s.trash', color='white'))
            btn_delete.setStyleSheet("background-color: #ef4444; padding: 5px;")
            btn_delete.setToolTip("Permanently Delete Tenant")
            btn_delete.clicked.connect(lambda checked=False, tid=t.id: self.delete_tenant(tid))

            layout_actions.addWidget(btn_edit)
            layout_actions.addWidget(btn_moveout)
            layout_actions.addWidget(btn_delete)
            self.table.setCellWidget(row, 6, widget_actions)

        self.table.resizeRowsToContents()
        self.table.blockSignals(False)

    def on_item_changed(self, item):
        # Column 5 is Notes
        if item.column() == 5:
            tid = item.data(32)
            new_notes = item.text()
            tenant = self.session.query(ResidentialTenant).get(tid)
            if tenant:
                tenant.notes = new_notes
                self.session.commit()

    def add_tenant(self):
        c_id = self.comp_combo.currentData()
        p_id = self.prop_combo.currentData()
        dialog = AddResTenantDialog(self.session, c_id, p_id, self)
        if dialog.exec():
            data = dialog.get_data()
            if not data['flat_id'] or not data['name']:
                QMessageBox.warning(self, "Error", "Property/Unit and Tenant Name are required!")
                return
                
            t = ResidentialTenant(**data)
            self.session.add(t)
            self.session.commit()
            self.load_data()

    def edit_tenant(self, tid):
        t = self.session.query(ResidentialTenant).get(tid)
        if not t: return
        dialog = AddResTenantDialog(self.session, None, t.flat.property_id, self, edit_tenant=t)
        if dialog.exec():
            data = dialog.get_data()
            if not data['flat_id'] or not data['name']:
                QMessageBox.warning(self, "Error", "Property/Unit and Tenant Name are required!")
                return
            t.flat_id = data['flat_id']
            t.name = data['name']
            t.phone = data['phone']
            t.email = data['email']
            t.tenancy_start_date = data['tenancy_start_date']
            t.monthly_rent = data['monthly_rent']
            t.notes = data['notes']
            self.session.commit()
            self.load_data()

    def delete_tenant(self, tenant_id):
        reply = QMessageBox.question(self, 'Confirm Deletion', 
                                     "Are you sure you want to permanently delete this tenant?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                t = self.session.query(ResidentialTenant).get(tenant_id)
                if t:
                    self.session.delete(t)
                    self.session.commit()
                    self.load_data()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not delete tenant:\n{e}")
                self.session.rollback()

    def move_out_tenant(self, tenant_id):
        try:
            t = self.session.query(ResidentialTenant).get(tenant_id)
            if not t: return
            
            dialog = MoveOutDialog(t.name, self)
            if dialog.exec():
                t.is_past = 1
                t.move_out_date = dialog.get_date()
                self.session.commit()
                self.load_data()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not move out tenant:\n{e}")
            self.session.rollback()
