class WindowsAdapter:
    def _show_safe_mode_alert(self, action_name):
        from PySide6.QtWidgets import QApplication, QLabel
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QFont
        
        app = QApplication.instance()
        if not app:
            print(f"SAFE MODE: Prevented actual {action_name}")
            return
            
        alert = QLabel(f"SECURITY BREACH DETECTED\n\nSYSTEM {action_name} INITIATED\n\n(Click anywhere to dismiss - Hackathon Safe Mode)")
        alert.setAlignment(Qt.AlignCenter)
        alert.setStyleSheet("background-color: #8c1c13; color: white; font-weight: bold; font-family: monospace;")
        alert.setFont(QFont("Courier", 24, QFont.Bold))
        alert.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        
        # Make it full screen
        screen = app.primaryScreen().geometry()
        alert.setGeometry(screen)
        
        # Close on click
        alert.mousePressEvent = lambda e: alert.close()
        
        alert.show()
        
        # Keep a reference so it doesn't get garbage collected
        if not hasattr(app, 'alerts'):
            app.alerts = []
        app.alerts.append(alert)
        print(f"SAFE MODE: Displayed {action_name} alert instead of actual system execution.")

    def lock_workstation(self):
        # Replaced actual ctypes.windll.user32.LockWorkStation() with Safe Mode UI
        self._show_safe_mode_alert("LOCK")

    def shutdown(self):
        # Replaced actual os.system("shutdown /s /t 1") with Safe Mode UI
        self._show_safe_mode_alert("SHUTDOWN")

