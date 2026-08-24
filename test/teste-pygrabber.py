"""
Teste de captura via pygrabber (DirectShow nativo Windows).
Pressione 'q' para sair.
"""
import sys
import threading

import cv2
import numpy as np
from pygrabber.dshow_graph import FilterGraph


def main(camera_index: int = 0) -> None:
    frame_data: dict = {"frame": None, "lock": threading.Lock()}

    def on_frame(frame: np.ndarray) -> None:
        with frame_data["lock"]:
            frame_data["frame"] = frame.copy()

    graph = FilterGraph()
    devices = graph.get_input_devices()

    if not devices:
        print("Nenhuma camera encontrada via DirectShow.")
        sys.exit(1)

    print(f"Cameras disponiveis: {devices}")
    print(f"Usando: {devices[camera_index]}")

    graph.add_video_input_device(camera_index)
    graph.add_sample_grabber(on_frame)
    graph.add_null_render()
    graph.prepare_preview_graph()
    graph.run()

    print("Camera aberta. Pressione 'q' para sair.")

    try:
        while True:
            graph.grab_frame()  # solicita o proximo frame
            with frame_data["lock"]:
                frame = frame_data["frame"]

            if frame is not None:
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                cv2.imshow("Teste pygrabber", frame_bgr)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        graph.stop()
        cv2.destroyAllWindows()
        print("Encerrado.")


if __name__ == "__main__":
    index = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    main(index)
