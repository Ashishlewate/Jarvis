import os
import cv2
import time
import threading
import numpy as np
import pyttsx3
import speech_recognition as sr
from datetime import datetime
from ultralytics import YOLO

# Stability Environment Variables
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

class AegisElite:
    def __init__(self):
        # --- 1. HUD & TRACKING SETTINGS ---
        self.active = True
        self.force_alert = False
        self.scan_active = False
        self.scan_line_y = 0
        self.max_threat_speed = 0
        self.tracker = {}
        
        # --- 2. SECURITY PROTOCOLS ---
        self.authorized = False
        self.auth_code = "2468"  # Set your custom verbal code
        self.awaiting_code = False
        
        # --- 3. VISION & AUDIO SETUP ---
        self.model = YOLO('yolov8n.pt')  # Ensure yolov8n.pt is in the same folder
        self.cap = cv2.VideoCapture(0)
        
        # Colors (BGR)
        self.CYAN = (255, 255, 0)
        self.RED = (0, 0, 255)
        self.AMBER = (0, 165, 255)
        self.GREEN = (0, 255, 0)

    def speak(self, text):
        """Thread-safe isolated speech engine to prevent HUD lag."""
        print(f"FRIDAY: {text}")
        def say_task():
            try:
                # Re-initializing inside thread for absolute stability
                engine = pyttsx3.init('sapi5')
                engine.setProperty('rate', 195)
                voices = engine.getProperty('voices')
                if len(voices) > 1: engine.setProperty('voice', voices[1].id)
                engine.say(text)
                engine.runAndWait()
            except Exception as e:
                print(f"Speech Loop Error: {e}")

        threading.Thread(target=say_task, daemon=True).start()

    def voice_engine(self):
        """Tactical Command Module with Security Authorization."""
        r = sr.Recognizer()
        r.energy_threshold = 150 # High sensitivity
        
        with sr.Microphone() as source:
            r.adjust_for_ambient_noise(source, duration=1)
            print("--- AEGIS MARK X: VOICE MODULE ONLINE ---")
            
            while self.active:
                try:
                    audio = r.listen(source, timeout=None, phrase_time_limit=4)
                    cmd = r.recognize_google(audio).lower()
                    print(f"TACTICAL INPUT >> {cmd}")

                    if "friday" in cmd:
                        # SECURITY CHECK: If waiting for code
                        if self.awaiting_code:
                            if self.auth_code in cmd:
                                self.authorized = True
                                self.awaiting_code = False
                                self.speak("Authorization confirmed. Accessing tactical arrays.")
                            else:
                                self.speak("Authentication failed. Security lock remains active.")
                                self.awaiting_code = False
                            continue

                        # --- AUTHORIZATION REQUIRED COMMANDS ---
                        restricted_cmds = ["lockdown", "arm", "weapons", "reboot", "disarm"]
                        if any(word in cmd for word in restricted_cmds):
                            if not self.authorized:
                                self.speak("Access denied. Please provide your authorization code.")
                                self.awaiting_code = True
                                continue
                            
                            # Execute restricted logic
                            if "lockdown" in cmd:
                                self.force_alert = True
                                self.speak("Protocol Level 5. Full perimeter lockdown.")
                            elif "arm" in cmd:
                                self.speak("Defensive batteries armed and tracking.")
                            elif "disarm" in cmd:
                                self.authorized = False
                                self.force_alert = False
                                self.speak("Systems disarmed. Security lock re-engaged.")

                        # --- UNRESTRICTED COMMANDS (25+ EXPANDED) ---
                        elif "status" in cmd: self.speak(f"Systems are {'Tactical' if self.authorized else 'Secure'}. All system are in stand by , alll weapons and radar are 100% in good condition.")
                        elif "scan" in cmd: 
                            self.scan_active = True
                            self.speak("Initiating deep structural scan.")
                        elif "clear" in cmd: 
                            self.scan_active = False
                            self.force_alert = False
                            self.speak("Scan clear. Returning to standby.")
                        elif "report" in cmd: self.speak(f"Peak intruder velocity recorded at {self.max_threat_speed} units.")
                        elif "time" in cmd: self.speak(f"Sir, the time is {datetime.now().strftime('%I:%M %p')}.")
                        elif "radar" in cmd: self.speak("Radar arrays synchronized with orbital platform.")
                        elif "thermal" in cmd: self.speak("Thermal filters active. Scanning for heat signatures.")
                        elif "identify" in cmd: self.speak("Subject analysis: Unknown biological signature.")
                        elif "coordinates" in cmd: self.speak("Triangulating GPS position. Signal strength optimal.")
                        elif "energy" in cmd: self.speak("Energy levels nominal. No depletion detected.")
                        elif "weather" in cmd: self.speak("Atmospheric pressure is dropping. Stay alert.")
                        elif "diagnostic" in cmd: self.speak("Integrity check complete. All sub-systems 100 percent.")
                        elif "shield" in cmd: self.speak("Plasma shields deployed at 80 percent.")
                        elif "analyse" in cmd: self.speak("Analyzing movement patterns. Subject appears hostile.")
                        elif "shutdown" in cmd: 
                            self.speak("Safe journey, Boss.")
                            self.active = False
                            os._exit(0)
                        else: self.speak("Standing by, Boss.")
                except: continue

    def run(self):
        threading.Thread(target=self.voice_engine, daemon=True).start()
        self.speak("Aegis systems online. Friday is standing by.")

        while self.active:
            success, frame = self.cap.read()
            if not success: break
            
            frame = cv2.flip(frame, 1)
            h, w = frame.shape[:2]
            results = self.model(frame, conf=0.4, verbose=False)
            curr_t = time.time()
            
            # Base UI State
            is_danger = self.force_alert
            hud_col = self.RED if is_danger else self.CYAN

            # 1. SCANNER ANIMATION
            if self.scan_active:
                self.scan_line_y = (self.scan_line_y + 15) % h
                cv2.line(frame, (0, self.scan_line_y), (w, self.scan_line_y), self.CYAN, 2)
                overlay = frame.copy()
                cv2.rectangle(overlay, (0, self.scan_line_y - 20), (w, self.scan_line_y), self.CYAN, -1)
                cv2.addWeighted(overlay, 0.1, frame, 0.9, 0, frame)

            # 2. OBJECT TRACKING
            for r in results:
                for box in r.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    label = self.model.names[int(box.cls[0])]
                    
                    if label in ['person', 'car', 'drone']:
                        center = ((x1+x2)//2, (y1+y2)//2)
                        obj_id = f"{label}_{center[0]//50}"
                        
                        speed = 0
                        target_col = self.CYAN
                        
                        if obj_id in self.tracker:
                            px, py, pt = self.tracker[obj_id]
                            dist = np.sqrt((center[0]-px)**2 + (center[1]-py)**2)
                            dt = curr_t - pt
                            if dt > 0:
                                speed = int((dist/dt) * 0.5)
                                if speed > self.max_threat_speed: self.max_threat_speed = speed
                                
                                if speed > 40 or self.force_alert: 
                                    target_col = self.RED
                                    hud_col = self.RED
                                    is_danger = True
                                elif speed > 15: target_col = self.AMBER

                        self.tracker[obj_id] = (center[0], center[1], curr_t)
                        
                        # Tactical Reticle Design
                        cv2.rectangle(frame, (x1, y1), (x2, y2), target_col, 1)
                        l = 25 # Corner length
                        cv2.line(frame, (x1, y1), (x1+l, y1), target_col, 3)
                        cv2.line(frame, (x1, y1), (x1, y1+l), target_col, 3)
                        cv2.putText(frame, f"TRGT_{label.upper()}: {speed} units", (x1, y1-10), 0, 0.4, target_col, 1)

            # 3. HUD OVERLAY
            if is_danger and int(time.time() * 5) % 2 == 0:
                cv2.rectangle(frame, (5, 5), (w-5, h-5), self.RED, 10) # Alert Pulse

            # Security Indicator
            auth_text = "AUTHORIZED" if self.authorized else "LOCKED"
            auth_col = self.GREEN if self.authorized else self.RED
            cv2.putText(frame, f"SECURITY_BRIDGE: {auth_text}", (30, 40), 0, 0.5, auth_col, 2)

            # System Data
            cv2.rectangle(frame, (10, 10), (w-10, h-10), hud_col, 1)
            cv2.putText(frame, f"AEGIS_STATUS: {'DANGER' if is_danger else 'SECURE'}", (30, h-30), 0, 0.5, hud_col, 1)
            cv2.putText(frame, f"PEAK_VELOCITY: {self.max_threat_speed}", (w-200, h-30), 0, 0.5, hud_col, 1)

            # Auth Prompt Overlay
            if self.awaiting_code:
                overlay = frame.copy()
                cv2.rectangle(overlay, (w//2-100, h//2-30), (w//2+100, h//2+30), (0,0,0), -1)
                cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
                cv2.putText(frame, "AWAITING AUTH CODE", (w//2-85, h//2+5), 0, 0.5, (0, 255, 255), 1)

            cv2.imshow("AEGIS DEFENCE SYSTEM", frame)
            if cv2.waitKey(1) == ord('q'): break

        self.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    AegisElite().run()