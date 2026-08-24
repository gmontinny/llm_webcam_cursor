"""
Teste de captura via vidgear (CamGear).
Pressione 'q' para sair.
"""
import sys

import cv2
from vidgear.gears import CamGear


def main(camera_index: int = 0) -> None:
    print(f"Abrindo camera {camera_index} via vidgear/CamGear...")

    stream = CamGear(source=camera_index, logging=False).start()

    # verifica se abriu corretamente
    frame = stream.read()
    if frame is None:
        print(f"Erro: nao foi possivel abrir a camera {camera_index}.")
        stream.stop()
        sys.exit(1)

    print(f"Camera aberta. Resolucao: {frame.shape[1]}x{frame.shape[0]}")
    print("Pressione 'q' para sair.")

    try:
        while True:
            frame = stream.read()
            if frame is None:
                print("Frame invalido recebido — encerrando.")
                break

            cv2.imshow("Teste vidgear", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        stream.stop()
        cv2.destroyAllWindows()
        print("Encerrado.")


if __name__ == "__main__":
    index = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    main(index)
