"""
Exemplo 5 — imageio + imageio-ffmpeg

Captura via FFmpeg usando a API imageio.
No Windows, o dispositivo e referenciado pelo nome retornado pelo sistema.

Dependencias: imageio, imageio-ffmpeg
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cv2
import imageio.v3 as iio
import numpy as np

from nonmouse.detector import HandDetector
from nonmouse.gesture import GestureController


def get_device_name(index: int = 0) -> str:
    """Retorna o nome do dispositivo de video para uso com imageio no Windows."""
    devices = iio.immeta("<video0>", plugin="pyav", exclude_applied=False)
    # fallback: usa indice direto como string no formato FFmpeg/dshow
    return f"video={index}"


def run(camera_index: int = 0) -> None:
    # No Windows com imageio-ffmpeg, o dispositivo e aberto via indice
    device = f"<video{camera_index}>"
    detector = HandDetector(mode="IMAGE")
    controller = GestureController(sensitivity=3.0)

    print(f"[imageio] Abrindo {device}. Pressione ESC para sair.")

    try:
        for frame_rgb in iio.imiter(device, plugin="pyav"):
            frame_rgb = np.asarray(frame_rgb)
            if frame_rgb.ndim != 3:
                continue

            frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
            frame_bgr = cv2.flip(frame_bgr, 1)
            h, w = frame_bgr.shape[:2]

            frame_rgb_flipped = cv2.flip(frame_rgb, 1)
            hands = detector.detect(frame_rgb_flipped)
            if hands:
                controller.process(hands[0], frame_bgr, w, h)
            else:
                controller.reset()

            cv2.imshow("NonMouse — imageio", frame_bgr)
            if cv2.waitKey(1) & 0xFF == 27:
                break
    except Exception as e:
        print(f"[imageio] Erro: {e}")
        print("Dica: tente instalar ffmpeg no PATH do sistema ou use outro exemplo.")
    finally:
        detector.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    index = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    run(index)
