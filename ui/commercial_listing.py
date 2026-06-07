from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox, 
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QLabel, QDialog, QLineEdit, QDateEdit, QFormLayout, QCheckBox, QTextEdit
)
import datetime
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor, QFontMetrics
import qtawesome as qta
from db import get_session, Company, Property, Flat, CommercialTenant
from utils import tenant_sort_key, property_sort_key, flat_sort_key
from ui.move_out_dialog import MoveOutDialog

class AddComTenantDialog(QDialog):
    def __init__(self, session, initial_comp_id=None, initial_prop_id=None, parent=None, edit_tenant=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Commercial Tenant" if edit_tenant else "Add Commercial Tenant")
        self.resize(450, 550)
        self.session = session
        self.edit_tenant = edit_tenant
        
        layout = QFormLayout(self)
        
        # Property Selection
        self.prop_combo = QComboBox()
        self.flat_combo = QComboBox()
        
        query = self.session.query(Property).filter_by(property_type="Commercial")
        if initial_comp_id:
            query = query.filter_by(company_id=initial_comp_id)
        self.properties = query.order_by(Property.address).all()
        
        for p in self.properties:
            self.prop_combo.addItem(p.address, userData=p.id)
            
        self.prop_combo.currentIndexChanged.connect(self.update_flats)
        layout.addRow("Property (*):", self.prop_combo)
        layout.addRow("Unit (Optional):", self.flat_combo)
        
        # Details
        self.company_in = QLineEdit()
        self.contact_in = QLineEdit()
        self.phone_in = QLineEdit()
        self.email_in = QLineEdit()
        
        self.start_in = QDateEdit()
        self.start_in.setCalendarPopup(True)
        self.start_in.setDate(QDate.currentDate())
        
        self.has_end_cb = QCheckBox("Has End Date")
        self.has_end_cb.stateChanged.connect(self.toggle_end_date)
        self.end_in = QDateEdit()
        self.end_in.setCalendarPopup(True)
        self.end_in.setDate(QDate.currentDate().addYears(1))
        self.end_in.setEnabled(False)
        
        end_layout = QHBoxLayout()
        end_layout.addWidget(self.has_end_cb)
        end_layout.addWidget(self.end_in)
        
        self.rent_in = QLineEdit()
        
        self.has_review_cb = QCheckBox("Has Rent Review")
        self.has_review_cb.stateChanged.connect(self.toggle_review_date)
        self.review_in = QDateEdit()
        self.review_in.setCalendarPopup(True)
        self.review_in.setDate(QDate.currentDate().addYears(1))
        self.review_in.setEnabled(False)
        
        review_layout = QHBoxLayout()
        review_layout.addWidget(self.has_review_cb)
        review_layout.addWidget(self.review_in)
        
        self.notes_in = QTextEdit()
        self.notes_in.setMaximumHeight(80)
        
        layout.addRow("Tenant / Company (*):", self.company_in)
        layout.addRow("Contact Person (*):", self.contact_in)
        layout.addRow("Telephone:", self.phone_in)
        layout.addRow("Email:", self.email_in)
        layout.addRow("Lease Start (*):", self.start_in)
        layout.addRow("Lease End:", end_layout)
        layout.addRow("Initial Rent:", self.rent_in)
        layout.addRow("Rent Review:", review_layout)
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
            if self.edit_tenant.flat_id:
                idx = self.flat_combo.findData(self.edit_tenant.flat_id)
                if idx >= 0:
                    self.flat_combo.setCurrentIndex(idx)
            
            self.company_in.setText(self.edit_tenant.tenant_company)
            self.contact_in.setText(self.edit_tenant.contact)
            self.phone_in.setText(self.edit_tenant.telephone or "")
            self.email_in.setText(self.edit_tenant.email or "")
            self.start_in.setDate(self.edit_tenant.lease_start_date)
            if self.edit_tenant.lease_end_date:
                self.has_end_cb.setChecked(True)
                self.end_in.setDate(self.edit_tenant.lease_end_date)
            self.rent_in.setText(self.edit_tenant.initial_rent or "")
            if self.edit_tenant.rent_review:
                self.has_review_cb.setChecked(True)
                self.review_in.setDate(self.edit_tenant.rent_review)
            self.notes_in.setPlainText(self.edit_tenant.notes or "")

    def toggle_end_date(self, state):
        self.end_in.setEnabled(self.has_end_cb.isChecked())

    def toggle_review_date(self, state):
        self.review_in.setEnabled(self.has_review_cb.isChecked())

    def update_flats(self):
        self.flat_combo.clear()
        self.flat_combo.addItem("(Whole Property)", userData=None)
        prop_id = self.prop_combo.currentData()
        if not prop_id: return
        flats = self.session.query(Flat).filter(Flat.property_id == prop_id).all()
        for f in sorted(flats, key=flat_sort_key):
            self.flat_combo.addItem(f.name, userData=f.id)

    def get_data(self):
        end_date = self.end_in.date().toPython() if self.has_end_cb.isChecked() else None
        rev_date = self.review_in.date().toPython() if self.has_review_cb.isChecked() else None
        
        rent_val = self.rent_in.text().replace("£", "").strip()
        if rent_val:
            rent_val = f"£{rent_val}"
            
        return {
            "property_id": self.prop_combo.currentData(),
            "flat_id": self.flat_combo.currentData(),
            "tenant_company": self.company_in.text().strip(),
            "contact": self.contact_in.text().strip(),
            "telephone": self.phone_in.text().strip(),
            "email": self.email_in.text().strip(),
            "lease_start_date": self.start_in.date().toPython(),
            "lease_end_date": end_date,
            "initial_rent": rent_val,
            "rent_review": rev_date,
            "notes": self.notes_in.toPlainText().strip()
        }

class CommercialListingWidget(QWidget):
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
        self.btn_add.setIcon(qta.icon('fa5s.user-tie', color='white'))
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
        self.table.setColumnCount(12)
        self.table.setHorizontalHeaderLabels([
            "Property", "Unit", "Tenant/Company", "Contact", "Telephone", "Email", 
            "Lease Start", "Lease End", "Initial Rent", "Rent Review", "Notes (Edit)", "Actions"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(10, QHeaderView.Stretch)
        # Fix actions column width
        self.table.horizontalHeader().setSectionResizeMode(11, QHeaderView.Fixed)
        self.table.setColumnWidth(11, 120)
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
        properties = self.session.query(Property).filter(Property.property_type == "Commercial")
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
        
        query = self.session.query(CommercialTenant).join(Property).outerjoin(Flat)
        if comp_id:
            query = query.filter(Property.company_id == comp_id)
        if prop_id:
            query = query.filter(Property.id == prop_id)
            
        query = query.filter(Property.property_type == "Commercial")
        query = query.filter(CommercialTenant.is_past == 0)
        
        tenants = query.all()
        tenants.sort(key=tenant_sort_key)
        
        self.table.setRowCount(len(tenants))
        
        today = datetime.date.today()
        warning_date = today + datetime.timedelta(days=30)
        
        for row, t in enumerate(tenants):
            # Property
            i_prop = QTableWidgetItem(t.property.address)
            i_prop.setFlags(i_prop.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 0, i_prop)
            
            # Unit
            unit_name = t.flat.name if t.flat else "-"
            i_flat = QTableWidgetItem(unit_name)
            i_flat.setFlags(i_flat.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 1, i_flat)
            
            # Tenant/Company
            i_comp = QTableWidgetItem(t.tenant_company)
            i_comp.setFlags(i_comp.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 2, i_comp)

            # Contact
            i_con = QTableWidgetItem(t.contact)
            i_con.setFlags(i_con.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 3, i_con)
            
            # Phone
            i_phone = QTableWidgetItem(t.telephone or "")
            i_phone.setFlags(i_phone.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 4, i_phone)
            
            # Email
            i_email = QTableWidgetItem(t.email or "")
            i_email.setFlags(i_email.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 5, i_email)
            
            # Start Date
            start_str = t.lease_start_date.strftime("%d/%m/%Y") if t.lease_start_date else ""
            i_start = QTableWidgetItem(start_str)
            i_start.setFlags(i_start.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 6, i_start)

            # End Date
            end_str = t.lease_end_date.strftime("%d/%m/%Y") if t.lease_end_date else "-"
            i_end = QTableWidgetItem(end_str)
            i_end.setFlags(i_end.flags() & ~Qt.ItemIsEditable)
            if t.lease_end_date and t.lease_end_date <= warning_date:
                i_end.setForeground(QColor("#ef4444"))
                font = i_end.font()
                font.setBold(True)
                i_end.setFont(font)
            self.table.setItem(row, 7, i_end)
            
            # Rent
            i_rent = QTableWidgetItem(t.initial_rent or "")
            i_rent.setFlags(i_rent.flags() & ~Qt.ItemIsEditable)
            i_rent.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 8, i_rent)

            # Review
            rev_str = t.rent_review.strftime("%d/%m/%Y") if t.rent_review else "-"
            i_rev = QTableWidgetItem(rev_str)
            i_rev.setFlags(i_rev.flags() & ~Qt.ItemIsEditable)
            if t.rent_review and t.rent_review <= warning_date:
                i_rev.setForeground(QColor("#ef4444"))
                font = i_rev.font()
                font.setBold(True)
                i_rev.setFont(font)
            self.table.setItem(row, 9, i_rev)
            
            # Notes (Editable)
            i_notes = QTableWidgetItem(t.notes or "")
            i_notes.setData(32, t.id)
            i_notes.setBackground(QColor("#fef3c7"))
            self.table.setItem(row, 10, i_notes)
            
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
            btn_moveout.setStyleSheet("background-color: #f59e0b; padding: 5px;")
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
            self.table.setCellWidget(row, 11, widget_actions)

        self.table.resizeRowsToContents()
        self.table.blockSignals(False)

    def on_item_changed(self, item):
        if item.column() == 10:
            tid = item.data(32)
            new_notes = item.text()
            tenant = self.session.query(CommercialTenant).get(tid)
            if tenant:
                tenant.notes = new_notes
                self.session.commit()

    def add_tenant(self):
        c_id = self.comp_combo.currentData()
        p_id = self.prop_combo.currentData()
        dialog = AddComTenantDialog(self.session, c_id, p_id, self)
        if dialog.exec():
            data = dialog.get_data()
            if not data['property_id'] or not data['tenant_company'] or not data['contact']:
                QMessageBox.warning(self, "Error", "Property, Company, and Contact are required!")
                return
                
            t = CommercialTenant(**data)
            self.session.add(t)
            self.session.commit()
            self.load_data()

    def edit_tenant(self, tid):
        t = self.session.query(CommercialTenant).get(tid)
        if not t: return
        dialog = AddComTenantDialog(self.session, None, t.property_id, self, edit_tenant=t)
        if dialog.exec():
            data = dialog.get_data()
            if not data['property_id'] or not data['tenant_company'] or not data['contact']:
                QMessageBox.warning(self, "Error", "Property, Company, and Contact are required!")
                return
            t.property_id = data['property_id']
            t.flat_id = data['flat_id']
            t.tenant_company = data['tenant_company']
            t.contact = data['contact']
            t.telephone = data['telephone']
            t.email = data['email']
            t.lease_start_date = data['lease_start_date']
            t.lease_end_date = data['lease_end_date']
            t.initial_rent = data['initial_rent']
            t.rent_review = data['rent_review']
            t.notes = data['notes']
            self.session.commit()
            self.load_data()

    def delete_tenant(self, tenant_id):
        reply = QMessageBox.question(self, 'Confirm Deletion', 
                                     "Are you sure you want to permanently delete this tenant?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                t = self.session.query(CommercialTenant).get(tenant_id)
                if t:
                    self.session.delete(t)
                    self.session.commit()
                    self.load_data()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not delete tenant:\n{e}")
                self.session.rollback()

    def move_out_tenant(self, tenant_id):
        try:
            t = self.session.query(CommercialTenant).get(tenant_id)
            if not t: return
            
            dialog = MoveOutDialog(t.tenant_company, self)
            if dialog.exec():
                t.is_past = 1
                t.move_out_date = dialog.get_date()
                self.session.commit()
                self.load_data()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not move out tenant:\n{e}")
            self.session.rollback()
