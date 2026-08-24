"""
Exemplo 2 — pygrabber (DirectShow nativo Windows)

Captura frames diretamente via COM/DirectShow sem depender do OpenCV.
Entrega frames como numpy array RGB — compativel direto com mediapipe.

Dependencias: pygrabber, comtypes
"""
import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cv2
import numpy as np
from pygrabber.dshow_graph import FilterGraph

from nonmouse.detector import HandDetector
from nonmouse.gesture import GestureController


class PyGrabberCamera:
    """Captura frames via DirectShow usando pygrabber."""

    def __init__(self, index: int = 0):
        self._frame: np.ndarray | None = None
        self._lock = threading.Lock()

        self._graph = FilterGraph()
        devices = self._graph.get_input_devices()
        if not devices:
            raise RuntimeError("Nenhuma camera encontrada via DirectShow.")
        if index >= len(devices):
            raise RuntimeError(f"Camera {index} nao encontrada. Disponiveis: {devices}")

        print(f"[pygrabber] Usando: {devices[index]}")
        self._graph.add_video_input_device(index)
        self._graph.add_sample_grabber(self._on_frame)
        self._graph.add_null_render()
        self._graph.prepare_preview_graph()
        self._graph.run()

    def _on_frame(self, frame: np.ndarray) -> None:
        with self._lock:
            self._frame = frame.copy()

    def grab(self) -> None:
        """Solicita captura do proximo frame (pygrabber e one-shot)."""
        self._graph.grab_frame()

    def read(self) -> tuple[bool, np.ndarray | None]:
        with self._lock:
            if self._frame is None:
                return False, None
            return True, self._frame.copy()

    def stop(self) -> None:
        self._graph.stop()


def run(camera_index: int = 0) -> None:
    cam = PyGrabberCamera(camera_index)
    detector = HandDetector(mode="VIDEO")
    controller = GestureController(sensitivity=3.0)
    ts = 0

    print(f"[pygrabber] Camera {camera_index} aberta. Pressione ESC para sair.")

    try:
        while True:
            cam.grab()
            ok, frame_rgb = cam.read()
            if not ok or frame_rgb is None:
                continue

            # pygrabber entrega RGB — converte para exibicao no OpenCV (BGR)
            frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
            frame_bgr = cv2.flip(frame_bgr, 1)
            h, w = frame_bgr.shape[:2]

            # mediapipe recebe o mesmo frame ja corrigido
            frame_rgb_flipped = np.ascontiguousarray(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB))
            ts += 33
            hands = detector.detect(frame_rgb_flipped, timestamp_ms=ts)
            if hands:
                controller.process(hands[0], frame_bgr, w, h)
            else:
                controller.reset()

            cv2.imshow("NonMouse — pygrabber", frame_bgr)
            if cv2.waitKey(1) & 0xFF == 27:
                break
    finally:
        cam.stop()
        detector.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    index = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    run(index)
