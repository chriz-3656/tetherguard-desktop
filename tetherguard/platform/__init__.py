def get_platform_adapter():
    import sys
    if sys.platform == 'win32':
        from .windows import WindowsAdapter
        return WindowsAdapter()
    elif sys.platform.startswith('linux'):
        from .linux import LinuxAdapter
        return LinuxAdapter()
    else:
        raise NotImplementedError("Platform not supported")
