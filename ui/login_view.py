from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QFrame, QSpacerItem, QSizePolicy)
from PySide6.QtCore import Qt, Signal

class LoginView(QWidget):
    login_success = Signal(object) # Emissions user object
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login - TEXKNIT COLORS")
        self.resize(400, 500)
        
        # Load Styles
        with open("ui/styles.qss", "r") as f:
            self.setStyleSheet(f.read())
            
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        # Background Gradient simulation through layout spacing if needed
        # but the QSS handles the background fine.
        
        # Card Container
        from ui.components.card_widget import CardWidget
        card = CardWidget()
        card.setFixedSize(380, 480)
        card.layout.setContentsMargins(40, 50, 40, 50)
        card.layout.setSpacing(10)
        
        # Header
        title = QLabel("Welcome Back")
        title.setStyleSheet("font-size: 28px; font-weight: 800; color: #1E293B; margin-bottom: 4px;")
        title.setAlignment(Qt.AlignCenter)
        
        subtitle = QLabel("TEXKNIT COLORS MANAGEMENT")
        subtitle.setObjectName("SubtitleLabel")
        subtitle.setStyleSheet("font-weight: 600; text-transform: uppercase; font-size: 10px; letter-spacing: 1px;")
        subtitle.setAlignment(Qt.AlignCenter)
        
        # Form Fields
        form_layout = QVBoxLayout()
        form_layout.setSpacing(15)
        form_layout.addSpacing(20)
        
        self.username = QLineEdit()
        self.username.setPlaceholderText("Username")
        self.username.setMinimumHeight(45)
        
        self.password = QLineEdit()
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setMinimumHeight(45)
        
        self.btn_login = QPushButton("Sign In")
        self.btn_login.setProperty("class", "PrimaryButton")
        self.btn_login.setCursor(Qt.PointingHandCursor)
        self.btn_login.setMinimumHeight(45)
        
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #f87171; font-size: 11px; font-weight: 600;")
        self.error_label.setAlignment(Qt.AlignCenter)
        
        form_layout.addWidget(self.username)
        form_layout.addWidget(self.password)
        form_layout.addWidget(self.error_label)
        form_layout.addSpacing(10)
        form_layout.addWidget(self.btn_login)
        
        # Assemble Card
        card.layout.addWidget(title)
        card.layout.addWidget(subtitle)
        card.layout.addStretch()
        card.layout.addLayout(form_layout)
        card.layout.addStretch()
        
        layout.addWidget(card)

    def set_error(self, message):
        self.error_label.setText(message)
