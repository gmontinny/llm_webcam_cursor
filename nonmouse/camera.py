import cv2
import platform
import threading

_PLATFORM = platform.system()
_WIN_BACKENDS = [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY]
_BACKEND_NAMES = {cv2.CAP_DSHOW: "DSHOW", cv2.CAP_MSMF: "MSMF", cv2.CAP_ANY: "ANY"}


def open_camera(index: int, width: int = 640, height: int = 480) -> cv2.VideoCapture:
    """Abre a câmera tentando múltiplos backends até obter um frame válido."""
    backends = _WIN_BACKENDS if _PLATFORM == "Windows" else [cv2.CAP_ANY]
    for backend in backends:
        cap = cv2.VideoCapture(index, backend)
        if cap.isOpened():
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            ret, _ = cap.read()
            if ret:
                return cap
            cap.release()
    raise RuntimeError(
        f"Nao foi possivel abrir a camera {index} com nenhum backend disponivel.\n"
        "Execute list_camera.py para ver cameras detectadas."
    )


def list_cameras(max_index: int = 5) -> list[dict]:
    """Retorna lista de cameras disponiveis com backend, resolucao e FPS."""
    backends = _WIN_BACKENDS if _PLATFORM == "Windows" else [cv2.CAP_ANY]
    found = []
    for idx in range(max_index):
        for backend in backends:
            cap = cv2.VideoCapture(idx, backend)
            if cap.isOpened():
                ret, _ = cap.read()
                if ret:
                    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    fps = cap.get(cv2.CAP_PROP_FPS)
                    found.append({
                        "index": idx,
                        "backend": _BACKEND_NAMES.get(backend, str(backend)),
                        "res": f"{w}x{h}",
                        "fps": fps,
                    })
                    cap.release()
                    break
                cap.release()
    return found


class ThreadedCamera:
    """Captura frames em thread separada para evitar bloqueio no loop principal."""

    def __init__(self, index: int = 0, width: int = 640, height: int = 480):
        self._cap = open_camera(index, width, height)
        self._grabbed, self._frame = self._cap.read()
        self._lock = threading.Lock()
        self._running = False
        self._thread: threading.Thread | None = None

    def start(self) -> "ThreadedCamera":
        if self._running:
            return self
        self._running = True
        self._thread = threading.Thread(target=self._update, daemon=True)
        self._thread.start()
        return self

    def _update(self) -> None:
        while self._running:
            grabbed, frame = self._cap.read()
            with self._lock:
                self._grabbed = grabbed
                self._frame = frame

    def read(self) -> tuple[bool, cv2.typing.MatLike | None]:
        with self._lock:
            if not self._grabbed or self._frame is None:
                return False, None
            return True, self._frame.copy()

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join()
        self._cap.release()
