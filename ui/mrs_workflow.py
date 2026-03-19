from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, 
                             QComboBox, QFrame, QScrollArea, QTabWidget, QMessageBox, QGridLayout, QDateEdit)
from PySide6.QtCore import Qt, QDate
from datetime import datetime
from services.mrs_service import MRSService
from services.inventory_service import InventoryService
from services.communication_service import relay
from services.validators import validate_required, validate_batch_id, validate_gst, validate_positive_float, collect_errors
from database.models import Consumer
from ui.mrs_issue_dialog import MRSIssueDialog
from ui.components.status_badge import StatusBadge

class MRSWorkflowView(QWidget):
    def __init__(self, user):
        super().__init__()
        self.user = user
        self.editing_invoice_id = None
        self.setup_ui()
        self.load_data()
        
        from services.communication_service import relay
        relay.edit_requested.connect(self.edit_draft_invoice)
        
        # Connect to reactivity system
        relay.data_changed.connect(self.refresh_consumers)
        relay.data_changed.connect(self.load_data)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)
        
        title_container = QVBoxLayout()
        title = QLabel("Invoices")
        title.setObjectName("TitleLabel")
        subtitle = QLabel("Generate sales invoices and manage billing history.")
        subtitle.setObjectName("SubtitleLabel")
        title_container.addWidget(title)
        title_container.addWidget(subtitle)
        layout.addLayout(title_container)
        
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #e2e8f0; border-radius: 12px; background: white; top: 0px; margin-top: 10px; }
            QTabBar { background: #f1f5f9; border-radius: 10px; padding: 4px; }
            QTabBar::tab { 
                padding: 10px 24px; 
                background: transparent; 
                border: none;
                border-radius: 8px;
                color: #64748b;
                font-weight: 700;
                font-size: 12px;
                margin-right: 2px;
            }
            QTabBar::tab:hover {
                background: rgba(0,0,0,0.03);
            }
            QTabBar::tab:selected { 
                background: white; 
                color: #8B5E3C; 
            }
        """)
        
        # Tab 1: Create Invoice
        if self.user.role in ['SUPERVISOR', 'ADMIN', 'STORE_MANAGER']:
            self.tabs.addTab(self.create_new_request_tab(), "Create Invoice")
            
        # Tab 2: Invoice History
        self.invoice_tab = self.create_invoice_history_tab()
        self.tabs.addTab(self.invoice_tab, "Invoice History")
        
        layout.addWidget(self.tabs)

    def create_new_request_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)
        
        from ui.components.card_widget import CardWidget
        form_card = CardWidget()
        form_layout = form_card.layout
        
        grid = QGridLayout()
        grid.setSpacing(10)
        grid.setContentsMargins(0, 0, 0, 0)
        
        lbl_style = "font-weight: 700; font-size: 10px; color: #64748b; letter-spacing: 0.5px;"
        
        # New: Invoice Type Selection
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Existing Consumer", "New User / Manual Entry"])
        self.type_combo.setMinimumHeight(36)
        self.type_combo.setStyleSheet("border: 1px solid #e2e8f0; border-radius: 8px; padding: 0 12px; background: white; color: #000000;")
        self.type_combo.currentIndexChanged.connect(self.on_invoice_type_changed)
        
        self.consumer_combo = QComboBox()
        self.consumer_combo.setPlaceholderText("Select Consumer")
        self.consumer_combo.setMinimumHeight(36)
        self.consumer_combo.setStyleSheet("border: 1.5px solid #8B5E3C; border-radius: 8px; padding: 0 12px; background: white; color: #000000;")
        self.consumer_combo.currentIndexChanged.connect(self.on_consumer_selected)

        # Row 0: Invoice Type
        type_lbl = QLabel("INVOICE FOR")
        type_lbl.setStyleSheet(lbl_style)
        grid.addWidget(type_lbl, 0, 0)
        grid.addWidget(self.type_combo, 0, 1)
        grid.addWidget(self.consumer_combo, 0, 2, 1, 2)
        
        # Load Consumers initially
        self.refresh_consumers()
        
        # Batch ID
        self.batch_input = QLineEdit()
        self.batch_input.setPlaceholderText("e.g. BATCH-2026-001")
        self.batch_input.setMinimumHeight(36)
        self.batch_input.setStyleSheet("border: 1px solid #e2e8f0; border-radius: 8px; padding: 0 12px; background: white;")
        
        # Recipient Name
        self.client_input = QLineEdit()
        self.client_input.setPlaceholderText("Enter client or department name")
        self.client_input.setMinimumHeight(36)
        self.client_input.setStyleSheet("border: 1px solid #e2e8f0; border-radius: 8px; padding: 0 12px; background: white;")
        
        # Row 1: Batch & Client
        batch_lbl = QLabel("BATCH ID")
        batch_lbl.setStyleSheet(lbl_style)
        grid.addWidget(batch_lbl, 1, 0)
        grid.addWidget(self.batch_input, 1, 1)
        
        client_lbl = QLabel("CUSTOMER")
        client_lbl.setStyleSheet(lbl_style)
        grid.addWidget(client_lbl, 1, 2)
        grid.addWidget(self.client_input, 1, 3)
        
        # New: Address
        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText("Enter client address")
        self.address_input.setMinimumHeight(36)
        self.address_input.setStyleSheet("border: 1px solid #e2e8f0; border-radius: 8px; padding: 0 12px; background: white;")

        # New: GSTIN
        self.gstin_input = QLineEdit()
        self.gstin_input.setPlaceholderText("e.g. 33AAAAA0000A1Z5")
        self.gstin_input.setMinimumHeight(36)
        self.gstin_input.setMaxLength(15)
        self.gstin_input.setStyleSheet("border: 1px solid #e2e8f0; border-radius: 8px; padding: 0 12px; background: white;")
        # Auto-uppercase GSTIN input
        self.gstin_input.textChanged.connect(
            lambda text: self.gstin_input.setText(text.upper()) if text != text.upper() else None
        )

        # Row 2: Address & GSTIN
        addr_lbl = QLabel("ADDRESS")
        addr_lbl.setStyleSheet(lbl_style)
        grid.addWidget(addr_lbl, 2, 0)
        grid.addWidget(self.address_input, 2, 1)
        
        gstin_lbl = QLabel("GSTIN")
        gstin_lbl.setStyleSheet(lbl_style)
        grid.addWidget(gstin_lbl, 2, 2)
        grid.addWidget(self.gstin_input, 2, 3)
        
        # Row 3: Due Date
        self.due_date_input = QDateEdit()
        self.due_date_input.setCalendarPopup(True)
        self.due_date_input.setDate(QDate.currentDate().addDays(14))
        self.due_date_input.setMinimumHeight(36)
        self.due_date_input.setStyleSheet("border: 1px solid #e2e8f0; border-radius: 8px; padding: 0 12px; background: white;")

        # Row 3: Due Date
        due_lbl = QLabel("DUE DATE")
        due_lbl.setStyleSheet(lbl_style)
        grid.addWidget(due_lbl, 3, 0)
        grid.addWidget(self.due_date_input, 3, 1)
        
        form_layout.addLayout(grid)
        form_layout.addSpacing(10)
        
        # Items Section
        items_header = QHBoxLayout()
        items_label = QLabel("INVOICE ITEMS")
        items_label.setStyleSheet("font-weight: 700; font-size: 11px; color: #94a3b8; letter-spacing: 0.5px;")
        self.btn_add_item = QPushButton("+ Add Item")
        self.btn_add_item.setStyleSheet("color: #8B5E3C; background: rgba(139, 94, 60, 0.1); border: none; padding: 6px 14px; border-radius: 14px; font-weight: 700;")
        self.btn_add_item.clicked.connect(self.add_item_row)
        items_header.addWidget(items_label)
        items_header.addStretch()
        items_header.addWidget(self.btn_add_item)
        form_layout.addLayout(items_header)
        
        self.items_scroll = QScrollArea()
        self.items_scroll.setWidgetResizable(True)
        self.items_scroll.setStyleSheet("background: transparent; border: 1px solid rgba(255,255,255,0.05); border-radius: 8px;")
        self.items_container = QWidget()
        self.items_layout = QVBoxLayout(self.items_container)
        self.items_layout.setAlignment(Qt.AlignTop)
        self.items_layout.setSpacing(10)
        self.items_scroll.setWidget(self.items_container)
        form_layout.addWidget(self.items_scroll)
        
        self.rows = []
        self.add_item_row() # Initial row
        
        # Submit Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.btn_submit_invoice = QPushButton("Generate Invoice")
        self.btn_submit_invoice.setStyleSheet("""
            QPushButton {
                background-color: #8B5E3C;
                color: white;
                border: none;
                padding: 10px 30px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #734D31;
            }
        """)
        self.btn_submit_invoice.setFixedWidth(240)
        self.btn_submit_invoice.clicked.connect(lambda: self.submit_request(generate_invoice=True))
        
        self.btn_cancel_edit = QPushButton("Clear Form")
        self.btn_cancel_edit.setStyleSheet("""
            QPushButton {
                background-color: #f1f5f9;
                color: #475569;
                border: 1px solid #e2e8f0;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #e2e8f0; }
        """)
        self.btn_cancel_edit.clicked.connect(self.handle_cancel_clear)
        
        button_layout.addWidget(self.btn_cancel_edit)
        button_layout.addWidget(self.btn_submit_invoice)
        form_layout.addLayout(button_layout)
        
        layout.addWidget(form_card)
        return tab

    def refresh_consumers(self):
        if not hasattr(self, 'consumer_combo'):
            return
        self.consumer_combo.clear()
        self.consumer_combo.addItem("Select a Consumer...", None)
        consumers = Consumer.select().order_by(Consumer.company_name)
        for c in consumers:
            self.consumer_combo.addItem(c.company_name, c)

    def on_invoice_type_changed(self, index):
        if not hasattr(self, 'consumer_combo'):
            return
        is_existing = (index == 0)
        self.consumer_combo.setVisible(is_existing)
        
        # If new user, clear and enable everything
        if not is_existing:
            self.client_input.clear()
            self.client_input.setReadOnly(False)
            self.client_input.setStyleSheet("border: 1px solid #e2e8f0; border-radius: 8px; padding: 0 12px; background: white; color: #000000;")
            
            self.address_input.clear()
            self.address_input.setReadOnly(False)
            self.address_input.setStyleSheet("border: 1px solid #e2e8f0; border-radius: 8px; padding: 0 12px; background: white; color: #000000;")
            
            self.gstin_input.clear()
            self.gstin_input.setReadOnly(False)
            self.gstin_input.setStyleSheet("border: 1px solid #e2e8f0; border-radius: 8px; padding: 0 12px; background: white; color: #000000;")
        else:
            # Re-trigger selection logic to populate if something is already selected
            self.on_consumer_selected(self.consumer_combo.currentIndex())

    def on_consumer_selected(self, index):
        if self.type_combo.currentIndex() != 0:
            return
            
        consumer = self.consumer_combo.currentData()
        readonly_style = "border: 1px solid #e2e8f0; border-radius: 8px; padding: 0 12px; background: #f1f5f9; color: #475569;"
        editable_style = "border: 1px solid #e2e8f0; border-radius: 8px; padding: 0 12px; background: white; color: #000000;"

        if consumer:
            self.client_input.setText(consumer.company_name)
            self.client_input.setReadOnly(True)
            self.client_input.setStyleSheet(readonly_style)
            
            self.address_input.setText(consumer.location or "")
            self.address_input.setReadOnly(True)
            self.address_input.setStyleSheet(readonly_style)
            
            self.gstin_input.setText(consumer.gst_no or "")
            self.gstin_input.setReadOnly(True)
            self.gstin_input.setStyleSheet(readonly_style)
            
            from PySide6.QtCore import QDate
            self.due_date_input.setDate(QDate.currentDate().addDays(14))
        else:
            self.client_input.clear()
            self.client_input.setReadOnly(False)
            self.client_input.setStyleSheet(editable_style)
            
            self.address_input.clear()
            self.address_input.setReadOnly(False)
            self.address_input.setStyleSheet(editable_style)
            
            self.gstin_input.clear()
            self.gstin_input.setReadOnly(False)
            self.gstin_input.setStyleSheet(editable_style)
            
            from PySide6.QtCore import QDate
            self.due_date_input.setDate(QDate.currentDate().addDays(14))

    def add_item_row(self):
        row = QFrame()
        row.setStyleSheet("background: #F8FAFC; border-radius: 8px; border: 1px solid #E5E7EB;")
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(12, 12, 12, 12)
        
        combo = QComboBox()
        combo.setPlaceholderText("Select Material")
        combo.setMinimumHeight(36)
        combo.setStyleSheet("border: 1px solid #e2e8f0; border-radius: 8px; padding: 0 12px; background: white; color: #000000;")
        materials = InventoryService.get_all_materials()
        for m in materials:
            combo.addItem(f"{m.name} (Available: {m.quantity} {m.unit})", m.id)
            
        qty_input = QLineEdit()
        qty_input.setPlaceholderText("Qty")
        qty_input.setFixedWidth(100)
        qty_input.setMinimumHeight(36)
        qty_input.setStyleSheet("border: 1px solid #e2e8f0; border-radius: 8px; padding: 0 12px; background: white; color: #000000;")
        
        from PySide6.QtGui import QDoubleValidator
        validator = QDoubleValidator(0.0, 1000000.0, 3)
        validator.setNotation(QDoubleValidator.StandardNotation)
        qty_input.setValidator(validator)
        
        btn_remove = QPushButton("✕")
        btn_remove.setStyleSheet("color: #EF4444; background: transparent; font-weight: 800; border: none;")
        btn_remove.clicked.connect(lambda: self.remove_row(row))
        
        row_layout.addWidget(combo, 3)
        row_layout.addWidget(qty_input, 1)
        row_layout.addWidget(btn_remove)
        
        self.items_layout.addWidget(row)
        self.rows.append({'row': row, 'combo': combo, 'qty': qty_input})

    def remove_row(self, row_widget):
        row_widget.deleteLater()
        self.rows = [r for r in self.rows if r['row'] != row_widget]

    def create_invoice_history_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Ultra-Minimal Filter Bar
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(8)
        filter_layout.setContentsMargins(0, 5, 0, 10)
        
        # Minimal Search
        self.invoice_search = QLineEdit()
        self.invoice_search.setPlaceholderText("Search invoices...")
        self.invoice_search.setMinimumWidth(300)
        self.invoice_search.setStyleSheet("""
            QLineEdit {
                border: 1px solid #e2e8f0;
                border-radius: 20px;
                padding: 6px 15px;
                background: #f8fafc;
                font-size: 13px;
                color: #1e293b;
            }
            QLineEdit:focus {
                border: 1px solid #3b82f6;
                background: #ffffff;
            }
        """)
        self.invoice_search.textChanged.connect(self.filter_invoices)
        filter_layout.addWidget(self.invoice_search, 2)
        
        # Minimal Status
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All Statuses", "Draft", "Sent", "Paid", "Overdue"])
        self.status_filter.setFixedWidth(120)
        self.status_filter.setStyleSheet("""
            QComboBox {
                border: 1px solid #e2e8f0;
                border-radius: 15px;
                padding: 4px 10px;
                background: #f8fafc;
                font-size: 12px;
                color: #475569;
            }
        """)
        self.status_filter.currentIndexChanged.connect(self.filter_invoices)
        filter_layout.addWidget(self.status_filter)
        
        # Minimal Date Selection
        date_style = """
            QDateEdit {
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                padding: 4px 5px;
                background: #f8fafc;
                font-size: 12px;
                color: #475569;
                min-width: 110px;
            }
            QDateEdit::drop-button { 
                border: none;
                width: 20px;
            }
        """
        
        filter_layout.addWidget(QLabel("📅"))
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setFixedWidth(115)
        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        self.start_date.setStyleSheet(date_style)
        self.start_date.dateChanged.connect(self.filter_invoices)
        filter_layout.addWidget(self.start_date)
        
        filter_layout.addWidget(QLabel("-"))
        
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setFixedWidth(115)
        self.end_date.setDate(QDate.currentDate().addDays(1))
        self.end_date.setStyleSheet(date_style)
        self.end_date.dateChanged.connect(self.filter_invoices)
        filter_layout.addWidget(self.end_date)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        self.invoice_table = QTableWidget()
        headers = ["Invoice #", "Batch Ref", "Date", "Original Total", "Late Fee", "Total Due", "Status", "Due Date", "Days Overdue", "Action"]
        self.invoice_table.setColumnCount(len(headers))
        self.invoice_table.setHorizontalHeaderLabels(headers)
        self.invoice_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.invoice_table.verticalHeader().setVisible(False)
        self.invoice_table.verticalHeader().setDefaultSectionSize(52)
        self.invoice_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.invoice_table.setStyleSheet("QTableWidget { border: none; background: white; gridline-color: #f1f5f9; }")
        
        layout.addWidget(self.invoice_table)
        return tab

    def load_invoice_history(self):
        from services.invoice_service import InvoiceService
        self.all_invoices = list(InvoiceService.get_all_invoices())
        self.display_invoices(self.all_invoices)

    def filter_invoices(self):
        term = self.invoice_search.text().lower()
        status_filter = self.status_filter.currentText().upper()
        
        start_date = self.start_date.date().toPython()
        end_date = self.end_date.date().toPython()
        
        filtered = []
        for inv in self.all_invoices:
            match_term = (term in inv.invoice_no.lower() or
                         term in inv.mrs.batch_id.lower() or
                         term in (inv.client_name or '').lower())
            
            match_status = True
            if status_filter != "ALL STATUSES":
                if status_filter == "OVERDUE":
                    match_status = inv.days_overdue > 0
                else:
                    match_status = inv.status.upper() == status_filter
            
            # Date filtering
            inv_date = inv.created_at
            if isinstance(inv_date, datetime):
                inv_date = inv_date.date()
                
            match_date = (start_date <= inv_date <= end_date)
            
            if match_term and match_status and match_date:
                filtered.append(inv)
                
        self.display_invoices(filtered)

    def display_invoices(self, invoices):
        self.invoice_table.setRowCount(len(invoices))
        for i, inv in enumerate(invoices):
            self.invoice_table.setItem(i, 0, QTableWidgetItem(inv.invoice_no))
            self.invoice_table.setItem(i, 1, QTableWidgetItem(inv.mrs.batch_id))
            
            # Dynamic Timestamp
            status = inv.status.upper()
            if status == 'PAID' and inv.paid_at:
                time_label = "Paid: " + inv.paid_at.strftime("%Y-%m-%d %H:%M")
            elif status == 'SENT' and inv.sent_at:
                time_label = "Sent: " + inv.sent_at.strftime("%Y-%m-%d %H:%M")
            elif inv.draft_at:
                time_label = "Draft: " + inv.draft_at.strftime("%Y-%m-%d %H:%M")
            else:
                time_label = inv.created_at.strftime("%Y-%m-%d %H:%M")
            
            self.invoice_table.setItem(i, 2, QTableWidgetItem(time_label))
            
            # Original Total
            self.invoice_table.setItem(i, 3, QTableWidgetItem(f"₹{inv.grand_total:,.2f}"))
            
            # Late Fee
            fee_item = QTableWidgetItem(f"₹{inv.late_fee:,.2f}")
            if inv.late_fee > 0:
                fee_item.setForeground(Qt.red)
            self.invoice_table.setItem(i, 4, fee_item)
            
            # Total Due
            total_item = QTableWidgetItem(f"₹{inv.total_due:,.2f}")
            font = total_item.font()
            font.setBold(True)
            total_item.setFont(font)
            self.invoice_table.setItem(i, 5, total_item)
            
            # Status & Overdue Logic
            status = inv.status.upper()
            days_overdue = inv.days_overdue
            is_overdue = days_overdue > 0
            
            # Status Badge
            from ui.components.status_badge import StatusBadge
            if is_overdue:
                badge = StatusBadge("OVERDUE", "critical")
            else:
                badge_type = "neutral"
                if status == "PAID": badge_type = "success"
                elif status == "DRAFT": badge_type = "warning"
                badge = StatusBadge(status, badge_type)
            
            status_widget = QWidget()
            status_layout = QHBoxLayout(status_widget)
            status_layout.setContentsMargins(0, 0, 0, 0)
            status_layout.addWidget(badge, alignment=Qt.AlignCenter)
            self.invoice_table.setCellWidget(i, 6, status_widget)

            # Due Date
            due_str = inv.due_date.strftime("%Y-%m-%d") if inv.due_date else "N/A"
            self.invoice_table.setItem(i, 7, QTableWidgetItem(due_str))
            
            # Days Overdue
            overdue_text = f"{days_overdue} days" if days_overdue > 0 else "-"
            self.invoice_table.setItem(i, 8, QTableWidgetItem(overdue_text))
            
            # Action Button Container
            widget = QWidget()
            layout = QHBoxLayout(widget)
            layout.setContentsMargins(0, 0, 10, 0)
            layout.setSpacing(12)
            layout.addStretch()
            
            # 1. Details Icon (ⓘ)
            btn_details = QPushButton("ⓘ")
            btn_details.setFixedSize(32, 32)
            btn_details.setCursor(Qt.PointingHandCursor)
            btn_details.setToolTip("View / Manage Invoice")
            btn_details.setStyleSheet("""
                QPushButton {
                    background-color: #F8FAFC;
                    color: #475569;
                    border: 1px solid #E2E8F0;
                    border-radius: 16px;
                    font-size: 16px;
                    font-weight: 800;
                }
                QPushButton:hover {
                    background-color: #475569;
                    color: white;
                    border: none;
                }
            """)
            btn_details.clicked.connect(lambda checked=False, iv=inv: self.open_invoice_dialog(iv))
            layout.addWidget(btn_details)
            
            if status == "DRAFT":
                # 2. Edit Icon (✎)
                btn_edit = QPushButton("✎")
                btn_edit.setFixedSize(32, 32)
                btn_edit.setCursor(Qt.PointingHandCursor)
                btn_edit.setToolTip("Edit Draft Invoice")
                btn_edit.setStyleSheet("""
                    QPushButton {
                        background-color: #FFFFFF;
                        color: #8B5E3C;
                        border: 1px solid #E5E7EB;
                        border-radius: 16px;
                        font-size: 16px;
                    }
                    QPushButton:hover {
                        background-color: #8B5E3C;
                        color: white;
                        border: none;
                    }
                """)
                btn_edit.clicked.connect(lambda checked=False, iv=inv: self.edit_draft_invoice(iv))
                layout.addWidget(btn_edit)
                
                # 3. Delete Icon (✕)
                btn_del = QPushButton("✕")
                btn_del.setFixedSize(32, 32)
                btn_del.setCursor(Qt.PointingHandCursor)
                btn_del.setToolTip("Delete Draft Invoice")
                btn_del.setStyleSheet("""
                    QPushButton {
                        background-color: #FEE2E2;
                        color: #EF4444;
                        border: 1px solid #FECACA;
                        border-radius: 16px;
                        font-size: 14px;
                        font-weight: 800;
                    }
                    QPushButton:hover {
                        background-color: #EF4444;
                        color: white;
                        border: none;
                    }
                """)
                btn_del.clicked.connect(lambda checked=False, iv=inv: self.confirm_delete_invoice(iv))
                layout.addWidget(btn_del)
            
            self.invoice_table.setCellWidget(i, 9, widget)

    def _get_action_button_style(self, color):
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 10px;
                font-weight: 700;
                text-transform: uppercase;
            }}
            QPushButton:hover {{
                background-color: {color}CC;
            }}
        """

    def edit_draft_invoice(self, invoice):
        """Load draft invoice data into the creation form."""
        if not hasattr(self, 'type_combo'):
            QMessageBox.warning(self, "Permission Denied", "You do not have permission to edit invoices.")
            return
        self.tabs.setCurrentIndex(0)
        
        # Determine invoice type
        # We don't store "is_manual" explicitly, but we can check if client exists in Consumer
        consumer = Consumer.get_or_none(Consumer.company_name == invoice.client_name)
        if consumer:
            self.type_combo.setCurrentIndex(0)
            index = self.consumer_combo.findText(consumer.company_name)
            self.consumer_combo.setCurrentIndex(index)
        else:
            self.type_combo.setCurrentIndex(1)
            self.client_input.setText(invoice.client_name or "")
            self.address_input.setText(invoice.client_address or "")
            self.gstin_input.setText(invoice.client_gstin or "")

        self.batch_input.setText(invoice.mrs.batch_id)
        if invoice.due_date:
            self.due_date_input.setDate(QDate(invoice.due_date.year, invoice.due_date.month, invoice.due_date.day))

        # Clear and load items
        for r in self.rows: r['row'].deleteLater()
        self.rows = []
        
        for item in invoice.mrs.items:
            self.add_item_row()
            last_row = self.rows[-1]
            idx = last_row['combo'].findData(item.material_id)
            if idx >= 0: last_row['combo'].setCurrentIndex(idx)
            # Use quantity_requested as stored in MRSItem model
            last_row['qty'].setText(str(getattr(item, 'quantity_requested', 0)))

        # Store the invoice ID being edited
        self.editing_invoice_id = invoice.id
        self.btn_submit_invoice.setText("Update Draft Invoice")
        self.btn_cancel_edit.setText("Cancel Edit")

    def handle_cancel_clear(self):
        if self.editing_invoice_id:
            # If editing, ask if they want to discard changes
            reply = QMessageBox.question(self, "Cancel Edit", 
                                       "Discard changes and return to history?",
                                       QMessageBox.Yes | QMessageBox.No)
            if reply != QMessageBox.Yes: return
        
        self.reset_form()
        self.editing_invoice_id = None
        self.btn_submit_invoice.setText("Generate Invoice")
        self.btn_cancel_edit.setText("Clear Form")
        if self.tabs.currentIndex() == 0 and self.editing_invoice_id:
            self.tabs.setCurrentIndex(1)

    def reset_form(self):
        self.batch_input.clear()
        self.client_input.clear()
        self.address_input.clear()
        self.gstin_input.clear()
        self.due_date_input.setDate(QDate.currentDate().addDays(14))
        for r in self.rows: r['row'].deleteLater()
        self.rows = []
        self.add_item_row()

    def confirm_delete_invoice(self, invoice):
        reply = QMessageBox.question(self, "Confirm Delete", 
                                   f"Are you sure you want to delete Invoice #{invoice.id}?\nThis will also delete the associated MRS record.",
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            # Delete MRS (cascade will handle child items if set, but we'll be careful)
            if invoice.mrs:
                invoice.mrs.delete_instance(recursive=True)
            invoice.delete_instance()
            relay.data_changed.emit()
            self.filter_invoices()

    def show_invoice_dialog(self, mrs, client_name=None, client_address=None, client_gstin=None, due_date=None):
        from services.invoice_service import InvoiceService
        invoice = InvoiceService.get_invoice_by_mrs(mrs.id)
        if not invoice:
            invoice = InvoiceService.create_invoice_from_mrs(mrs.id, client_name=client_name, client_address=client_address, client_gstin=client_gstin, due_date=due_date)
            self.load_invoice_history()
        
        self.open_invoice_dialog(invoice)

    def open_invoice_dialog(self, invoice):
        from ui.invoice_dialog import InvoiceDialog
        dialog = InvoiceDialog(invoice, self)
        dialog.exec()


    def load_data(self):
        # Only load invoice history now
        self.load_invoice_history()

    def handle_action(self, mrs):
        if self.user.role != 'SUPERVISOR':
            dialog = MRSIssueDialog(mrs, self)
            if dialog.exec():
                if dialog.issue_items:
                    MRSService.issue_mrs(mrs.id, self.user.id, dialog.issue_items)
                    self.load_data()
        else:
            # Show details (could expand further)
            msg = QMessageBox()
            msg.setWindowTitle(f"Request {mrs.batch_id}")
            text = f"Status: {mrs.status}\n\nItems:\n"
            for it in mrs.items:
                text += f"- {it.material.name}: {it.quantity_issued}/{it.quantity_requested} {it.material.unit}\n"
            msg.setText(text)
            msg.exec()

    def submit_request(self, generate_invoice=False):
        batch_id = self.batch_input.text().strip()
        client_name = self.client_input.text().strip()
        client_address = self.address_input.text().strip()
        client_gstin = self.gstin_input.text().strip()
        due_date = self.due_date_input.date().toPython()

        # Validate header fields
        validations = [
            validate_batch_id(batch_id),
            validate_required(client_name, "Customer Name"),
            validate_gst(client_gstin),
        ]

        # Validate item rows
        items = []
        has_valid_item = False
        for i, r in enumerate(self.rows):
            mid = r['combo'].currentData()
            qty_text = r['qty'].text().strip()
            if not mid and not qty_text:
                continue  # Skip fully empty rows
            if mid and qty_text:
                qty_valid, qty_msg, qty_val = validate_positive_float(qty_text, f"Item {i+1} Quantity", allow_zero=False)
                if not qty_valid:
                    validations.append((False, qty_msg))
                else:
                    items.append({'material_id': mid, 'quantity_requested': qty_val})
                    has_valid_item = True
            elif mid and not qty_text:
                validations.append((False, f"Item {i+1}: Quantity is required."))
            elif not mid and qty_text:
                validations.append((False, f"Item {i+1}: Please select a material."))

        if not has_valid_item:
            validations.append((False, "Add at least one material with a valid quantity."))

        all_valid, error_msg = collect_errors(validations)
        if not all_valid:
            QMessageBox.warning(self, "Validation Error", error_msg)
            return

        # Check stock availability
        for it in items:
            mat = InventoryService.get_material_details(it['material_id'])
            if it['quantity_requested'] > mat.quantity:
                QMessageBox.warning(self, "Insufficient Stock", 
                                  f"Insufficient stock for {mat.name}.\n"
                                  f"Available: {mat.quantity} {mat.unit}\n"
                                  f"Requested: {it['quantity_requested']} {mat.unit}")
                return

        # Check for zero-price items and warn
        zero_price_items = []
        for it in items:
            mat = InventoryService.get_material_details(it['material_id'])
            if mat and mat.unit_cost == 0:
                zero_price_items.append(mat.name)
        
        if zero_price_items:
            names = ", ".join(zero_price_items)
            confirm = QMessageBox.question(
                self, "Zero Price Warning",
                f"The following items have ₹0 unit cost:\n{names}\n\n"
                "The invoice will show ₹0 for these items. Continue anyway?",
                QMessageBox.Yes | QMessageBox.No
            )
            if confirm != QMessageBox.Yes:
                return
            
        try:
            if hasattr(self, 'editing_invoice_id') and self.editing_invoice_id:
                # Update existing DRAFT
                from services.invoice_service import InvoiceService
                from database.models import MRS, MRSItem, Invoice, db
                
                with db.atomic():
                    invoice = Invoice.get_by_id(self.editing_invoice_id)
                    mrs = invoice.mrs
                    mrs.batch_id = batch_id
                    mrs.save()
                    
                    # Update Client Info
                    invoice.client_name = client_name
                    invoice.client_address = client_address
                    invoice.client_gstin = client_gstin
                    invoice.due_date = due_date
                    
                    # Update Items (Simplified: Delete and re-create)
                    MRSItem.delete().where(MRSItem.mrs == mrs).execute()
                    total_amount = 0
                    for it in items:
                        mat = InventoryService.get_material_details(it['material_id'])
                        MRSItem.create(
                            mrs=mrs,
                            material=it['material_id'],
                            quantity_requested=it['quantity_requested']
                        )
                        total_amount += it['quantity_requested'] * mat.unit_cost
                    
                    gst_rate = invoice.gst_percentage / 100.0
                    invoice.total_amount = total_amount
                    invoice.tax_amount = total_amount * gst_rate
                    invoice.grand_total = total_amount + invoice.tax_amount
                    invoice.save()
                
                QMessageBox.information(self, "Success", "Draft Invoice Updated Successfully")
                self.editing_invoice_id = None
                self.btn_submit_invoice.setText("Generate Invoice")
            else:
                # Create NEW DRAFT
                mrs = MRSService.create_mrs(self.user.id, batch_id, items)
                # DO NOT ISSUE YET (Keep as DRAFT)
                # MRSService.issue_mrs(mrs.id, self.user.id, issue_items)
            
                QMessageBox.information(self, "Success", "Draft Invoice Created Successfully")
            
            # Clean up form
            self.reset_form()
            self.editing_invoice_id = None
            self.btn_submit_invoice.setText("Generate Invoice")
            self.btn_cancel_edit.setText("Clear Form")
            
            if generate_invoice:
                self.show_invoice_dialog(mrs, client_name=client_name, client_address=client_address, client_gstin=client_gstin, due_date=due_date)
            
            # Switch to History tab
            self.tabs.setCurrentIndex(1)
            self.load_invoice_history()
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create request: {str(e)}")
