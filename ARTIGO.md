# NonMouse: Controle Touchless de Cursor com Visão Computacional em Tempo Real

---

## 1. Introdução

A evolução das interfaces homem-máquina (IHM / HCI — *Human-Computer Interaction*) tem buscado formas cada vez mais naturais, ergonômicas e acessíveis de interação com sistemas computacionais. Tradicionalmente, o mouse físico e o touchpad têm sido os métodos predominantes de controle de ponteiros em computadores desktop e notebooks. No entanto, o uso contínuo desses periféricos pode acarretar problemas ergonômicos (como lesões por esforço repetitivo — LER/DORT) e impor limitações de acessibilidade para indivíduos com restrições motoras nos membros superiores.

Além disso, cenários como apresentações interativas, manipulação de interfaces em telas grandes (Smart TVs), quiosques públicos e ambientes cirúrgicos demandam soluções *touchless* (sem contato físico), em que higiene e controle à distância são fatores determinantes.

O projeto **NonMouse** aborda essas necessidades ao transformar qualquer webcam convencional (integrada ou USB) em um sensor de rastreamento de alta precisão. Utilizando visão computacional moderna por meio da biblioteca **MediaPipe Tasks (Google)**, manipulação eficiente de matrizes com **NumPy** e **OpenCV**, e emulação de periféricos em nível de sistema operacional com **pynput**, o NonMouse mapeia coordenadas tridimensionais da mão humana diretamente para eventos de cursor (movimentação, clique esquerdo, clique duplo, clique direito, arraste e scroll).

---

## 2. Arquitetura do Sistema e Design Modular

O projeto foi refatorado para seguir uma arquitetura modular orientada ao princípio de separação de responsabilidades (SoC — *Separation of Concerns*). Essa abordagem garante manutenibilidade, testabilidade e extensibilidade para novos tipos de gestos ou dispositivos de captura.

```
webcam-cursor/
├── nonmouse/                  # Pacote central da aplicação
│   ├── __init__.py
│   ├── camera.py              # Captura de vídeo multi-backend e controle em thread
│   ├── detector.py            # Inferência neural via MediaPipe Hand Landmarker
│   ├── gesture.py             # Heurística geométrica e máquina de estados de gestos
│   ├── drawing.py             # Renderização de HUD e feedback visual dos marcos
│   └── screen.py              # Gerenciamento de coordenadas de telas e múltiplos monitores
├── models/
│   └── hand_landmarker.task   # Modelo de rede neural quantizado Float16 (Google MediaPipe)
├── examples/                  # Implementações comparativas com múltiplos backends de captura
├── test/                      # Testes de diagnóstico de hardware por biblioteca
├── app.py                     # Ponto de entrada com interface gráfica (Tkinter)
├── tv_mouse.py                # Modo CLI otimizado de baixa latência (Headless/Background)
├── list_camera.py             # Utilitário de diagnóstico e listagem de câmeras
└── requirements.txt           # Dependências validadas para Python 3.12.9
```

### 2.1 Fluxo de Dados e Pipeline em Tempo Real

O ciclo de vida do processamento segue um pipeline linear e assíncrono:

```
[Webcam Hardware]
       │
       ▼ (Frames BGR @ 640x480)
[ThreadedCamera (camera.py)] ── Captura desacoplada com Lock de sincronização
       │
       ▼ (Frame RGB)
[HandDetector (detector.py)] ── Inferência: 21 Landmarks tridimensionais normalizados
       │
       ▼ (Lista de Landmarks)
[GestureController (gesture.py)] ── Filtro de Média Móvel (Anti-Jitter)
       │                         ├── Invariância de Escala Anatômica
       │                         └── Máquina de Estados (Clicks, Drag, Scroll)
       ▼
[pynput Controller] ─────────────── Emissão de eventos nativos ao SO (Cursor/Mouse)
       │
       ▼
[Feedback Visual (drawing.py)] ──── Renderização de esqueleto e indicadores de estado
```

---

## 3. Pipeline de Visão Computacional e Detecção de Mão

O sistema de visão computacional baseia-se na API moderna **MediaPipe Tasks**, que implementa uma arquitetura em dois estágios:

