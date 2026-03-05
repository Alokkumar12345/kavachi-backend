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

        # 2. Comprehensive Quality & Lighting Validation
        hsv_full = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        h_full, s_full, v_full = cv2.split(hsv_full)
        
        # A. Exposure & Focus Check
        avg_v = np.mean(v_full)
        if avg_v < 50:
            return {"error": "Image is too dark (underexposed). Please use natural lighting."}
        if avg_v > 210:
            return {"error": "Image has overexposed highlights. Please avoid direct harsh light."}
            
        gray_full = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray_full, cv2.CV_64F).var()
        if laplacian_var < 40:
            return {"error": "Image is blurry or lacks focus. Please hold the camera still."}

        # B. Color Cast & White Balance
        b_mean, g_mean, r_mean = cv2.mean(img)[:3]
        total_mean = max((r_mean + g_mean + b_mean) / 3, 1)
        if r_mean > total_mean * 1.35 or b_mean > total_mean * 1.35 or g_mean > total_mean * 1.35:
             return {"error": "Strong color cast or colored lighting detected (e.g., LED/Neon). Please use balanced, natural lighting."}

        # 3. Detect Faces
        cascade_path = os.path.join(os.path.dirname(__file__), 'haarcascade_frontalface_default.xml')
        face_cascade = cv2.CascadeClassifier(cascade_path)
        
        if face_cascade.empty():
            return {"error": "Internal Error: Haar cascade file not found."}
            
        # Optimized detectMultiScale parameters
        faces = face_cascade.detectMultiScale(gray_full, 1.2, 5, minSize=(50, 50))
        
        if len(faces) == 0:
            return {"error": "No face detected. Please face the camera directly."}
        elif len(faces) > 1:
            return {"error": "Multiple faces detected. Please ensure only one person is in the frame."}
            
        (x, y, w, h) = faces[0]
        
        # C. Background Influence Check
        # Mask everything outside the face box
        bg_mask = np.ones(img.shape[:2], dtype=np.uint8) * 255
        cv2.rectangle(bg_mask, (x, y), (x+w, y+h), 0, -1)
        bg_s_mean = cv2.mean(s_full, mask=bg_mask)[0]
        if bg_s_mean > 120:  # Highly saturated background
            return {"error": "Background reflects strong colors. Please use a neutral background (white, gray, or natural)."}
        
        # D. Face Shadows & Visibility Validation
        face_roi = img[y:y+h, x:x+w]
        face_v = v_full[y:y+h, x:x+w]
        
        # Left/Right Shadow mismatch (Harsh side lighting)
        left_half_v = np.mean(face_v[:, :w//2])
        right_half_v = np.mean(face_v[:, w//2:])
        if abs(left_half_v - right_half_v) > 40:
            return {"error": "Heavy mixed shadows across the face. Ensure even, frontal lighting."}
            
        # Top/Bottom mismatch (Hat shadows)
        top_half_v = np.mean(face_v[:h//3, :])
        bottom_half_v = np.mean(face_v[h//3:, :])
        if top_half_v < bottom_half_v - 35:
            return {"error": "Hat or heavy hair casting shadow over forehead. Please remove obstructions."}

        # E. Beauty Mode & Filter Detection
        # Texture variance is low when skin is artificially smoothed
        face_gray = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
        texture_var = cv2.Laplacian(face_gray, cv2.CV_64F).var()
        if texture_var < 30:
             return {"error": "Beauty filter or heavy skin smoothing detected. Please use a completely natural photo."}
             
        # F. Obstruction Detection (Eyes/Glasses)
        eye_cascade_path = os.path.join(os.path.dirname(__file__), 'haarcascade_eye.xml')
        eye_cascade = cv2.CascadeClassifier(eye_cascade_path)
        if not eye_cascade.empty():
            eyes = eye_cascade.detectMultiScale(face_gray, 1.3, 5)
            if len(eyes) < 1:
                 return {"error": "Eyes not clearly visible. Please remove sunglasses or heavy obstructions."}

        # 5. Extract Skin Tone with Refined Sampling
        # Forehead (Upper 20-40% height, Center 40% width)
        forehead_y1, forehead_y2 = int(y + h * 0.15), int(y + h * 0.35)
        forehead_x1, forehead_x2 = int(x + w * 0.3), int(x + w * 0.7)
        
        # Cheeks (Middle 40-60% height, Sides)
        cheek_y1, cheek_y2 = int(y + h * 0.45), int(y + h * 0.65)
        l_cheek_x1, l_cheek_x2 = int(x + w * 0.2), int(x + w * 0.4)
        r_cheek_x1, r_cheek_x2 = int(x + w * 0.6), int(x + w * 0.8)

        # Create localized skin masks based on standard human skin HSV bounds
        # Skin hue is typically between 0-25 and 160-180 (red/orange)
        # We apply this specifically to our sampled regions to drop lips, eyes, and stray hair
        def get_skin_pixels(roi_bgr):
            roi_hsv = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2HSV)
            lower_skin1 = np.array([0, 20, 50], dtype=np.uint8)
            upper_skin1 = np.array([25, 255, 255], dtype=np.uint8)
            mask1 = cv2.inRange(roi_hsv, lower_skin1, upper_skin1)
            
            lower_skin2 = np.array([160, 20, 50], dtype=np.uint8)
            upper_skin2 = np.array([180, 255, 255], dtype=np.uint8)
            mask2 = cv2.inRange(roi_hsv, lower_skin2, upper_skin2)
            
            mask = mask1 | mask2
            return roi_bgr[mask > 0]

        # Extract and Combine
        samples = []
        samples.append(get_skin_pixels(img[forehead_y1:forehead_y2, forehead_x1:forehead_x2]))
        samples.append(get_skin_pixels(img[cheek_y1:cheek_y2, l_cheek_x1:l_cheek_x2]))
        samples.append(get_skin_pixels(img[cheek_y1:cheek_y2, r_cheek_x1:r_cheek_x2]))
        
        combined_pixels = []
        for s in samples:
            if s.size > 0:
                combined_pixels.append(s)
        
        if not combined_pixels:
            return {"error": "Could not extract sufficient bare skin pixels. Avoid heavy makeup or facial obstructions."}
            
        skin_pixels = np.vstack(combined_pixels)
        
        # 6. Makeup Detection Validation
        # Check standard deviation of a* and b* channels in skin pixels
        skin_roi_bgr = np.uint8([skin_pixels])
        skin_lab = cv2.cvtColor(skin_roi_bgr, cv2.COLOR_BGR2Lab)[0]
        a_var = np.std(skin_lab[:, 1])
        b_var = np.std(skin_lab[:, 2])
        if a_var < 1.5 and b_var < 1.5:
             return {"error": "Heavy makeup or foundation detected, concealing natural texture. Results may not reflect natural tone."}

        # Use average for ITA calculation
        mean_bgr = np.mean(skin_pixels, axis=0)
        skin_roi_mean = np.uint8([[mean_bgr]]) # 1x1 image for conversion
            
        # --- DEFINITIVE LIGHTING-INVARIANT LOGIC (LAB & ITA) ---
        # Switch to CIE L*a*b* color space using the 1x1 mean image
        # L* = Lightness, a* = Green/Red, b* = Blue/Yellow
        lab_pixel = cv2.cvtColor(skin_roi_mean, cv2.COLOR_BGR2Lab)[0][0]
        mean_l, mean_a, mean_b = lab_pixel
        
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
        # Using KMeans on the stacked sampled pixels to find dominant color
        pixels_float = np.float32(skin_pixels)
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 5, 1.0)
        _, labels, palette = cv2.kmeans(pixels_float, 1, None, criteria, 1, cv2.KMEANS_RANDOM_CENTERS)
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
