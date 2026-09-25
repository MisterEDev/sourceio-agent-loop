import pickle
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONT_PATH = "IBMPlexMonoFont/IBMPlexMono-Regular.ttf"
OUTPUT_TEMPLATE_FILE = "char_templates.pkl"

def place_on_standard_canvas(char_crop, canvas_size=(16, 16)):
    h, w = char_crop.shape
    canvas = np.full(canvas_size, 255, dtype=np.uint8)
    
    y_offset = max(0, (canvas_size[0] - h) // 2)
    x_offset = max(0, (canvas_size[1] - w) // 2)
    
    h_clamp = min(h, canvas_size[0])
    w_clamp = min(w, canvas_size[1])
    
    canvas[y_offset:y_offset+h_clamp, x_offset:x_offset+w_clamp] = char_crop[:h_clamp, :w_clamp]
    return canvas

def generate_synthetic_templates(font_size=11):
    templates = {}
    
    try:
        font = ImageFont.truetype(FONT_PATH, font_size)
    except OSError:
        print(f"[ERROR] Could not find '{FONT_PATH}'. Ensure the file is in the script directory.")
        return

    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

    for char in alphabet:
        img = Image.new("L", (30, 30), color=255)
        draw = ImageDraw.Draw(img)
        
        draw.text((8, 5), char, fill=0, font=font)
        
        img_np = np.array(img)
        
        _, thresh = cv2.threshold(img_np, 180, 255, cv2.THRESH_BINARY)
        
        thresh_inv = cv2.bitwise_not(thresh)
        contours, _ = cv2.findContours(thresh_inv, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            c = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(c)
            tight_crop = thresh[y:y+h, x:x+w]
            
            template_canvas = place_on_standard_canvas(tight_crop)
            templates[char] = template_canvas

    with open(OUTPUT_TEMPLATE_FILE, "wb") as f:
        pickle.dump(templates, f)

    print(f"[SUCCESS] Generated {len(templates)} synthetic character templates using IBM Plex Mono!")
