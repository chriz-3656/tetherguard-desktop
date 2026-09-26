from tetherguard.platform import get_platform_adapter

class ShutdownResponder:
    def execute(self):
        print("Executing workstation shutdown...")
        try:
            adapter = get_platform_adapter()
            adapter.shutdown()
        except Exception as e:
            print(f"Shutdown failed: {e}")
