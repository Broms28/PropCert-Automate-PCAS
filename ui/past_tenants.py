from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox, 
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QLabel, QTabWidget
)
from PySide6.QtCore import Qt
import qtawesome as qta
from db import get_session, Company, Property, Flat, ResidentialTenant, CommercialTenant
from utils import tenant_sort_key, property_sort_key

class PastTenantsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.session = get_session()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Top Bar Filters
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
        
        self.btn_refresh = QPushButton(" Refresh")
        self.btn_refresh.setIcon(qta.icon('fa5s.sync', color='black'))
        self.btn_refresh.clicked.connect(self.refresh_filters)
        top_bar.addWidget(self.btn_refresh)
        
        top_bar.addStretch()
        layout.addLayout(top_bar)
        
        # Tabs
        self.tabs = QTabWidget()
        
        self.res_tab = QWidget()
        self.setup_res_tab()
        self.tabs.addTab(self.res_tab, "Residential")
        
        self.com_tab = QWidget()
        self.setup_com_tab()
        self.tabs.addTab(self.com_tab, "Commercial")
        
        layout.addWidget(self.tabs)
        self.tabs.currentChanged.connect(self.load_data)
        
    def setup_res_tab(self):
        layout = QVBoxLayout(self.res_tab)
        self.res_table = QTableWidget()
        self.res_table.setColumnCount(6)
        self.res_table.setHorizontalHeaderLabels(["Property Address", "Flat", "Tenant Name", "Email", "Move Out Date", "Actions"])
        self.res_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.res_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)
        self.res_table.setColumnWidth(5, 90)
        self.res_table.setWordWrap(True)
        layout.addWidget(self.res_table)
        
    def setup_com_tab(self):
        layout = QVBoxLayout(self.com_tab)
        self.com_table = QTableWidget()
        self.com_table.setColumnCount(6)
        self.com_table.setHorizontalHeaderLabels(["Property Address", "Unit", "Tenant/Company", "Email", "Move Out Date", "Actions"])
        self.com_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.com_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)
        self.com_table.setColumnWidth(5, 90)
        self.com_table.setWordWrap(True)
        layout.addWidget(self.com_table)

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
        properties = self.session.query(Property)
        if comp_id:
            properties = properties.filter(Property.company_id == comp_id)
            
        for p in sorted(properties.all(), key=property_sort_key):
            self.prop_combo.addItem(p.address, userData=p.id)
            
        self.prop_combo.blockSignals(False)
        self.load_data()

    def load_data(self):
        if self.tabs.currentIndex() == 0:
            self.load_res_data()
        else:
            self.load_com_data()

    def load_res_data(self):
        self.res_table.setRowCount(0)
        
        comp_id = self.comp_combo.currentData()
        prop_id = self.prop_combo.currentData()
        
        query = self.session.query(ResidentialTenant).join(Flat).join(Property)
        if comp_id:
            query = query.filter(Property.company_id == comp_id)
        if prop_id:
            query = query.filter(Property.id == prop_id)
            
        query = query.filter(Property.property_type == "Residential")
        query = query.filter(ResidentialTenant.is_past == 1)
        
        tenants = query.all()
        tenants.sort(key=tenant_sort_key)
        
        self.res_table.setRowCount(len(tenants))
        for row, t in enumerate(tenants):
            i_prop = QTableWidgetItem(t.flat.property.address)
            i_prop.setFlags(i_prop.flags() & ~Qt.ItemIsEditable)
            self.res_table.setItem(row, 0, i_prop)
            
            i_flat = QTableWidgetItem(t.flat.name)
            i_flat.setFlags(i_flat.flags() & ~Qt.ItemIsEditable)
            self.res_table.setItem(row, 1, i_flat)
            
            i_name = QTableWidgetItem(t.name)
            i_name.setFlags(i_name.flags() & ~Qt.ItemIsEditable)
            self.res_table.setItem(row, 2, i_name)
            
            i_email = QTableWidgetItem(t.email or "")
            i_email.setFlags(i_email.flags() & ~Qt.ItemIsEditable)
            self.res_table.setItem(row, 3, i_email)
            
            move_str = t.move_out_date.strftime("%d/%m/%Y") if t.move_out_date else ""
            i_move = QTableWidgetItem(move_str)
            i_move.setFlags(i_move.flags() & ~Qt.ItemIsEditable)
            self.res_table.setItem(row, 4, i_move)
            
            btn_delete = QPushButton()
            btn_delete.setIcon(qta.icon('fa5s.trash', color='white'))
            btn_delete.setStyleSheet("background-color: #ef4444; padding: 5px;")
            btn_delete.setToolTip("Permanently Delete Tenant")
            btn_delete.clicked.connect(lambda checked=False, tid=t.id: self.delete_res_tenant(tid))
            
            w = QWidget()
            l = QHBoxLayout(w)
            l.setContentsMargins(5, 2, 5, 2)
            l.addWidget(btn_delete)
            self.res_table.setCellWidget(row, 5, w)

    def load_com_data(self):
        self.com_table.setRowCount(0)
        
        comp_id = self.comp_combo.currentData()
        prop_id = self.prop_combo.currentData()
        
        query = self.session.query(CommercialTenant).join(Property).outerjoin(Flat)
        if comp_id:
            query = query.filter(Property.company_id == comp_id)
        if prop_id:
            query = query.filter(Property.id == prop_id)
            
        query = query.filter(Property.property_type == "Commercial")
        query = query.filter(CommercialTenant.is_past == 1)
        
        tenants = query.all()
        tenants.sort(key=tenant_sort_key)
        
        self.com_table.setRowCount(len(tenants))
        for row, t in enumerate(tenants):
            i_prop = QTableWidgetItem(t.property.address)
            i_prop.setFlags(i_prop.flags() & ~Qt.ItemIsEditable)
            self.com_table.setItem(row, 0, i_prop)
            
            unit_name = t.flat.name if t.flat else "-"
            i_flat = QTableWidgetItem(unit_name)
            i_flat.setFlags(i_flat.flags() & ~Qt.ItemIsEditable)
            self.com_table.setItem(row, 1, i_flat)
            
            i_name = QTableWidgetItem(t.tenant_company)
            i_name.setFlags(i_name.flags() & ~Qt.ItemIsEditable)
            self.com_table.setItem(row, 2, i_name)
            
            i_email = QTableWidgetItem(t.email or "")
            i_email.setFlags(i_email.flags() & ~Qt.ItemIsEditable)
            self.com_table.setItem(row, 3, i_email)
            
            move_str = t.move_out_date.strftime("%d/%m/%Y") if t.move_out_date else ""
            i_move = QTableWidgetItem(move_str)
            i_move.setFlags(i_move.flags() & ~Qt.ItemIsEditable)
            self.com_table.setItem(row, 4, i_move)
            
            btn_delete = QPushButton()
            btn_delete.setIcon(qta.icon('fa5s.trash', color='white'))
            btn_delete.setStyleSheet("background-color: #ef4444; padding: 5px;")
            btn_delete.setToolTip("Permanently Delete Tenant")
            btn_delete.clicked.connect(lambda checked=False, tid=t.id: self.delete_com_tenant(tid))
            
            w = QWidget()
            l = QHBoxLayout(w)
            l.setContentsMargins(5, 2, 5, 2)
            l.addWidget(btn_delete)
            self.com_table.setCellWidget(row, 5, w)

    def delete_res_tenant(self, tid):
        reply = QMessageBox.question(self, 'Confirm Deletion', 
                                     "Are you sure you want to permanently delete this archived tenant?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                t = self.session.query(ResidentialTenant).get(tid)
                if t:
                    self.session.delete(t)
                    self.session.commit()
                    self.load_data()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not delete tenant:\n{e}")
                self.session.rollback()

    def delete_com_tenant(self, tid):
        reply = QMessageBox.question(self, 'Confirm Deletion', 
                                     "Are you sure you want to permanently delete this archived tenant?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                t = self.session.query(CommercialTenant).get(tid)
                if t:
                    self.session.delete(t)
                    self.session.commit()
                    self.load_data()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not delete tenant:\n{e}")
                self.session.rollback()
