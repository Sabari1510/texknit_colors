from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
                             QPushButton, QLabel, QMessageBox, QHBoxLayout)
from database.models import Supplier, db
from services.communication_service import relay

class SupplierFormDialog(QDialog):
    def __init__(self, supplier=None, parent=None):
        super().__init__(parent)
        self.supplier = supplier
        self.setWindowTitle("Edit Supplier" if supplier else "Register New Supplier")
        self.resize(450, 450)
        
        # Load Styles
        with open("ui/styles.qss", "r") as f:
            self.setStyleSheet(f.read())
            
        self.setup_ui()
        if self.supplier:
            self.fill_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        title_text = "EDIT SUPPLIER" if self.supplier else "SUPPLIER REGISTRATION"
        title = QLabel(title_text)
        title.setObjectName("TitleLabel")
        title.setStyleSheet("font-size: 18px; letter-spacing: 1px;")
        layout.addWidget(title)
        
        form_container = QFormLayout()
        form_container.setSpacing(15)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. Acme Chemicals Pvt Ltd")
        
        self.contact_person = QLineEdit()
        self.contact_person.setPlaceholderText("Primary Contact Person")
        
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Phone Number")
        
        self.gst_no_input = QLineEdit()
        self.gst_no_input.setPlaceholderText("GST No (15 digits)")
        
        self.categories_input = QLineEdit()
        self.categories_input.setPlaceholderText("e.g. Dyes, Chemicals, Tools")
        
        form_container.addRow("Company Name:", self.name_input)
        form_container.addRow("Contact Person:", self.contact_person)
        form_container.addRow("Phone / Mobile:", self.phone_input)
        form_container.addRow("GST No:", self.gst_no_input)
        form_container.addRow("Categories:", self.categories_input)
        
        layout.addLayout(form_container)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setProperty("class", "SecondaryButton")
        btn_cancel.clicked.connect(self.reject)
        
        save_btn_text = "Update Supplier" if self.supplier else "Register Supplier"
        self.btn_save = QPushButton(save_btn_text)
        self.btn_save.setProperty("class", "PrimaryButton")
        self.btn_save.clicked.connect(self.save)
        
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(self.btn_save)
        layout.addLayout(btn_layout)

    def fill_data(self):
        self.name_input.setText(self.supplier.name)
        self.contact_person.setText(self.supplier.contact_person)
        self.phone_input.setText(self.supplier.phone)
        self.gst_no_input.setText(self.supplier.gst_no or "")
        self.categories_input.setText(self.supplier.material_categories)

    def save(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation Error", "Company Name is required.")
            return
            
        try:
            with db.atomic():
                if self.supplier:
                    # Update
                    self.supplier.name = name
                    self.supplier.contact_person = self.contact_person.text().strip()
                    self.supplier.phone = self.phone_input.text().strip()
                    self.supplier.gst_no = self.gst_no_input.text().strip()
                    self.supplier.material_categories = self.categories_input.text().strip()
                    self.supplier.save()
                else:
                    # Create
                    Supplier.create(
                        name=name,
                        contact_person=self.contact_person.text().strip(),
                        phone=self.phone_input.text().strip(),
                        gst_no=self.gst_no_input.text().strip(),
                        material_categories=self.categories_input.text().strip(),
                        rating=5.0 # Initial rating for new partner
                    )
            self.accept()
            relay.data_changed.emit()
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to save supplier: {str(e)}")
