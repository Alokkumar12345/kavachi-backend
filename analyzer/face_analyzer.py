import cv2
import numpy as np
import base64
import sys
import json
import os

def analyze_image(base64_str):
    try:
        # 1. Decode base64 image
        if ',' in base64_str:
            base64_str = base64_str.split(',')[1]
        
        img_data = base64.b64decode(base64_str)
        nparr = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return {"error": "Could not decode image."}

        # --- OPTIMIZATION: Immediate Resizing ---
        # Resizing the image to a smaller width significantly speeds up face detection
        target_width = 400
        h_orig, w_orig = img.shape[:2]
        ratio = target_width / float(w_orig)
        target_height = int(h_orig * ratio)
        img = cv2.resize(img, (target_width, target_height), interpolation=cv2.INTER_AREA)

        # 2. Check Lighting Conditions
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        avg_v = np.mean(v)
        
        if avg_v < 40:
            return {"error": "Image is too dark. Please ensure proper lighting."}
        elif avg_v > 230:
            return {"error": "Image is too bright/overexposed. Please adjust lighting."}

        # 3. Detect Faces
        cascade_path = os.path.join(os.path.dirname(__file__), 'haarcascade_frontalface_default.xml')
        face_cascade = cv2.CascadeClassifier(cascade_path)
        
        if face_cascade.empty():
            return {"error": "Internal Error: Haar cascade file not found."}
            
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # Optimized detectMultiScale parameters
        faces = face_cascade.detectMultiScale(gray, 1.2, 5, minSize=(30, 30))
        
        if len(faces) == 0:
            return {"error": "No face detected. Please face the camera directly."}
        elif len(faces) > 1:
            return {"error": "Multiple faces detected. Please ensure only one person is in the frame."}
            
        # 4. Extract Skin Tone
        (x, y, w, h) = faces[0]
        # Crop to the center-top of the face (usually forehead/cheeks) to avoid hair/beard
        skin_roi = img[int(y + h * 0.2):int(y + h * 0.5), int(x + w * 0.3):int(x + w * 0.7)]
        
        if skin_roi.size == 0:
            return {"error": "Could not extract skin region."}
            
        pixels = np.float32(skin_roi.reshape(-1, 3))
        
        # --- OPTIMIZATION: Simplified KMeans ---
        n_colors = 1
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 5, 1.0)
        flags = cv2.KMEANS_RANDOM_CENTERS
        _, labels, palette = cv2.kmeans(pixels, n_colors, None, criteria, 1, flags)
        
        dominant_bgr = palette[0]
        # Convert BGR to RGB
        r, g, b = (int(dominant_bgr[2]), int(dominant_bgr[1]), int(dominant_bgr[0]))
        dominant_rgb = (r, g, b)
        
        # --- IMPROVED CLASSIFICATION LOGIC ---
        # 1. Intensity (Brightness)
        brightness = (r + g + b) / 3
        
        # 2. Undertone Analysis (Warm vs Cool vs Neutral)
        # Standard skin: R > G > B
        rg_diff = r - g
        gb_diff = g - b
        
        # Determine Undertone
        if rg_diff > gb_diff + 15:
            undertone = "Warm"
        elif gb_diff > rg_diff + 15:
            undertone = "Cool"
        else:
            undertone = "Neutral"

        # 3. Final Tone Assignment
        if brightness < 80:
            tone = f"Deep {undertone}"
            if undertone == "Warm": tone = "Deep Cocoa"
            elif undertone == "Cool": tone = "Cool Ebony"
            else: tone = "Rich Espresso"
        elif brightness < 130:
            tone = f"Medium {undertone}"
            if undertone == "Warm": tone = "Warm Bronze Glow"
            elif undertone == "Cool": tone = "Rosy Cool" # This was catching too many
            else: tone = "Natural Tan"
        elif brightness < 180:
            tone = f"Light-Medium {undertone}"
            if undertone == "Warm": tone = "Caramel Warmth"
            elif undertone == "Cool": tone = "Soft Rosy"
            else: tone = "Balanced Neutral" # "Dull" usually falls here
        else:
            tone = f"Fair {undertone}"
            if undertone == "Warm": tone = "Golden Glow"
            elif undertone == "Cool": tone = "Porcelain Light"
            else: tone = "Soft Almond"

        # Special casing for "Sun-Kissed" if very high Red
        if r > g * 1.35 and r > b * 1.35:
            tone = "Sun-Kissed Warmth"

        # Special casing for "Olive" if Green is high
        if g > r * 0.95 and g > b * 1.05:
            tone = "Olive Undertone"
            
        return {
            "success": True,
            "lighting": "Optimal",
            "detectedTone": tone,
            "dominantRgb": dominant_rgb
        }
        
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    # Expect base64 string from stdin
    input_data = sys.stdin.read().strip()
    if not input_data:
        print(json.dumps({"error": "No input provided"}))
        sys.exit(1)
        
    result = analyze_image(input_data)
    print(json.dumps(result))
