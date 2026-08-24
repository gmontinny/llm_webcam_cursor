# Exemplos alternativos de captura de webcam

Cada exemplo implementa o mesmo pipeline do NonMouse usando uma biblioteca diferente para captura de frames.

O pipeline e identico em todos:

```
Captura de frame  →  mediapipe (deteccao de mao)  →  pynput (controle do mouse)
```

Apenas a camada de captura muda.

---

## Como executar

```sh
# da raiz do projeto
python examples/example_opencv.py       # OpenCV (padrao)
python examples/example_pygrabber.py    # pygrabber (DirectShow nativo)
python examples/example_pyav.py         # PyAV (FFmpeg)
python examples/example_vidgear.py      # vidgear
python examples/example_imageio.py      # imageio + ffmpeg

# para usar camera 1 em qualquer exemplo
python examples/example_opencv.py 1
```

Pressione **ESC** para encerrar qualquer exemplo.

---

## Comparativo rapido

| Exemplo | Biblioteca | Backend | Threading | Windows 11 | Complexidade |
|---|---|---|---|---|---|
| `example_opencv.py` | opencv-python | DSHOW/MSMF/ANY | manual | ✅ nativo | baixa |
| `example_pygrabber.py` | pygrabber | DirectShow COM | callback | ✅ nativo | media |
| `example_pyav.py` | av (PyAV) | FFmpeg/dshow | nao | ✅ via FFmpeg | alta |
| `example_vidgear.py` | vidgear | OpenCV interno | embutido | ✅ | baixa |
| `example_imageio.py` | imageio-ffmpeg | FFmpeg | nao | ⚠️ parcial | media |

---

## Detalhes de cada abordagem

---

### 1. OpenCV — `example_opencv.py`

A abordagem padrao e mais utilizada para captura de webcam em Python.

Documentacao: https://docs.opencv.org/4.x/

**Como funciona:**
Usa `cv2.VideoCapture` com fallback automatico de backend (`DSHOW → MSMF → ANY`). O modulo `nonmouse/camera.py` testa cada backend ate obter um frame valido, garantindo compatibilidade com qualquer driver no Windows 11.

**Vantagens:**
- Biblioteca mais testada e documentada para visao computacional
- Fallback automatico de backend resolve problemas de driver no Windows 11
- Integrado nativamente com numpy — frames ja chegam como array BGR
- Suporte a ajuste de resolucao, FPS e propriedades da camera via `CAP_PROP_*`
- Comunidade enorme, facil de encontrar solucoes para problemas

**Desvantagens:**
- Pacote pesado (~45 MB) para quem precisa apenas de captura
- Sem threading embutido — necessario implementar manualmente para evitar bloqueio
- Em alguns drivers do Windows 11, `isOpened()` retorna `True` mas frames chegam pretos

**Quando usar:**
- Projetos novos que precisam de captura + processamento de imagem
- Quando compatibilidade maxima com Windows e prioridade
- Quando ja se usa OpenCV para outras operacoes (resize, flip, desenho)

---

### 2. pygrabber — `example_pygrabber.py`

Acesso direto ao DirectShow do Windows via interface COM, sem passar pelo OpenCV.

Documentacao pygrabber: https://github.com/andreaschiavinato/python_grabber
Documentacao DirectShow: https://learn.microsoft.com/en-us/windows/win32/directshow/directshow

**Como funciona:**
Usa `FilterGraph` do DirectShow para montar um pipeline de captura. Os frames chegam via callback em uma thread separada como numpy array RGB. E a unica biblioteca desta lista que elimina completamente o OpenCV da captura.

**Vantagens:**
- Acesso nativo ao DirectShow — mesmo backend que o Windows usa internamente
- Frames entregues via callback em thread separada, sem necessidade de loop de leitura
- Entrega frames em RGB — compativel direto com mediapipe sem conversao extra
- Pacote leve (~24 KB)
- Elimina dependencia do OpenCV para captura (OpenCV fica so para exibicao)

**Desvantagens:**
- Funciona apenas no Windows — sem suporte a Linux ou macOS
- Pouco mantido (ultima versao 0.2)
- API de baixo nivel — requer entender o modelo de FilterGraph do DirectShow
- `grab_frame()` e one-shot — precisa ser chamado a cada iteracao do loop
- O modo `IMAGE` do mediapipe gera warning `NORM_RECT without IMAGE_DIMENSIONS`; usar modo `VIDEO` com `timestamp_ms` incremental
- Sem controle facil de resolucao ou FPS via API Python

