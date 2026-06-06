from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton, 
    QLabel, QInputDialog, QMessageBox, QFileDialog, QAbstractItemView, QListWidgetItem, QStackedWidget
)
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import Qt, QUrl
from db import get_session, Company, Property, Flat
import os
from config_manager import get_base_dir

BASE_DIR = get_base_dir()

class ManagePropertiesWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.session = get_session()
        self.setup_ui()
        self.load_companies()

    def setup_ui(self):
        layout = QHBoxLayout(self)

        import qtawesome as qta
        
        # Companies List
        comp_layout = QVBoxLayout()
        comp_layout.addWidget(QLabel("Companies"))
        self.comp_list = QListWidget()
        self.comp_list.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.comp_list.itemSelectionChanged.connect(self.on_company_selected)
        self.comp_list.itemDoubleClicked.connect(self.open_company_folder)
        comp_layout.addWidget(self.comp_list)
        
        btn_layout_c = QHBoxLayout()
        self.btn_add_c = QPushButton(" Add")
        self.btn_add_c.setIcon(qta.icon('fa5s.plus', color='white'))
        self.btn_folder_c = QPushButton(" Set Folder")
        self.btn_folder_c.setIcon(qta.icon('fa5s.folder-open', color='white'))
        self.btn_del_c = QPushButton(" Delete")
        self.btn_del_c.setIcon(qta.icon('fa5s.trash', color='white'))
        self.btn_add_c.clicked.connect(self.add_company)
        self.btn_folder_c.clicked.connect(self.set_folder_company)
        self.btn_del_c.clicked.connect(self.del_company)
        btn_layout_c.addWidget(self.btn_add_c)
        btn_layout_c.addWidget(self.btn_folder_c)
        btn_layout_c.addWidget(self.btn_del_c)
        comp_layout.addLayout(btn_layout_c)

        # Properties List
        prop_layout = QVBoxLayout()
        prop_layout.addWidget(QLabel("Properties"))
        self.prop_stack = QStackedWidget()
        
        self.prop_list = QListWidget()
        self.prop_list.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.prop_list.itemSelectionChanged.connect(self.on_property_selected)
        self.prop_list.itemDoubleClicked.connect(self.open_property_folder)
        
        self.prop_label = QLabel("Please select a company")
        self.prop_label.setAlignment(Qt.AlignCenter)
        self.prop_label.setStyleSheet("font-weight: bold; color: #9ca3af; font-size: 16pt;")
        
        self.prop_stack.addWidget(self.prop_list)
        self.prop_stack.addWidget(self.prop_label)
        prop_layout.addWidget(self.prop_stack)
        
        btn_layout_p = QHBoxLayout()
        self.btn_add_p = QPushButton(" Add")
        self.btn_add_p.setIcon(qta.icon('fa5s.plus', color='white'))
        self.btn_folder_p = QPushButton(" Set Folder")
        self.btn_folder_p.setIcon(qta.icon('fa5s.folder-open', color='white'))
        self.btn_del_p = QPushButton(" Delete")
        self.btn_del_p.setIcon(qta.icon('fa5s.trash', color='white'))
        self.btn_add_p.clicked.connect(self.add_property)
        self.btn_folder_p.clicked.connect(self.set_folder_property)
        self.btn_del_p.clicked.connect(self.del_property)
        btn_layout_p.addWidget(self.btn_add_p)
        btn_layout_p.addWidget(self.btn_folder_p)
        btn_layout_p.addWidget(self.btn_del_p)
        prop_layout.addLayout(btn_layout_p)

        # Flats List
        flat_layout = QVBoxLayout()
        flat_layout.addWidget(QLabel("Flats"))
        self.flat_stack = QStackedWidget()
        
        self.flat_list = QListWidget()
        self.flat_list.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.flat_list.itemDoubleClicked.connect(self.open_flat_folder)
        
        self.flat_label = QLabel("Please select a property")
        self.flat_label.setAlignment(Qt.AlignCenter)
        self.flat_label.setStyleSheet("font-weight: bold; color: #9ca3af; font-size: 16pt;")
        
        self.flat_stack.addWidget(self.flat_list)
        self.flat_stack.addWidget(self.flat_label)
        flat_layout.addWidget(self.flat_stack)
        
        btn_layout_f = QHBoxLayout()
        self.btn_add_f = QPushButton(" Add")
        self.btn_add_f.setIcon(qta.icon('fa5s.plus', color='white'))
        self.btn_folder_f = QPushButton(" Set Folder")
        self.btn_folder_f.setIcon(qta.icon('fa5s.folder-open', color='white'))
        self.btn_del_f = QPushButton(" Delete")
        self.btn_del_f.setIcon(qta.icon('fa5s.trash', color='white'))
        self.btn_add_f.clicked.connect(self.add_flat)
        self.btn_folder_f.clicked.connect(self.set_folder_flat)
        self.btn_del_f.clicked.connect(self.del_flat)
        btn_layout_f.addWidget(self.btn_add_f)
        btn_layout_f.addWidget(self.btn_folder_f)
        btn_layout_f.addWidget(self.btn_del_f)
        flat_layout.addLayout(btn_layout_f)

        layout.addLayout(comp_layout)
        layout.addLayout(prop_layout)
        layout.addLayout(flat_layout)
        
        self.update_prop_state(False)
        self.update_flat_state(False)

    def update_prop_state(self, enabled):
        self.btn_add_p.setEnabled(enabled)
        self.btn_folder_p.setEnabled(enabled)
        self.btn_del_p.setEnabled(enabled)
        if enabled:
            self.prop_stack.setCurrentIndex(0)
        else:
            self.prop_stack.setCurrentIndex(1)

    def update_flat_state(self, enabled):
        self.btn_add_f.setEnabled(enabled)
        self.btn_folder_f.setEnabled(enabled)
        self.btn_del_f.setEnabled(enabled)
        if enabled:
            self.flat_stack.setCurrentIndex(0)
        else:
            self.flat_stack.setCurrentIndex(1)

    def load_companies(self):
        self.comp_list.clear()
        self.prop_list.clear()
        self.flat_list.clear()
        companies = self.session.query(Company).order_by(Company.name).all()
        for c in companies:
            self.comp_list.addItem(c.name)
            item = self.comp_list.item(self.comp_list.count() - 1)
            item.setData(32, c.id)
            
        self.update_prop_state(False)
        self.update_flat_state(False)

    def on_company_selected(self):
        self.update_flat_state(False)
        items = self.comp_list.selectedItems()
        if not items: 
            self.update_prop_state(False)
            return
            
        self.update_prop_state(True)
        self.prop_list.clear()
        comp_id = items[0].data(32)
        
        properties = self.session.query(Property).filter(Property.company_id == comp_id).order_by(Property.address).all()
        for p in properties:
            self.prop_list.addItem(p.address)
            item = self.prop_list.item(self.prop_list.count() - 1)
            item.setData(32, p.id)

    def on_property_selected(self):
        import re
        def natural_sort_key(flat):
            return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', flat.name)]

        items = self.prop_list.selectedItems()
        if not items: 
            self.update_flat_state(False)
            return
            
        self.update_flat_state(True)
        self.flat_list.clear()
        prop_id = items[0].data(32)
        
        flats = self.session.query(Flat).filter(Flat.property_id == prop_id).all()
        flats.sort(key=natural_sort_key)
        for f in flats:
            self.flat_list.addItem(f.name)
            item = self.flat_list.item(self.flat_list.count() - 1)
            item.setData(32, f.id)

    def open_folder(self, path):
        os.makedirs(path, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    # --- Company Methods ---
    def add_company(self):
        name, ok = QInputDialog.getText(self, "Add Company", "Company Name:")
        if ok and name:
            c = Company(name=name)
            reply = QMessageBox.question(self, 'Folder Location', 
                                         "Would you like to set a custom folder location for this company now?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                folder = QFileDialog.getExistingDirectory(self, f"Select Folder for {name}")
                if folder:
                    c.folder_path = folder
                    
            self.session.add(c)
            self.session.commit()
            self.load_companies()

    def del_company(self):
        items = self.comp_list.selectedItems()
        if not items: return
        comp_id = items[0].data(32)
        c = self.session.query(Company).get(comp_id)
        if c:
            self.session.delete(c)
            self.session.commit()
            self.load_companies()

    def set_folder_company(self):
        items = self.comp_list.selectedItems()
        if not items: return
        comp_id = items[0].data(32)
        c = self.session.query(Company).get(comp_id)
        if c:
            folder = QFileDialog.getExistingDirectory(self, f"Select Folder for {c.name}")
            if folder:
                c.folder_path = folder
                self.session.commit()
                QMessageBox.information(self, "Success", f"Folder for {c.name} set to:\n{folder}")

    def open_company_folder(self, item):
        comp_id = item.data(32)
        c = self.session.query(Company).get(comp_id)
        if c:
            if c.folder_path:
                self.open_folder(c.folder_path)
            else:
                default_path = os.path.join(BASE_DIR, c.name)
                c.folder_path = default_path
                self.session.commit()
                self.open_folder(default_path)

    # --- Property Methods ---
    def add_property(self):
        items = self.comp_list.selectedItems()
        if not items: return
        comp_id = items[0].data(32)
        address, ok = QInputDialog.getText(self, "Add Property", "Property Address:")
        if ok and address:
            p = Property(company_id=comp_id, address=address)
            # Ask for folder location
            reply = QMessageBox.question(self, 'Folder Location', 
                                         "Would you like to set a custom folder location for this property now?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                folder = QFileDialog.getExistingDirectory(self, f"Select Folder for {address}")
                if folder:
                    p.folder_path = folder
            
            self.session.add(p)
            self.session.commit()
            self.on_company_selected()

    def del_property(self):
        items = self.prop_list.selectedItems()
        if not items: return
        prop_id = items[0].data(32)
        p = self.session.query(Property).get(prop_id)
        if p:
            self.session.delete(p)
            self.session.commit()
            self.on_company_selected()

    def set_folder_property(self):
        items = self.prop_list.selectedItems()
        if not items: return
        prop_id = items[0].data(32)
        p = self.session.query(Property).get(prop_id)
        if p:
            folder = QFileDialog.getExistingDirectory(self, f"Select Folder for {p.address}")
            if folder:
                p.folder_path = folder
                self.session.commit()
                QMessageBox.information(self, "Success", f"Folder for {p.address} set to:\n{folder}")

    def open_property_folder(self, item):
        prop_id = item.data(32)
        p = self.session.query(Property).get(prop_id)
        if p:
            if p.folder_path:
                self.open_folder(p.folder_path)
            else:
                comp = self.session.query(Company).get(p.company_id)
                comp_root = comp.folder_path if comp.folder_path else os.path.join(BASE_DIR, comp.name)
                default_path = os.path.join(comp_root, p.address)
                p.folder_path = default_path
                self.session.commit()
                self.open_folder(default_path)

    # --- Flat Methods ---
    def add_flat(self):
        items = self.prop_list.selectedItems()
        if not items: return
        prop_id = items[0].data(32)
        name, ok = QInputDialog.getText(self, "Add Flat", "Flat Name (e.g. Flat 1):")
        if ok and name:
            f = Flat(property_id=prop_id, name=name)
            reply = QMessageBox.question(self, 'Folder Location', 
                                         "Would you like to set a custom folder location for this flat now?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                folder = QFileDialog.getExistingDirectory(self, f"Select Folder for {name}")
                if folder:
                    f.folder_path = folder
                    
            self.session.add(f)
            self.session.commit()
            self.on_property_selected()

    def del_flat(self):
        items = self.flat_list.selectedItems()
        if not items: return
        flat_id = items[0].data(32)
        f = self.session.query(Flat).get(flat_id)
        if f:
            self.session.delete(f)
            self.session.commit()
            self.on_property_selected()

    def set_folder_flat(self):
        items = self.flat_list.selectedItems()
        if not items: return
        flat_id = items[0].data(32)
        f = self.session.query(Flat).get(flat_id)
        if f:
            folder = QFileDialog.getExistingDirectory(self, f"Select Folder for {f.name}")
            if folder:
                f.folder_path = folder
                self.session.commit()
                QMessageBox.information(self, "Success", f"Folder for {f.name} set to:\n{folder}")

    def open_flat_folder(self, item):
        flat_id = item.data(32)
        f = self.session.query(Flat).get(flat_id)
        if f:
            if f.folder_path:
                self.open_folder(f.folder_path)
            else:
                p = self.session.query(Property).get(f.property_id)
                comp = self.session.query(Company).get(p.company_id)
                comp_root = comp.folder_path if comp.folder_path else os.path.join(BASE_DIR, comp.name)
                prop_root = p.folder_path if p.folder_path else os.path.join(comp_root, p.address)
                default_path = os.path.join(prop_root, f.name)
                f.folder_path = default_path
                self.session.commit()
                self.open_folder(default_path)
