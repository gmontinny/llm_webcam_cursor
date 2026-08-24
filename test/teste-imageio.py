"""
Teste de captura via imageio + imageio-ffmpeg.

AVISO: imageio nao suporta captura de webcam no Windows.
No Windows, use: python test/teste-pyav.py
No Linux/macOS: iio.imiter("<video0>", plugin="pyav")
"""
import sys

print(
    "[imageio] Captura de webcam via imageio nao e suportada no Windows.\n"
    "Use: python test/teste-pyav.py"
)
sys.exit(1)
