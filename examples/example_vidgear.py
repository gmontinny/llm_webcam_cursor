"""
Exemplo 4 — vidgear (CamGear)

API de alto nivel com threading embutido sobre OpenCV.
Mais simples que gerenciar ThreadedCamera manualmente.

Dependencias: vidgear
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cv2
from vidgear.gears import CamGear

from nonmouse.detector import HandDetector
from nonmouse.gesture import GestureController


def run(camera_index: int = 0) -> None:
    stream = CamGear(source=camera_index, logging=False).start()
    detector = HandDetector(mode="IMAGE")
    controller = GestureController(sensitivity=3.0)

    print(f"[vidgear] Camera {camera_index} aberta. Pressione ESC para sair.")

    try:
        while True:
            frame = stream.read()
            if frame is None:
                continue

            frame = cv2.flip(frame, 1)
            h, w = frame.shape[:2]
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            hands = detector.detect(rgb)
            if hands:
                controller.process(hands[0], frame, w, h)
            else:
                controller.reset()

            cv2.imshow("NonMouse — vidgear", frame)
            if cv2.waitKey(1) & 0xFF == 27:
                break
    finally:
        stream.stop()
        detector.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    index = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    run(index)
