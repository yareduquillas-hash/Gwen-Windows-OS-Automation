from __future__ import annotations

import sys

from .base import PlatformAdapter


def get_adapter() -> PlatformAdapter:
    if sys.platform == "win32":
        from .windows import WindowsAdapter
        return WindowsAdapter()
    from .linux import LinuxAdapter
    return LinuxAdapter()
