from PySide6.QtWidgets import QFrame, QVBoxLayout

class CardWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        self.setProperty("class", "Card")
        self.setStyleSheet("Card { background-color: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 16px; }")
        self.card_layout = QVBoxLayout(self)
        self.card_layout.setContentsMargins(20, 20, 20, 20)
        self.card_layout.setSpacing(15)
        self.layout = self.card_layout # Maintain compatibility

    def addWidget(self, widget):
        self.layout.addWidget(widget)

    def addLayout(self, layout):
        self.layout.addLayout(layout)
