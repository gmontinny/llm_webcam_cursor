import ctypes
import platform

_PLATFORM = platform.system()


def get_virtual_screen() -> tuple[int, int, int, int]:
    """Retorna (x_origin, y_origin, largura, altura) da area virtual de todos os monitores."""
    if _PLATFORM == "Windows":
        gm = ctypes.windll.user32.GetSystemMetrics
        return (gm(76), gm(77), gm(78), gm(79))
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        w, h = root.winfo_screenwidth(), root.winfo_screenheight()
        root.destroy()
        return (0, 0, w, h)
    except Exception:
        return (0, 0, 1920, 1080)
