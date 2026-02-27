from database.models import User
import hashlib

class AuthService:
    def __init__(self):
        self.current_user = None

    def login(self, username, password):
        try:
            # Simple password check for demo purposes
            # In production, use bcrypt or similar
            user = User.get(User.username == username)
            
            # For this project, passwords seem to be stored as plain strings in the seed
            if user.password == password:
                self.current_user = user
                return user
            else:
                return None
        except User.DoesNotExist:
            return None

    def logout(self):
        self.current_user = None

    def is_authenticated(self):
        return self.current_user is not None
