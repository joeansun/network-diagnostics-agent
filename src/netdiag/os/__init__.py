import platform

from .base import OSAdapter
from .windows import WindowsOSAdapter


def get_os_adapter() -> OSAdapter:
    system = platform.system()

    if system == "Windows":
        return WindowsOSAdapter()
    else:
        raise RuntimeError(f"Unsupported OS: {system}")


all = ["OSAdapter", "get_os_adapter"]
