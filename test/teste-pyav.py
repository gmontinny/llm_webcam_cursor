"""
Teste de captura via PyAV (FFmpeg bindings).
Pressione 'q' para sair.
"""
import sys

import av
import cv2
from pygrabber.dshow_graph import FilterGraph


def _device_name(index: int) -> str:
    devices = FilterGraph().get_input_devices()
    if not devices or index >= len(devices):
        raise RuntimeError(f"Camera {index} nao encontrada.")
    return devices[index]


def main(camera_index: int = 0) -> None:
    name = _device_name(camera_index)
    print(f"Usando: {name}")

    try:
        container = av.open(
            f"video={name}",
            format="dshow",
            options={"video_size": "640x480", "framerate": "30"},
        )
    except av.AVError as e:
        print(f"Erro ao abrir camera: {e}")
        sys.exit(1)

    stream = container.streams.video[0]
    print(f"Camera aberta. Codec: {stream.codec_context.name} | "
          f"Resolucao: {stream.width}x{stream.height}")
    print("Pressione 'q' para sair.")

    try:
        for packet in container.demux(stream):
            for frame in packet.decode():
                img = frame.to_ndarray(format="bgr24")
                cv2.imshow("Teste PyAV", img)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    return
    except KeyboardInterrupt:
        pass
    finally:
        container.close()
        cv2.destroyAllWindows()
        print("Encerrado.")


if __name__ == "__main__":
    index = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    main(index)
