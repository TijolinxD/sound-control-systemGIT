Controle de Mídia por Gestos com a Mão
Este projeto permite controlar as mídias do seu computador (Volume, Play/Pause, Próxima/Anterior Faixa) usando gestos da mão capturados por uma webcam em tempo real. Foi feito 100% sozinho então não esperem um dos melhores resultados (teve momentos que nem eu mesmo sabia oq estava fazendo kksksks).

Funcionalidades
Controle de Volume: Gesto de pinça entre o polegar e o indicador (ativado com o dedo mindinho levantado).
Mudo (Mute): Fechar a pinça completamente.
Play/Pause: Gesto de punho fechado.
Próxima Faixa: Gesto com o dedo médio abaixado e os outros levantados.
Faixa Anterior: Gesto com o dedo anelar abaixado e os outros levantados.
Interface Visual: Feedback em tempo real desenhado sobre a imagem da câmera com OpenCV.
Controle de Mídia Nativo: Usa as APIs do Windows para um controle robusto que funciona mesmo com o player de música em segundo plano.
Tecnologias Utilizadas
Python 3.11
OpenCV
MediaPipe
pycaw
pyautogui (ou winsdk)
Como Executar
Clone este repositório.
Instale as dependências: pip install -r requirements.txt
Execute o script principal: python controle_de_audio.py
Mostre sua mão para a câmera e use os gestos!
Demonstração
(logo logo gravo um vídeo rápido ou gif mostrando!)