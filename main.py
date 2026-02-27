import sys
from PySide6.QtWidgets import QApplication
from database.models import initialize_db
from ui.login_view import LoginView
from ui.main_window import MainWindow
from services.auth_service import AuthService

class ConsultancyApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.auth_service = AuthService()
        
        # Initialize Database
        initialize_db()
        
        # Show Login
        self.show_login()

    def show_login(self):
        self.login_window = LoginView()
        self.login_window.btn_login.clicked.connect(self.handle_login)
        self.login_window.show()

    def handle_login(self):
        username = self.login_window.username.text()
        password = self.login_window.password.text()
        
        user = self.auth_service.login(username, password)
        if user:
            self.login_window.close()
            self.show_main_window(user)
        else:
            self.login_window.set_error("Invalid username or password")

    def show_main_window(self, user):
        self.main_window = MainWindow(user)
        self.main_window.show()

    def run(self):
        sys.exit(self.app.exec())

if __name__ == "__main__":
    app = ConsultancyApp()
    app.run()
