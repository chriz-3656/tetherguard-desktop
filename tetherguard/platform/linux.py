class LinuxAdapter:
    def lock_workstation(self):
        import os
        os.system("loginctl lock-session")

    def shutdown(self):
        import os
        os.system("systemctl poweroff")
