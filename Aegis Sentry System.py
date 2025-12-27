import cv2
import numpy as np
import time
import threading
import os
import speech_recognition as sr
import webbrowser
from datetime import datetime
from gtts import gTTS
from pygame import mixer

class AirDefenceAI:
    def __init__(self):
        mixer.init()
        self.cmd = None
        self.force_alert = False # Manual lockdown override
        
        # Audio Manifest
        self.audio_files = {
            "boot": "Air defense system active. Tracking and monitoring protocols engaged. Good evening, Sir.",
            "scan": "Initiating deep structural scan. Analyzing perimeter for hostiles.",
            "danger": "Hostile intent detected. Sir, I recommend immediate action.",
            "normal": "Scan complete. No hostile signatures found.",
            "sus": "Sir, I have detected a suspicious presence.",
            "clear": "Perimeter is secure. All systems nominal.",
            "off": "Powering down systems. Goodbye, Sir.",
            "google": "Accessing the global network, Sir.",
            "report": "All air defense sub-systems are operational. Energy at one hundred percent.",
            "lockdown": "Protocol initiated. Full perimeter lockdown in effect.",
            "reset": "Alert cleared. Returning to standard monitoring."
        }
        self.sync_voice()

    def sync_voice(self):
        for key, text in self.audio_files.items():
            if not os.path.exists(f"{key}.mp3"):
                gTTS(text=text, lang='en', tld='co.uk').save(f"{key}.mp3")

    def speak(self, key):
        if mixer.music.get_busy(): mixer.music.stop()
        mixer.music.load(f"{key}.mp3")
        mixer.music.play()

    def voice_engine(self):
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=2)
            while True:
                try:
                    audio = recognizer.listen(source, timeout=None, phrase_time_limit=3)
                    text = recognizer.recognize_google(audio).lower()
                    print(f"COMM_LOG: {text}")
                    
                    if "jarvis" in text:
                        if "scan" in text: self.cmd = "SCAN"
                        elif "status" in text: self.cmd = "STATUS"
                        elif "shutdown" in text: self.cmd = "SHUTDOWN"
                        elif "time" in text: self.cmd = "TIME"
                        elif "google" in text: self.cmd = "GOOGLE"
                        elif "report" in text: self.cmd = "REPORT"
                        elif "level 5" in text or "lockdown" in text: self.cmd = "ALERT_ON"
                        elif "clear" in text or "reset" in text: self.cmd = "ALERT_OFF"
                except: continue

def main():
    cap = cv2.VideoCapture(0)
    ai = AirDefenceAI()
    fgbg = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=50)
    
    threading.Thread(target=ai.voice_engine, daemon=True).start()
    ai.speak("boot")

    while True:
        ret, frame = cap.read()
        if not ret: break
        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]
        display = frame.copy()

        # --- DETECTION ENGINE ---
        fgmask = fgbg.apply(frame)
        contours, _ = cv2.findContours(fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        target = None
        threat_level = 0
        for c in contours:
            area = cv2.contourArea(c)
            if area > 5000:
                target = cv2.boundingRect(c)
                threat_level = min(100, int((area/(w*h))*400))
                break

        # --- COMMAND LOGIC ---
        if ai.cmd == "TIME":
            now = datetime.now().strftime("%I:%M %p")
            ai.speak("clear") # Notification sound
            print(f"SYSTEM TIME: {now}")
            ai.cmd = None

        elif ai.cmd == "GOOGLE":
            ai.speak("google")
            webbrowser.open("https://www.google.com")
            ai.cmd = None

        elif ai.cmd == "REPORT":
            ai.speak("report")
            ai.cmd = None

        elif ai.cmd == "ALERT_ON":
            ai.speak("lockdown")
            ai.force_alert = True
            ai.cmd = None

        elif ai.cmd == "ALERT_OFF":
            ai.speak("reset")
            ai.force_alert = False
            ai.cmd = None

        # --- HUD RENDERING ---
        is_danger = threat_level > 35 or ai.force_alert
        col = (0, 0, 255) if is_danger else (0, 255, 255)
        
        # Pulsing outer frame
        thick = 2 if not is_danger else int(2 + np.sin(time.time()*10)*2)
        cv2.rectangle(display, (10, 10), (w-10, h-10), col, max(1, thick))
        
        if target:
            x, y, cw, ch = target
            cv2.drawMarker(display, (x+cw//2, y+ch//2), col, cv2.MARKER_CROSS, 40, 2)
            cv2.putText(display, f"THREAT_LVL: {threat_level}%", (x, y-10), 0, 0.5, col, 2)

        if ai.cmd == "SCAN":
            ai.speak("scan")
            for i in range(15):
                ly = int((time.time()*500 + i*30) % h)
                cv2.line(display, (0, ly), (w, ly), (0, 255, 255), 1)
            time.sleep(1)
            ai.speak("danger" if threat_level > 35 else "normal")
            ai.cmd = None

        elif ai.cmd == "STATUS":
            ai.speak("sus" if target else "clear")
            ai.cmd = None

        elif ai.cmd == "SHUTDOWN":
            ai.speak("off")
            time.sleep(2)
            break

        # Status HUD Text
        cv2.putText(display, f"SYSTEM_MODE: {'LOCKDOWN' if ai.force_alert else 'TRACKING'}", (20, h-20), 0, 0.4, col, 1)

        cv2.imshow("AIR DEFENCE SYSTEM", display)
        if cv2.waitKey(1) == ord('q'): break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()