1. **Palm Detector:** Localiza a palma da mão na imagem completa em tempo real.
2. **Hand Skeleton Landmarker:** Prediz 21 pontos-chave (*landmarks*) tridimensionais da mão ($x, y, z$).

### 3.1 Topologia dos 21 Pontos Anatômicos

Os pontos anatômicos extraídos pelo modelo são:

- **Ponto 0:** Punho (*Wrist*) — ponto fixo de referência.
- **Pontos 1–4:** Polegar (*Thumb*) — CMC, MCP, IP e ponta (`lm[4]`).
- **Pontos 5–8:** Dedo Indicador (*Index*) — MCP, PIP, DIP e ponta (`lm[8]`).
- **Pontos 9–12:** Dedo Médio (*Middle*) — MCP, PIP, DIP e ponta (`lm[12]`).
- **Pontos 13–16:** Dedo Anelar (*Ring*).
- **Pontos 17–20:** Dedo Mínimo (*Pinky*).

### 3.2 Implementação do Detector de Mãos

```python
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision
from dataclasses import dataclass

@dataclass
class Landmark:
    x: float
    y: float
    z: float = 0.0

class HandDetector:
    def __init__(self, mode: str = "IMAGE", confidence: float = 0.8):
        running_mode = (
            mp_vision.RunningMode.VIDEO
            if mode == "VIDEO"
            else mp_vision.RunningMode.IMAGE
        )
        options = mp_vision.HandLandmarkerOptions(
            base_options=mp_python.BaseOptions(model_asset_path=MODEL_PATH),
            running_mode=running_mode,
            num_hands=1,
            min_hand_detection_confidence=confidence,
            min_hand_presence_confidence=confidence,
            min_tracking_confidence=confidence,
        )
        self._detector = mp_vision.HandLandmarker.create_from_options(options)
        self._mode = mode

    def detect(self, frame_rgb, timestamp_ms: int = 0) -> list[list[Landmark]]:
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        if self._mode == "VIDEO":
            result = self._detector.detect_for_video(mp_image, timestamp_ms)
        else:
            result = self._detector.detect(mp_image)
        return [
            [Landmark(p.x, p.y, p.z) for p in hand]
            for hand in result.hand_landmarks
        ]
```

> **Nota:** O modo `VIDEO` com `timestamp_ms` incremental é obrigatório para backends assíncronos como pygrabber e imageio. O modo `IMAGE` gera o warning `NORM_RECT without IMAGE_DIMENSIONS` nesses contextos, pois o MediaPipe não consegue inferir as dimensões do frame sem o contexto temporal.

---

## 4. Algoritmos de Reconhecimento e Controle de Gestos

### 4.1 Invariância de Escala Anatômica

Um desafio crítico em interfaces baseadas em visão é a variação de escala decorrente da distância entre a mão e a câmera. Para neutralizar esse efeito, todas as distâncias de controle são normalizadas pela distância euclidiana entre o punho (`lm[0]`) e a articulação CMC do polegar (`lm[1]`):

$$\text{distancia\_base} = \|\vec{P}_0 - \vec{P}_1\|_2 + \epsilon$$

$$\text{click\_dist} = \frac{\|\vec{P}_4 - \vec{P}_6\|_2}{\text{distancia\_base}}, \quad \text{spread} = \frac{\|\vec{P}_8 - \vec{P}_{12}\|_2}{\text{distancia\_base}}$$

### 4.2 Filtragem de Tremor (Anti-Jitter)

Para evitar micro-oscilações indesejadas no cursor, aplica-se um filtro de média móvel (*Moving Average Filter*) sobre as posições da ponta do indicador (`lm[8]`):

$$\bar{x}_t = \frac{1}{N} \sum_{i=0}^{N-1} x_{t-i}, \quad \Delta x = S \cdot (\bar{x}_t - \bar{x}_{t-1}) \cdot W + 0.5$$

Onde $S$ é a sensibilidade configurada pelo usuário e $W$ é a largura em pixels do frame de entrada.

### 4.3 Mapeamento de Gestos