**Quando usar:**
- Projetos exclusivos para Windows que precisam minimizar dependencias
- Quando se quer eliminar o OpenCV completamente da captura
- Integracao com outros componentes COM/DirectShow do Windows

---

### 3. PyAV — `example_pyav.py`

Bindings Python completos para o FFmpeg, a biblioteca de multimedia mais poderosa disponivel.

Documentacao PyAV: https://pyav.org/docs/stable/
Documentacao FFmpeg: https://ffmpeg.org/documentation.html

**Como funciona:**
Abre o dispositivo de camera via FFmpeg usando o formato `dshow` (DirectShow) no Windows. Decodifica os frames quadro a quadro via `container.demux()`, entregando objetos `av.VideoFrame` que podem ser convertidos para numpy.

**Vantagens:**
- FFmpeg e o codec mais robusto e completo disponivel
- Controle total sobre formato de pixel, resolucao, FPS e codec
- Suporte a praticamente qualquer fonte de video (arquivo, stream RTSP, webcam, captura de tela)
- Multiplataforma — funciona no Windows, Linux e macOS
- Ideal para pipelines que precisam gravar ou transcodificar video simultaneamente

**Desvantagens:**
- API mais complexa e verbosa que as outras opcoes
- Pacote pesado (~27 MB)
- No Windows, requer o nome exato do dispositivo no formato DirectShow (`video=<nome>`)
- Sem threading embutido — o loop de demux e sincrono
- Latencia ligeiramente maior que OpenCV em captura ao vivo

**Quando usar:**
- Projetos que precisam capturar e gravar video simultaneamente
- Quando se precisa de controle fino sobre codec e formato
- Pipelines que consomem streams de rede (RTSP, HLS) alem de webcam
- Substituicao do OpenCV em ambientes onde FFmpeg ja e dependencia

---

### 4. vidgear — `example_vidgear.py`

Biblioteca de alto nivel que envolve o OpenCV com threading embutido e API simplificada.

Documentacao: https://abhitronix.github.io/vidgear/latest/

**Como funciona:**
`CamGear` abre a camera via OpenCV internamente e gerencia uma thread de captura automaticamente. A leitura de frames e feita com `stream.read()` sem necessidade de implementar lock ou thread manualmente.

**Vantagens:**
- API extremamente simples — tres linhas para abrir, ler e fechar
- Threading embutido sem necessidade de implementar `ThreadedCamera` manualmente
- Suporte a multiplas fontes: webcam, arquivo, YouTube, stream de rede
- Boa documentacao e manutencao ativa
- Compativel com todo o ecossistema OpenCV

**Desvantagens:**
- Depende do OpenCV internamente — nao elimina essa dependencia
- Pacote com muitas dependencias transitivas (requests, tqdm, colorlog, cython)
- Menos controle sobre backend de captura que o OpenCV direto
- Overhead adicional da camada de abstracao

**Quando usar:**
- Prototipagem rapida onde simplicidade e mais importante que controle
- Projetos que precisam alternar entre webcam, arquivo e stream sem mudar o codigo
- Quando se quer evitar implementar threading de captura manualmente

---

### 5. imageio + imageio-ffmpeg — `example_imageio.py`

Captura via FFmpeg usando a API de leitura de imagens do imageio.

Documentacao imageio: https://imageio.readthedocs.io/
Documentacao imageio-ffmpeg: https://github.com/imageio/imageio-ffmpeg

**Como funciona:**
`iio.imiter()` abre um iterador de frames sobre o dispositivo de video usando FFmpeg como backend. Cada iteracao entrega um frame como numpy array RGB.

**Vantagens:**
- API muito simples baseada em iterador Python
- Mesmo codigo funciona para webcam, arquivo de video e imagens
- FFmpeg como backend garante suporte amplo a formatos
- Leve para projetos que ja usam imageio para outras finalidades

**Desvantagens:**
- Suporte a webcam no Windows e parcial — depende do FFmpeg instalado no PATH do sistema
- A sintaxe `<video0>` funciona bem no Linux/macOS mas tem limitacoes no Windows
- Sem threading embutido — iterador e sincrono e pode causar bloqueio no loop principal
- Latencia maior que OpenCV para captura ao vivo
- Menos controle sobre propriedades da camera (resolucao, FPS)

**Quando usar:**
- Projetos multiplataforma onde Linux/macOS e o ambiente principal
- Pipelines que ja processam arquivos de video e imagens com imageio
- Prototipagem rapida em ambientes onde FFmpeg esta disponivel no PATH
