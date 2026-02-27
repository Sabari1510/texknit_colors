from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt

class StatusBadge(QLabel):
    def __init__(self, text, status='neutral', parent=None):
        super().__init__(text, parent)
        self.set_status(status)
        self.setAlignment(Qt.AlignCenter)
        self.setContentsMargins(8, 4, 8, 4)
        self.setFixedHeight(24)

    def set_status(self, status):
        # status: success, warning, critical, neutral
        # Tailored for Beige/Light theme
        styles = {
            'success': "background-color: #DCFCE7; color: #166534; border-radius: 12px; font-size: 11px; font-weight: 700; padding: 4px 12px; border: 1px solid #BBF7D0;",
            'warning': "background-color: #FEF3C7; color: #92400E; border-radius: 12px; font-size: 11px; font-weight: 700; padding: 4px 12px; border: 1px solid #FDE68A;",
            'critical': "background-color: #FEE2E2; color: #991B1B; border-radius: 12px; font-size: 11px; font-weight: 700; padding: 4px 12px; border: 1px solid #FECACA;",
            'neutral': "background-color: #F1F5F9; color: #475569; border-radius: 12px; font-size: 11px; font-weight: 700; padding: 4px 12px; border: 1px solid #E2E8F0;"
        }
        self.setStyleSheet(styles.get(status, styles['neutral']))