| Gesto da Mão | Condição Lógica | Ação Disparada no SO | Feedback Visual |
|---|---|---|---|
| **Mover Cursor** | `spread >= 0.7` e não em scroll | Move o cursor para $(\Delta x, \Delta y)$ | Ponto azul na ponta do indicador |
| **Pausar Cursor** | `spread < 0.7` (juntar indicador e médio) | Interrompe o envio de coordenadas | Sem ação |
| **Clique Esquerdo / Arraste** | `click_dist < 0.7` | `mouse.press(Button.left)` | Ponto amarelo |
| **Soltar Clique** | `click_dist >= 0.7` | `mouse.release(Button.left)` | Liberação do botão |
| **Duplo Clique** | Dois cliques em intervalo $\Delta t < 0.5$ s | `mouse.click(Button.left, 2)` | — |
| **Clique Direito** | Manter clique parado por $t \ge 1.5$ s | Emissão de clique com botão direito | Ponto vermelho |
| **Scroll de Tela** | $\text{lm}[8].y - \text{lm}[5].y > -0.06$ (indicador flexionado) | `mouse.scroll(0, -\Delta y / 50)` | Ponto preto |

---

## 5. Resiliência de Hardware e Multi-Backend

### 5.1 Fallback Automático de Backend (OpenCV)

No ambiente Windows, drivers de câmera frequentemente apresentam incompatibilidades ao inicializar com o backend padrão do OpenCV. O NonMouse implementa um algoritmo de fallback inteligente no módulo `nonmouse/camera.py`:

```python
import cv2

def open_camera(index: int, width: int = 640, height: int = 480) -> cv2.VideoCapture:
    """Tenta sequencialmente múltiplos backends até obter um frame válido."""
    for backend in [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY]:
        cap = cv2.VideoCapture(index, backend)
        if cap.isOpened():
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            ret, frame = cap.read()
            if ret and frame is not None:
                return cap
            cap.release()
    raise RuntimeError(f"Não foi possível inicializar a câmera {index}.")
```

### 5.2 Comportamento One-Shot do pygrabber

Durante a investigação do backend DirectShow via pygrabber, identificou-se um comportamento não documentado: o `SampleGrabberCallback.BufferCB` só entrega frames quando `keep_photo=True`, ou seja, o método `grab_frame()` precisa ser chamado explicitamente a cada iteração do loop. Sem essa chamada, o callback nunca é disparado e nenhum frame é entregue, mesmo com o grafo DirectShow em execução.

```python
while True:
    graph.grab_frame()   # solicita o próximo frame (one-shot)
    with lock:
        frame = frame_data["frame"]
    if frame is not None:
        # processa frame...
```

Adicionalmente, o método `prepare_preview_graph()` é o correto para captura contínua. O `prepare_recording_graph()` exige um muxer de arquivo e lança `AssertionError` quando usado sem ele.

---

## 6. Guia de Instalação, Configuração e Execução

### 6.1 Instalação

O NonMouse é compatível e validado para **Python 3.12.9** no Windows 10/11.

```bash
# 1. Clonar o repositório
git clone https://github.com/takeyamayuki/NonMouse
cd NonMouse

# 2. Instalar dependências sem cache (evita IncompleteRead)
python -m pip install --no-cache-dir -r requirements.txt
```

> **Atenção:** Use sempre o **Windows installer (64-bit)** do Python 3.12.9. O *embeddable package* (`.zip`) não inclui `pip`, `venv` nem `ensurepip` e causará falhas na criação do ambiente virtual.

### 6.2 Diagnóstico de Dispositivos

Antes de iniciar, liste os dispositivos de vídeo disponíveis:

```bash
python list_camera.py
```

### 6.3 Execução com Interface Gráfica (`app.py`)

```bash
python app.py
```

A janela inicial permite escolher o índice da câmera, o modo de posicionamento (`Normal`, `Above`, `Behind`) e a sensibilidade do cursor.

### 6.4 Execução em Linha de Comando / Headless (`tv_mouse.py`)

Ideal para sistemas embarcados, PCs conectados a TVs ou uso contínuo em segundo plano:

```bash
# Câmera 1, sensibilidade 20, sem janela de vídeo
python tv_mouse.py --camera 1 --kando 20 --headless
```

---

## 7. Comparativo de Backends de Captura

