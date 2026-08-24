"""
Teste de captura via imageio + imageio-ffmpeg.
Pressione 'q' para sair.

Nota: no Windows, a captura via imageio depende do FFmpeg instalado no PATH
do sistema. Caso falhe, instale o FFmpeg em https://ffmpeg.org/download.html
e adicione ao PATH.
"""
import sys

import cv2
import imageio.v3 as iio
import numpy as np


def main(camera_index: int = 0) -> None:
    device = f"<video{camera_index}>"
    print(f"Tentando abrir {device} via imageio/FFmpeg...")

    try:
        frame_iter = iio.imiter(device, plugin="pyav")

        # testa primeiro frame antes de entrar no loop
        first = next(frame_iter, None)
        if first is None:
            print("Erro: nenhum frame recebido.")
            sys.exit(1)

        h, w = first.shape[:2]
        print(f"Camera aberta. Resolucao: {w}x{h}")
        print("Pressione 'q' para sair.")

        for frame_rgb in [first, *frame_iter]:
            frame_rgb = np.asarray(frame_rgb)
            if frame_rgb.ndim != 3:
                continue

            frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
            cv2.imshow("Teste imageio", frame_bgr)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    except Exception as e:
        print(f"Erro ao capturar: {e}")
        print("Dica: verifique se o FFmpeg esta instalado e no PATH do sistema.")
        print("Download: https://ffmpeg.org/download.html")
        sys.exit(1)
    finally:
        cv2.destroyAllWindows()
        print("Encerrado.")


if __name__ == "__main__":
    index = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    main(index)
