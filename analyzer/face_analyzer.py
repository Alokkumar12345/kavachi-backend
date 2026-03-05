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
            
        # 4. Extract Skin Tone
        (x, y, w, h) = faces[0]
        # Crop to the center-top of the face (usually forehead/cheeks) to avoid hair/beard
        skin_roi = img[int(y + h * 0.2):int(y + h * 0.5), int(x + w * 0.3):int(x + w * 0.7)]
        
        if skin_roi.size == 0:
            return {"error": "Could not extract skin region."}
            
        # --- DEFINITIVE LIGHTING-INVARIANT LOGIC (LAB & ITA) ---
        # Switch to CIE L*a*b* color space
        # L* = Lightness, a* = Green/Red, b* = Blue/Yellow
        lab_roi = cv2.cvtColor(skin_roi, cv2.COLOR_BGR2Lab)
        
        # Calculate mean Values
        mean_l, mean_a, mean_b = cv2.mean(lab_roi)[:3]
        
        # 1. ITA Calculation (Individual Typology Angle)
        # ITA = arctan((L - 50) / b) * (180 / pi)
        # Higher ITA (>55) is Very Light, lower is Dark.
        # It is highly resistant to lighting intensity (brightness) changes.
        import math
        # Prevent division by zero and handle scale (OpenCV L is 0-255, b is 0-255)
        # Convert OpenCV scale back to standard LAB scale:
        # L [0, 100], a [-128, 127], b [-128, 127]
        l_std = (mean_l * 100.0) / 255.0
        b_std = mean_b - 128.0
        
        # Calculate ITA
        ita = math.atan2((l_std - 50.0), b_std) * (180.0 / math.pi)
        
        # 2. Undertone Analysis (using normalized a* and b*)
        # a* > 0 is Reddish/Pink (Cool), b* > 0 is Yellowish/Golden (Warm)
        a_std = mean_a - 128.0
        
        # Undertone metric (Warmth Index)
        # Usually, Warm skin has b > a by a significant margin
        warmth_index = b_std - a_std
        
        if warmth_index > 12:
            undertone = "Warm"
        elif warmth_index < 0:
            undertone = "Cool"
        else:
            undertone = "Neutral"

        # 3. Final Tone Assignment based on ITA (Skin Group) and Undertone
        # Standard ITA Ranges:
        # > 55: Very Light
        # 41 to 55: Light
        # 28 to 41: Intermediate (Medium)
        # 10 to 28: Tan
        # -30 to 10: Brown
        # < -30: Dark
        
        if ita < 10:
            if undertone == "Warm": tone = "Deep Cocoa"
            elif undertone == "Cool": tone = "Cool Ebony"
            else: tone = "Rich Espresso"
        elif ita < 28:
            if undertone == "Warm": tone = "Warm Bronze Glow"
            elif undertone == "Cool": tone = "Rosy Cool"
            else: tone = "Natural Tan"
        elif ita < 50:
            if undertone == "Warm": tone = "Caramel Warmth"
            elif undertone == "Cool": tone = "Soft Rosy"
            else: tone = "Balanced Neutral"
        else:
            if undertone == "Warm": tone = "Golden Glow"
            elif undertone == "Cool": tone = "Porcelain Light"
            else: tone = "Soft Almond"

        # Special Refinement for "Sun-Kissed" (Very high Warmth)
        if warmth_index > 25:
            tone = "Sun-Kissed Warmth"

        # Special Refinement for "Olive" (Medium ITA but lower warmth)
        if 28 < ita < 45 and warmth_index < 5 and a_std < 0:
            tone = "Olive Undertone"
            
        # ROI for returning to frontend (for visual reference)
        pixels = np.float32(skin_roi.reshape(-1, 3))
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 5, 1.0)
        _, labels, palette = cv2.kmeans(pixels, 1, None, criteria, 1, cv2.KMEANS_RANDOM_CENTERS)
        dominant_bgr = palette[0]
        dominant_rgb = (int(dominant_bgr[2]), int(dominant_bgr[1]), int(dominant_bgr[0]))
            
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
