"""
Teste de captura via PyAV (FFmpeg bindings).
Pressione 'q' para sair.
"""
import sys

import av
import cv2


def list_dshow_devices() -> list[str]:
    """Lista dispositivos de video disponiveis via DirectShow."""
    devices = []
    try:
        container = av.open("list", format="dshow", options={"list_devices": "true"})
        container.close()
    except av.AVError as e:
        # FFmpeg imprime a lista no stderr mesmo com erro — capturamos o que temos
        for line in str(e).splitlines():
            if "video" in line.lower() and "@device" in line.lower():
                devices.append(line.strip())
    return devices


def main(camera_index: int = 0) -> None:
    # No Windows, PyAV/FFmpeg requer o nome do dispositivo DirectShow
    # Tenta abrir pelo indice usando o formato "video=<index>"
    device_name = f"video={camera_index}"

    print(f"Tentando abrir: {device_name} via FFmpeg/DirectShow...")

    try:
        container = av.open(
            device_name,
            format="dshow",
            options={"video_size": "640x480", "framerate": "30"},
        )
    except av.AVError as e:
        print(f"Erro ao abrir camera: {e}")
        print("Dica: use o nome exato do dispositivo, ex: 'video=Integrated Camera'")
        print("Execute list_camera.py para ver os dispositivos disponiveis.")
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
