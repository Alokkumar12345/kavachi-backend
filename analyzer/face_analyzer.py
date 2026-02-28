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
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        
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
        
        # KMeans to find dominant color
        n_colors = 1
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, .1)
        flags = cv2.KMEANS_RANDOM_CENTERS
        _, labels, palette = cv2.kmeans(pixels, n_colors, None, criteria, 10, flags)
        
        dominant_bgr = palette[0]
        # Convert BGR to RGB
        dominant_rgb = (int(dominant_bgr[2]), int(dominant_bgr[1]), int(dominant_bgr[0]))
        
        # Determine Tone (Simplified logic based on RGB values)
        r, g, b = dominant_rgb
        if r > g * 1.5 and r > b * 1.5:
            tone = "Sun-Kissed Warmth"
        elif b > r * 0.8 and b > g * 0.8:
            tone = "Rosy Cool"
        elif g > r * 1.1 and g > b * 1.1:
            tone = "Olive Undertone"
        elif r > 150 and g > 150 and b < 130:
            tone = "Golden Glow"
        elif r > g * 1.1 and r > b * 1.1 and r < 180:
            tone = "Soft Rosy"
        elif r < 80 and g < 80 and b < 80:
            tone = "Deep Cocoa"
        elif r > 200 and g > 200 and b > 200:
            tone = "Porcelain Light"
        elif r > 160 and g > 120 and b < 100:
            tone = "Warm Bronze Glow"
        elif r > 140 and g > 110 and b > 90 and r > g > b:
            tone = "Caramel Warmth"
        elif r > 180 and g > 170 and b > 150:
            tone = "Soft Almond"
        elif b > r and g > r and abs(g - b) < 20:
            tone = "Cool Ash Undertone"
        elif r > 130 and g > 100 and b < 110:
            tone = "Natural Tan"
        else:
            tone = "Balanced Neutral"
            
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
