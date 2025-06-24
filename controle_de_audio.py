import cv2
import mediapipe as mp
import numpy as np
import math
import pyautogui  # Usamos pyautogui para simular teclas de mídia
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

# --- CONFIGURAÇÕES GERAIS ---
CAM_WIDTH, CAM_HEIGHT = 1280, 720
SMOOTHING_FACTOR = 0.1
PINCH_MIN_DIST, PINCH_MAX_DIST = 35, 220
# Cooldowns (em frames) para evitar acionamentos múltiplos
FIST_COOLDOWN_FRAMES = 30
TRACK_CHANGE_COOLDOWN_FRAMES = 30

# --- INICIALIZAÇÃO ---
cap = cv2.VideoCapture(0)
cap.set(3, CAM_WIDTH)
cap.set(4, CAM_HEIGHT)

# Inicialização do MediaPipe no escopo global para ser acessível por todas as funções
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.8, min_tracking_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

# Inicialização de Áudio
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))
vol_range = volume.GetVolumeRange()
min_vol, max_vol = vol_range[0], vol_range[1]

# Variáveis de estado
vol_percent_suave = 0
fist_cooldown_counter = 0
track_change_cooldown_counter = 0

# --- FUNÇÃO AUXILIAR DE DETECÇÃO DE GESTOS ---
def get_finger_state(landmarks):
    """Retorna um dicionário com o estado (True para aberto, False para fechado) de cada dedo."""
    finger_states = {}
    finger_states['INDEX'] = landmarks[mp_hands.HandLandmark.INDEX_FINGER_TIP].y < landmarks[mp_hands.HandLandmark.INDEX_FINGER_PIP].y
    finger_states['MIDDLE'] = landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_TIP].y < landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_PIP].y
    finger_states['RING'] = landmarks[mp_hands.HandLandmark.RING_FINGER_TIP].y < landmarks[mp_hands.HandLandmark.RING_FINGER_PIP].y
    finger_states['PINKY'] = landmarks[mp_hands.HandLandmark.PINKY_TIP].y < landmarks[mp_hands.HandLandmark.PINKY_PIP].y
    return finger_states

# --- LOOP PRINCIPAL ---
while True:
    success, img = cap.read()
    if not success:
        break
    img = cv2.flip(img, 1)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)

    # Atualizar contadores de cooldown
    if fist_cooldown_counter > 0: fist_cooldown_counter -= 1
    if track_change_cooldown_counter > 0: track_change_cooldown_counter -= 1

    if results.multi_hand_landmarks:
        hand_landmarks = results.multi_hand_landmarks[0]
        landmarks = hand_landmarks.landmark
        finger_states = get_finger_state(landmarks)

        # --- LÓGICA DE DECISÃO DE GESTOS COM PRIORIDADE CORRIGIDA ---
        
        is_fist = not finger_states['INDEX'] and not finger_states['MIDDLE'] and not finger_states['RING'] and not finger_states['PINKY']

        # PRIORIDADE 1: Gesto de Punho Fechado
        if is_fist:
            if fist_cooldown_counter == 0:
                pyautogui.press('playpause')
                fist_cooldown_counter = FIST_COOLDOWN_FRAMES
                cv2.putText(img, "PLAY/PAUSE", (CAM_WIDTH//2-150, CAM_HEIGHT//2), cv2.FONT_HERSHEY_TRIPLEX, 2, (0, 255, 255), 3)

        # PRIORIDADE 2: Gesto de Próxima Faixa
        elif finger_states['INDEX'] and not finger_states['MIDDLE'] and finger_states['RING'] and finger_states['PINKY']:
            if track_change_cooldown_counter == 0:
                pyautogui.press('nexttrack')
                track_change_cooldown_counter = TRACK_CHANGE_COOLDOWN_FRAMES
                cv2.putText(img, ">> PROXIMA", (CAM_WIDTH//2-150, CAM_HEIGHT//2), cv2.FONT_HERSHEY_TRIPLEX, 2, (0, 255, 0), 3)
        
        # PRIORIDADE 3: Gesto de Faixa Anterior
        elif finger_states['INDEX'] and finger_states['MIDDLE'] and not finger_states['RING'] and finger_states['PINKY']:
            if track_change_cooldown_counter == 0:
                pyautogui.press('prevtrack')
                track_change_cooldown_counter = TRACK_CHANGE_COOLDOWN_FRAMES
                cv2.putText(img, "<< ANTERIOR", (CAM_WIDTH//2-150, CAM_HEIGHT//2), cv2.FONT_HERSHEY_TRIPLEX, 2, (0, 0, 255), 3)

        # PRIORIDADE 4: Gesto de Controle de Volume
        elif finger_states['PINKY']:
            active_color = (0, 255, 0)
            thumb_tip = landmarks[mp_hands.HandLandmark.THUMB_TIP]
            index_tip = landmarks[mp_hands.HandLandmark.INDEX_FINGER_TIP]
            tx, ty = int(thumb_tip.x * CAM_WIDTH), int(thumb_tip.y * CAM_HEIGHT)
            ix, iy = int(index_tip.x * CAM_WIDTH), int(index_tip.y * CAM_HEIGHT)
            pinch_length = math.hypot(ix - tx, iy - ty)
            
            if pinch_length < PINCH_MIN_DIST:
                active_color = (0, 0, 255); volume.SetMute(1, None)
            else:
                volume.SetMute(0, None)
                vol_percent = np.interp(pinch_length, [PINCH_MIN_DIST, PINCH_MAX_DIST], [0, 100])
                vol_percent_suave = (SMOOTHING_FACTOR * vol_percent) + ((1 - SMOOTHING_FACTOR) * vol_percent_suave)
                vol_db = np.interp(vol_percent_suave, [0, 100], [min_vol, max_vol])
                volume.SetMasterVolumeLevel(vol_db, None)
            
            cv2.line(img, (tx, ty), (ix, iy), active_color, 3)
            cv2.circle(img, (tx, ty), 10, active_color, cv2.FILLED)
            cv2.circle(img, (ix, iy), 10, active_color, cv2.FILLED)
        
        else:
            cv2.putText(img, "Mostre um gesto", (30, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        mp_draw.draw_landmarks(img, hand_landmarks, mp_hands.HAND_CONNECTIONS)

    # --- UI PERSISTENTE DESENHADA COM OPENCV ---
    bar_x, bar_y_start, bar_y_end, bar_width = 50, 150, 450, 35
    cv2.rectangle(img, (bar_x, bar_y_start), (bar_x + bar_width, bar_y_end), (210, 210, 210), 3)
    fill_height = int(np.interp(vol_percent_suave, [0, 100], [bar_y_end, bar_y_start]))
    cv2.rectangle(img, (bar_x, fill_height), (bar_x + bar_width, bar_y_end), (0, 255, 0), cv2.FILLED)
    cv2.putText(img, f'{int(vol_percent_suave)} %', (bar_x - 15, bar_y_end + 40), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2)
    
    cv2.imshow("Controle de Midia por Gestos (Python-OpenCV)", img)
    
    # Lógica de encerramento
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q') or key == ord('Q') or key == 27:
        break

# --- LIMPEZA ---.
cap.release()
cv2.destroyAllWindows()