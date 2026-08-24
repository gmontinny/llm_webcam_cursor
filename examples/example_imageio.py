"""
Exemplo 5 — imageio + imageio-ffmpeg

AVISO: o imageio nao suporta captura de webcam no Windows via plugin pyav.
O URI `video=<nome>` e interpretado como caminho de arquivo local.

No Linux/macOS, use: iio.imiter("<video0>", plugin="pyav")
No Windows, use o example_pyav.py que tem suporte completo via dshow.

Dependencias: imageio, imageio-ffmpeg
"""
import sys

print(
    "[imageio] Captura de webcam via imageio nao e suportada no Windows.\n"
    "Use: python examples/example_pyav.py"
)
sys.exit(1)
