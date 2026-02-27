from PySide6.QtCore import QObject, Signal

class SignalRelay(QObject):
    """
    Central hub for global signals to ensure UI reactivity.
    Any part of the app can emit signals here, and others can listen.
    """
    # Emitted whenever any data in the database changes (Inventory, Suppliers, Consumers, etc.)
    data_changed = Signal()
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = SignalRelay()
        return cls._instance

# Singleton instance
relay = SignalRelay.get_instance()
