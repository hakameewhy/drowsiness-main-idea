import cv2
import numpy as np
import mediapipe as mp
import time
import winsound
import threading  # Untuk suara tanpa blocking
import datetime
import os
import user

# --- Konstanta ---
EAR_THRESHOLD = 0.15       # Ambang batas mata tertutup
EAR_CONSEC_flipS = 30     # flip berturut-turut untuk kantuk
MAR_THRESHOLD = 0.8        # Ambang batas mulut terbuka (menguap)
MAR_CONSEC_flipS = 15     # flip berturut-turut untuk menguap
COUNTER_EYE = 0            # Counter untuk mata       
COUNTER_YAWN = 0
ALREADY_ALERTED = False    # Flag untuk menghindari multiple alert
TOTAL_EYE_COUNT = 0
TOTAL_YAWN_COUNT = 0

global ALARM_ON


# --- inisialisasi User ---
pengguna = user.User.load()

# --- Inisialisasi Mediapipe ---
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# --- Fungsi EAR (Eye Aspect Ratio) ---
def eye_aspect_ratio(landmarks, eye_indices):
    p1, p2, p3, p4, p5, p6 = [landmarks[i] for i in eye_indices]
    A = np.linalg.norm(np.array(p2) - np.array(p6))
    B = np.linalg.norm(np.array(p3) - np.array(p5))
    C = np.linalg.norm(np.array(p1) - np.array(p4))
    ear = (A + B) / (2.0 * C)
    return ear

# --- Fungsi MAR (Mouth Aspect Ratio) ---
def mouth_aspect_ratio(landmarks, mouth_indices):
    # Vertical: jarak atas-bawah bibir
    p1, p2, p3, p4 = [landmarks[i] for i in mouth_indices[:4]]
    A = np.linalg.norm(np.array(p2) - np.array(p4))  # atas ke bawah tengah
    B = np.linalg.norm(np.array(p1) - np.array(p3))  # atas ke bawah kiri/kanan

    # Horizontal: lebar mulut
    p5, p6 = [landmarks[i] for i in mouth_indices[4:6]]
    C = np.linalg.norm(np.array(p5) - np.array(p6))

    mar = (A + B) / (2.0 * C)
    return mar

# --- Fungsi memainkan suara di thread terpisah ---
ALARM_ON = False
def play_sound_async():
    threading.Thread(target=winsound.PlaySound, args=("alert.wav", winsound.SND_FILENAME), daemon=True).start()

# --- Indeks landmark mata & mulut (MediaPipe Face Mesh) ---
LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [263, 387, 385, 362, 380, 373]

# Mulut: atas, bawah, dan sudut mulut
MOUTH_OUTER = [
    61,   # kiri atas bibir
    291,  # kanan atas bibir
    39,   # kiri bawah bibir
    181,  # kanan bawah bibir
    0,    # ujung kiri mulut
    17    # ujung kanan mulut
]
MOUTH_INNER_VERTICAL = [13, 14]  # Tengah atas & bawah bibir dalam (opsional untuk akurasi)

# Gunakan outer untuk MAR sederhana
MOUTH_INDICES = [61, 291, 39, 181, 0, 17]  # [vert_left, vert_right, horz_left, horz_right, left_corner, right_corner]

# --- Akses kamera ---
cap = cv2.VideoCapture(0)
time.sleep(1)

print("[INFO] Starting drowsiness & yawning detection...")

while True:
    
    ret, layar = cap.read()
    if not ret:
        break
    
    flip = cv2.flip(layar,1)

    flip_rgb = cv2.cvtColor(flip, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(flip_rgb)
    
    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:
            h, w, _ = flip.shape
            landmarks = [(lm.x * w, lm.y * h) for lm in face_landmarks.landmark]
            

            # --- Deteksi Mata (Kantuk) ---
            left_ear = eye_aspect_ratio(landmarks, LEFT_EYE)
            right_ear = eye_aspect_ratio(landmarks, RIGHT_EYE)
            ear = (left_ear + right_ear) / 2.0

            # Gambar titik mata
            for i in LEFT_EYE + RIGHT_EYE:
                x, y = int(landmarks[i][0]), int(landmarks[i][1])
                cv2.circle(flip, (x, y), 1, (0, 255, 0), -1)

            # Logika kantuk
            if ear < EAR_THRESHOLD:
                COUNTER_EYE += 1
                if COUNTER_EYE >= EAR_CONSEC_flipS and not ALARM_ON:
                    ALARM_ON = True
                    cv2.putText(flip, "DROWSINESS!", (50, 100),
                                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
                    play_sound_async()
            else:
                if COUNTER_EYE >= EAR_CONSEC_flipS:
                    TOTAL_EYE_COUNT += 1  # Hitung 1 kali menguap penuh
                    print(f"[INFO] Total Eyes: {TOTAL_EYE_COUNT}")
                COUNTER_EYE = 0  # Reset setelah mulut menutup lagi
                ALARM_ON = False

            cv2.putText(flip, f"EAR: {ear:.2f}", (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            #Deteksi Menguap (Mulut Terbuka)
            mar = mouth_aspect_ratio(landmarks, MOUTH_INDICES)

            # Gambar titik mulut
            for i in [0, 17, 61, 291, 39, 181]:  # Hanya titik utama
                x, y = int(landmarks[i][0]), int(landmarks[i][1])
                cv2.circle(flip, (x, y), 2, (255, 255, 0), -1)

           #deteksi menguap
        if mar < MAR_THRESHOLD:  # Mulut terbuka lebar
            COUNTER_YAWN += 1
        else:
            if COUNTER_YAWN >= MAR_CONSEC_flipS:
                TOTAL_YAWN_COUNT += 1  # Hitung 1 kali menguap penuh
                print(f"[INFO] Total Yawns: {TOTAL_YAWN_COUNT}")
            COUNTER_YAWN = 0  # Reset setelah mulut menutup lagi

        #Jika total mata kantuk 4 kali, tampilkan pesan
        if TOTAL_EYE_COUNT >= 4 and not ALREADY_ALERTED:
                print("PLEASE TAKE A BREAK!")
                #ALREADY_ALERTED = True
                pengguna.tambahmatakantuk()
                TOTAL_EYE_COUNT =  0

        #Jika total menguap 4 kali, tampilkan pesan 
        if TOTAL_YAWN_COUNT >= 4 and not ALREADY_ALERTED:
                print("PLEASE TAKE A BREAK!")
                #ALREADY_ALERTED = True
                pengguna.tambahmenguap
                TOTAL_YAWN_COUNT =  0

        cv2.putText(flip, f"MAR: {mar:.2f}", (50, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    # Tampilkan flip
    cv2.imshow("Drowsiness & Yawning Detection", flip )
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# Cleanup
cap.release()
cv2.destroyAllWindows()