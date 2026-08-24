"""
Exemplo 1 — OpenCV (abordagem atual do projeto)

Captura frames via DirectShow/MSMF com fallback automatico de backend.
É a abordagem mais comum e compativel com Windows 11.

Dependencias: opencv-python
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cv2

from nonmouse.camera import open_camera
from nonmouse.detector import HandDetector
from nonmouse.gesture import GestureController


def run(camera_index: int = 0) -> None:
    cap = open_camera(camera_index)
    detector = HandDetector(mode="IMAGE")
    controller = GestureController(sensitivity=3.0)

    print(f"[opencv] Camera {camera_index} aberta. Pressione ESC para sair.")

    try:
        while cap.isOpened():
            ok, frame = cap.read()
            if not ok or frame is None:
                continue

            frame = cv2.flip(frame, 1)
            h, w = frame.shape[:2]
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            hands = detector.detect(rgb)
            if hands:
                controller.process(hands[0], frame, w, h)
            else:
                controller.reset()

            cv2.imshow("NonMouse — OpenCV", frame)
            if cv2.waitKey(1) & 0xFF == 27:
                break
    finally:
        cap.release()
        detector.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    index = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    run(index)
