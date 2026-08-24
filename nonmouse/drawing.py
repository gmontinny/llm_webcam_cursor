import cv2
import numpy as np

HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (17, 18), (18, 19), (19, 20),
    (0, 17),
]


def draw_landmarks(image: np.ndarray, landmarks: list, image_width: int, image_height: int) -> None:
    pts = [(int(lm.x * image_width), int(lm.y * image_height)) for lm in landmarks]
    for a, b in HAND_CONNECTIONS:
        cv2.line(image, pts[a], pts[b], (0, 255, 0), 2)
    for pt in pts:
        cv2.circle(image, pt, 4, (255, 255, 255), -1)


def draw_circle(image: np.ndarray, x: float, y: float, radius: int, color: tuple) -> None:
    cv2.circle(image, (int(x), int(y)), radius, color, thickness=5, lineType=cv2.LINE_8)
