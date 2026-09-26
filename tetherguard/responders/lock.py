from tetherguard.platform import get_platform_adapter

class LockResponder:
    def execute(self):
        print("Executing workstation lock...")
        try:
            adapter = get_platform_adapter()
            adapter.lock_workstation()
        except Exception as e:
            print(f"Lock failed: {e}")