O repositório inclui implementações comparativas na pasta `examples/`, demonstrando a viabilidade de diferentes abordagens no Windows 11:

| Backend | Biblioteca | Windows 11 | Threading | Observações |
|---|---|---|---|---|
| **OpenCV DSHOW/MSMF** | `opencv-python` | ✅ | Manual | Padrão recomendado; fallback automático de backend |
| **DirectShow COM** | `pygrabber` | ✅ | Callback | `grab_frame()` one-shot obrigatório; modo VIDEO no MediaPipe |
| **FFmpeg/dshow** | `av` (PyAV) | ✅ | Não | Requer nome exato do dispositivo via DirectShow |
| **OpenCV + threading** | `vidgear` | ✅ | Embutido | API simples; threading gerenciado automaticamente |
| **imageio-ffmpeg** | `imageio` | ❌ | Não | Não suporta webcam no Windows; use PyAV no lugar |

> **Nota sobre imageio:** A sintaxe `<video0>` é interpretada como caminho de arquivo local no Windows. O plugin `pyav` do imageio não expõe o parâmetro `format=dshow` necessário para captura via DirectShow. No Linux/macOS, `iio.imiter("<video0>", plugin="pyav")` funciona normalmente.

> **Nota sobre PyAV e pygrabber:** Ambos requerem o nome do dispositivo obtido via enumeração DirectShow, não o índice numérico. O utilitário `list_camera.py` e a função `FilterGraph().get_input_devices()` do pygrabber retornam os nomes corretos.

---

## 8. Conclusão

O projeto **NonMouse** consolida uma solução completa, leve e acessível para controle de computadores sem contato físico. Através do uso de redes neurais otimizadas (MediaPipe Tasks), filtros estatísticos de suavização e um sistema robusto de captura resiliente a falhas de hardware, o projeto atinge uma experiência de uso responsiva com hardware de consumo comum.

A investigação dos diferentes backends de captura revelou comportamentos não documentados relevantes — em especial o modelo one-shot do pygrabber e a incompatibilidade do imageio com DirectShow no Windows — que foram documentados e corrigidos no código.

Como trabalhos futuros e possíveis extensões, destacam-se:

- Suporte a gestos bi-manuais (ex: pinça com as duas mãos para zoom e rotação).
- Calibração automática de sensibilidade baseada no tamanho da tela do usuário.
- Classificação de gestos contínuos e atalhos customizados utilizando modelos de séries temporais (LSTM/GRU).
- Suporte a Linux/macOS com backends alternativos ao DirectShow (V4L2, AVFoundation).

---

## 9. Referências

1. **Lugaresi, C., Tang, J., Nash, H., McClanahan, C., Uboweja, E., Hays, M., ... & Grundmann, M.** (2019). *MediaPipe: A Framework for Building Perception Pipelines*. arXiv:1906.08172.
2. **Zhang, F., Bazarevsky, V., Vakunov, A., Tkachenka, A., Sung, G., Chang, C. L., & Grundmann, M.** (2020). *MediaPipe Hands: On-device Real-time Hand Tracking*. arXiv:2006.10214.
3. **Bradski, G.** (2000). *The OpenCV Library*. Dr. Dobb's Journal of Software Tools.
4. **Google for Developers.** *Hand Landmarks Detection Guide — MediaPipe Tasks*. https://developers.google.com/mediapipe/solutions/vision/hand_landmarker
5. **Python Software Foundation.** *pynput: Monitor and control user input devices*. https://pypi.org/project/pynput/
6. **Schiavinato, A.** *python_grabber: A Python wrapper for DirectShow*. https://github.com/andreaschiavinato/python_grabber
7. **PyAV Contributors.** *PyAV: Pythonic bindings for FFmpeg*. https://pyav.org/docs/stable/
8. **AbhiTronix.** *VidGear: High-performance Video Processing Python Library*. https://abhitronix.github.io/vidgear/latest/
9. **Microsoft.** *DirectShow — Windows App Development*. https://learn.microsoft.com/en-us/windows/win32/directshow/directshow
10. **FFmpeg Project.** *FFmpeg Documentation*. https://ffmpeg.org/documentation.html
