"""
Exemplo 3 — PyAV (bindings Python do FFmpeg)

Captura via FFmpeg com acesso direto ao dispositivo via DirectShow no Windows.
Oferece controle total sobre codec, resolucao e formato de pixel.

Dependencias: av (PyAV)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import av
import cv2
import numpy as np
from pygrabber.dshow_graph import FilterGraph

from nonmouse.detector import HandDetector
from nonmouse.gesture import GestureController


def _device_name(index: int) -> str:
    devices = FilterGraph().get_input_devices()
    if not devices or index >= len(devices):
        raise RuntimeError(f"Camera {index} nao encontrada.")
    return devices[index]


def open_av_camera(index: int = 0) -> av.container.InputContainer:
    """Abre camera via FFmpeg/DirectShow no Windows."""
    name = _device_name(index)
    print(f"[pyav] Usando: {name}")
    return av.open(
        f"video={name}",
        format="dshow",
        options={"video_size": "640x480", "framerate": "30"},
    )


def run(camera_index: int = 0) -> None:
    container = open_av_camera(camera_index)
    stream = container.streams.video[0]

    detector = HandDetector(mode="IMAGE")
    controller = GestureController(sensitivity=3.0)

    print(f"[pyav] Camera {camera_index} aberta via FFmpeg/DirectShow. Pressione ESC para sair.")

    try:
        for packet in container.demux(stream):
            for av_frame in packet.decode():
                # converte frame PyAV para numpy RGB
                frame_rgb: np.ndarray = av_frame.to_ndarray(format="rgb24")
                frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
                frame_bgr = cv2.flip(frame_bgr, 1)
                h, w = frame_bgr.shape[:2]

                frame_rgb_flipped = cv2.flip(frame_rgb, 1)
                hands = detector.detect(frame_rgb_flipped)
                if hands:
                    controller.process(hands[0], frame_bgr, w, h)
                else:
                    controller.reset()

                cv2.imshow("NonMouse — PyAV", frame_bgr)
                if cv2.waitKey(1) & 0xFF == 27:
                    return
    finally:
        container.close()
        detector.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    index = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    run(index)
