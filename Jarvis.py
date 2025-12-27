import cv2
import numpy as np
import math

# --- CONFIGURATION ---
COLOR_CYAN = (255, 255, 0)      # Electric Blue
COLOR_RED = (0, 0, 255)
FONT = cv2.FONT_HERSHEY_SIMPLEX
MAX_FRAMES = 60                 # How many angles to capture (more = smoother)

def process_blueprint_frame(image):
    """Converts a single frame into the blueprint style."""
    h, w = image.shape[:2]
    
    # mask out background (Center Circle)
    mask = np.zeros((h, w), dtype=np.uint8)
    center_x, center_y = w // 2, h // 2
    radius = int(min(h, w) * 0.35)
    cv2.circle(mask, (center_x, center_y), radius, (255), -1)
    
    masked = cv2.bitwise_and(image, image, mask=mask)
    
    # Edge Detection
    gray = cv2.cvtColor(masked, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, 40, 120)
    
    # Colorize
    blueprint = np.zeros((h, w, 3), dtype=np.uint8)
    blueprint[edges > 0] = COLOR_CYAN
    
    # Add weak fill
    blueprint[mask == 255] = cv2.add(blueprint[mask == 255], (30, 10, 0))
    
    return blueprint

def main():
    cap = cv2.VideoCapture(0)
    
    # Variables
    state = "READY"   # READY -> RECORDING -> PROCESSING -> INTERACTIVE
    scanned_frames = []
    current_frame_index = 0
    recording_progress = 0
    
    # Mouse interaction variables
    is_dragging = False
    last_mouse_x = 0
    
    def mouse_handler(event, x, y, flags, param):
        nonlocal current_frame_index, is_dragging, last_mouse_x
        
        if state == "INTERACTIVE":
            if event == cv2.EVENT_LBUTTONDOWN:
                is_dragging = True
                last_mouse_x = x
            elif event == cv2.EVENT_LBUTTONUP:
                is_dragging = False
            elif event == cv2.EVENT_MOUSEMOVE and is_dragging:
                # Dragging controls rotation (frames)
                dx = x - last_mouse_x
                if abs(dx) > 5: # Sensitivity threshold
                    if dx > 0:
                        current_frame_index = (current_frame_index - 1) % len(scanned_frames)
                    else:
                        current_frame_index = (current_frame_index + 1) % len(scanned_frames)
                    last_mouse_x = x

    cv2.namedWindow("360 Scanner")
    cv2.setMouseCallback("360 Scanner", mouse_handler)
    
    print("System Online. Rotate object during scan.")

    while True:
        ret, frame = cap.read()
        if not ret: break
        
        h, w = frame.shape[:2]
        center_x, center_y = w // 2, h // 2
        display = frame.copy()

        # --- STATE 1: READY ---
        if state == "READY":
            # Target Circle
            cv2.circle(display, (center_x, center_y), int(min(h,w)*0.35), COLOR_CYAN, 2)
            
            # Instructions
            cv2.putText(display, "STEP 1: ALIGN OBJECT", (center_x - 120, h - 80), FONT, 0.6, COLOR_CYAN, 1)
            cv2.putText(display, "PRESS [SPACE] TO START 360 SCAN", (center_x - 160, h - 50), FONT, 0.6, (0, 255, 0), 1)
            
            key = cv2.waitKey(1)
            if key == 32: # SPACE
                state = "RECORDING"
                scanned_frames = []
                recording_progress = 0

        # --- STATE 2: RECORDING (The Spin) ---
        elif state == "RECORDING":
            # Instructions
            cv2.putText(display, "ROTATE OBJECT SLOWLY...", (center_x - 130, 50), FONT, 0.8, COLOR_RED, 2)
            
            # Record Frame
            if recording_progress % 2 == 0: # Capture every 2nd frame to save memory
                scanned_frames.append(frame.copy())
            
            recording_progress += 1
            
            # Draw Progress Bar
            bar_width = 300
            fill = int((len(scanned_frames) / MAX_FRAMES) * bar_width)
            cv2.rectangle(display, (center_x - 150, h - 60), (center_x + 150, h - 40), (50, 50, 50), -1)
            cv2.rectangle(display, (center_x - 150, h - 60), (center_x - 150 + fill, h - 40), COLOR_CYAN, -1)
            
            # Stop when full
            if len(scanned_frames) >= MAX_FRAMES:
                state = "PROCESSING"
        
        # --- STATE 3: PROCESSING ---
        elif state == "PROCESSING":
            display = np.zeros_like(frame)
            cv2.putText(display, "CONVERTING TO BLUEPRINT...", (center_x - 160, center_y), FONT, 0.7, COLOR_CYAN, 2)
            cv2.imshow("360 Scanner", display)
            cv2.waitKey(1)
            
            # Convert all recorded frames to blueprints
            # (We do this in a loop so it creates a slight loading pause)
            processed_list = []
            for raw_frame in scanned_frames:
                bp = process_blueprint_frame(raw_frame)
                processed_list.append(bp)
            
            scanned_frames = processed_list # Replace raw video with blueprints
            state = "INTERACTIVE"
            
        # --- STATE 4: INTERACTIVE 3D ---
        elif state == "INTERACTIVE":
            # Show the current frame based on index
            if scanned_frames:
                display = scanned_frames[current_frame_index]
            
            # UI Overlay
            cv2.putText(display, "INTERACTIVE 3D VIEW", (30, 50), FONT, 0.8, COLOR_CYAN, 2)
            cv2.putText(display, "< DRAG MOUSE TO ROTATE >", (center_x - 140, h - 40), FONT, 0.6, (200, 200, 200), 1)
            
            # Frame counter HUD
            cv2.putText(display, f"ANGLE: {current_frame_index}/{MAX_FRAMES}", (w - 180, 50), FONT, 0.5, COLOR_CYAN, 1)

            key = cv2.waitKey(1)
            if key == ord('r'):
                state = "READY"

        cv2.imshow("360 Scanner", display)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()