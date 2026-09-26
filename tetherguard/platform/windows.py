class WindowsAdapter:
    def lock_workstation(self):
        import ctypes
        ctypes.windll.user32.LockWorkStation()

    def shutdown(self):
        import os
        os.system("shutdown /s /t 1")
