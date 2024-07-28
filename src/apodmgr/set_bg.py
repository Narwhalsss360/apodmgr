import os
from typing import Callable
from pathlib import Path


def set_bg_nt(image: Path) -> None:
    import ctypes
    ctypes.windll.user32.SystemParametersInfoW(20, 0, str(image.absolute()), 0)


OS_SETTERS: dict[str, Callable[[Path], None]] = {
    'nt': set_bg_nt
}


def set_bg(image: Path) -> None:
    if os.name not in OS_SETTERS:
        raise SystemError(f'{set_bg} is not supported on OS {os.name}')
    OS_SETTERS[os.name](image)
