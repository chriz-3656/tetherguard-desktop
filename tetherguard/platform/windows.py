class WindowsAdapter:
    def _show_safe_mode_alert(self, action_name):
        import ctypes
        import threading
        
        text = f"SECURITY BREACH DETECTED\n\nSYSTEM {action_name} INITIATED\n\n(Hackathon Safe Mode - Actual OS execution prevented)"
        title = f"TetherGuard - {action_name}"
        
        # 0x10 = MB_ICONERROR (Red X)
        # 0x40000 = MB_TOPMOST (Stays on top of all windows)
        # 0x1000 = MB_SYSTEMMODAL
        flags = 0x10 | 0x40000 | 0x1000
        
        # Run in a separate daemon thread so it doesn't block the WebSocket connection loop!
        def show_msg():
            ctypes.windll.user32.MessageBoxW(0, text, title, flags)
            
        threading.Thread(target=show_msg, daemon=True).start()
        print(f"SAFE MODE: Displayed {action_name} native alert instead of actual system execution.")

    def lock_workstation(self):
        import ctypes
        print("Executing actual workstation lock...")
        ctypes.windll.user32.LockWorkStation()

    def shutdown(self):
        # Replaced actual os.system("shutdown /s /t 1") with Safe Mode UI
        self._show_safe_mode_alert("SHUTDOWN")

