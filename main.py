import cv2
import requests
import numpy as np
from dotenv import load_dotenv
import os

load_dotenv()  

def send_telegram_message(message):
    """
    Envoie un message à un chat Telegram.
    :param message: Message à envoyer.
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHANNEL_ID")
    url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={message}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        print("Message envoyé avec succès.")
    except requests.RequestException as e:
        print(f"Erreur lors de l'envoi du message: {e}")


def verif_code_retour(video_url):
    """
    Vérifie le code de retour d'une requête HTTP pour une URL donnée.
    :param video_url: Lien de la vidéo (peut être un chemin local ou un URL).
    """
    try:
        response = requests.head(video_url, timeout=5)  # Timeout pour éviter les blocages
        return response.status_code
    except requests.RequestException as e:
        message = f"Erreur lors de la vérification du lien {video_url}: {e}"
        send_telegram_message(message)
        return None

def capture_frame_from_video(video_url, output_file='screenshot.jpg', frame_position=0):
    """
    Capture une image d'une vidéo.
    :param video_url: Lien de la vidéo (peut être un chemin local ou un URL).
    :param output_file: Chemin pour sauvegarder l'image capturée.
    :param frame_position: La position du cadre à capturer (en millisecondes ou indice de frame).
    """
    cap = cv2.VideoCapture(video_url)
    
    if not cap.isOpened():
        print(f"Impossible d'ouvrir la vidéo: {video_url}")
        return False, None
    
    cap.set(cv2.CAP_PROP_POS_MSEC, frame_position)  # Position en millisecondes
    ret, frame = cap.read()
    
    if ret:
        # Vérifier si l'image est valide (non vide)
        if is_frame_valid(frame):
            cv2.imwrite(output_file, frame)
            print(f"Image capturée et sauvegardée dans {output_file}")
            cap.release()
            return True, frame
        else:
            message = f"Frame capturée est vide ou noire. (URL: {video_url})"
            send_telegram_message(message)
    else:
        message = f"Impossible de capturer une frame pour la vidéo: {video_url}"
        send_telegram_message(message)
    
    cap.release()
    return False, None

def is_frame_valid(frame):
    """
    Vérifie si une frame est valide (non noire).
    :param frame: Image capturée en tant que tableau numpy.
    """
    if frame is None or np.sum(frame) == 0:
        return False  # Vide ou totalement noire
    return True

def open_m3u_file(m3u_file_path):
    """
    Ouvre un fichier M3U et retourne les liens des vidéos.
    :param m3u_file_path: Chemin du fichier M3U.
    """
    with open(m3u_file_path, 'r') as f:
        lines = f.readlines()
    return [line.strip() for line in lines if line.startswith('http')]

def monitor_links(m3u_file_path, frame_position=2000):
    """
    Surveille les liens d'un fichier M3U et vérifie leur disponibilité.
    :param m3u_file_path: Chemin du fichier M3U.
    :param frame_position: La position pour capturer la frame.
    """
    video_links = open_m3u_file(m3u_file_path)
    for video_url in video_links:
        print(f"Vérification de: {video_url}")
        code_retour = verif_code_retour(video_url)
        
        if code_retour == 200:
            print(f"Code de retour 200 pour {video_url}")
            success, frame = capture_frame_from_video(video_url, frame_position=frame_position)
            
            if success:
                print(f"Lien {video_url} valide et image capturée.")
            else:
                message = f"Lien {video_url} valide, mais image non valide."
                send_telegram_message(message)
        else:
            message = f"Code de retour invalide ({code_retour}) pour {video_url}"
            send_telegram_message(message)

# Exemple d'utilisation
m3u_path = "main.m3u"  # Remplacez par le chemin de votre fichier contenant les liens
monitor_links(m3u_path)
