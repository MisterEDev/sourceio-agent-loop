import base64
import json
import os
import pickle
import cv2
import numpy as np

TEMPLATE_FILE = "char_templates.pkl"
DATABASE_FILE = "word_database.json"


def load_templates() -> dict:
    if not os.path.exists(TEMPLATE_FILE):
        raise FileNotFoundError(f"Template file '{TEMPLATE_FILE}' not found!")
    with open(TEMPLATE_FILE, "rb") as f:
        return pickle.load(f)


def save_result_to_json(image_id: str, extracted_word: str):
    """Appends results to the local JSON database file."""
    database = {}
    if os.path.exists(DATABASE_FILE):
        try:
            with open(DATABASE_FILE, "r") as f:
                database = json.load(f)
        except json.JSONDecodeError:
            database = {}

    database[image_id] = extracted_word

    with open(DATABASE_FILE, "w") as f:
        json.dump(database, f, indent=4)


def place_on_standard_canvas(char_crop, canvas_size=(16, 16)):
    """Centers a letter crop onto a uniform 16x16 white canvas."""
    h, w = char_crop.shape
    canvas = np.full(canvas_size, 255, dtype=np.uint8)

    y_offset = max(0, (canvas_size[0] - h) // 2)
    x_offset = max(0, (canvas_size[1] - w) // 2)

    h_clamp = min(h, canvas_size[0])
    w_clamp = min(w, canvas_size[1])

    canvas[y_offset : y_offset + h_clamp, x_offset : x_offset + w_clamp] = (
        char_crop[:h_clamp, :w_clamp]
    )
    return canvas


def extract_character_crops(img_grayscale):
    """Robust character extraction with automatic background detection."""
    # 1. Add white border
    img_padded = cv2.copyMakeBorder(
        img_grayscale, 4, 4, 4, 4, cv2.BORDER_CONSTANT, value=255
    )

    # 2. Thresholding: Dark text on light background
    _, thresh = cv2.threshold(img_padded, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # 3. Ensure background is white (255) and text is black (0)
    # If corners are mostly black, invert the image
    corner_pixels = [thresh[0, 0], thresh[0, -1], thresh[-1, 0], thresh[-1, -1]]
    if sum(corner_pixels) < (255 * 2):  # If background turned black
        thresh = cv2.bitwise_not(thresh)

    # 4. Invert strictly for contour search (OpenCV finds white shapes on black)
    thresh_inv = cv2.bitwise_not(thresh)
    contours, _ = cv2.findContours(thresh_inv, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    letter_boxes = []
    img_h, img_w = thresh.shape

    for c in contours:
        x, y, w, h = cv2.boundingRect(c)

        # Ignore full image bounding box or single-pixel dots
        if w >= 1 and h >= 3 and not (w >= img_w - 2 and h >= img_h - 2):
            letter_boxes.append((x, y, w, h))

    # Sort left-to-right
    letter_boxes = sorted(letter_boxes, key=lambda box: box[0])

    print(f"\n[DEBUG] Detected {len(letter_boxes)} valid letter contour(s).")

    char_crops = []
    for idx, (x, y, w, h) in enumerate(letter_boxes):
        crop = thresh[y:y+h, x:x+w]
        normalized_crop = place_on_standard_canvas(crop)

        # Save crops to project folder for inspection
        debug_filename = f"crop_{idx}.png"
        cv2.imwrite(debug_filename, normalized_crop)
        print(f" -> Saved '{debug_filename}' ({w}x{h}px box centered on 16x16 canvas)")

        char_crops.append(normalized_crop)

    return char_crops


def identify_character(char_canvas, templates: dict) -> str:
    """Matches character crop and prints top confidence scores."""
    best_label = "?"
    best_score = -1.0

    for label, template_canvas in templates.items():
        res = cv2.matchTemplate(char_canvas, template_canvas, cv2.TM_CCOEFF_NORMED)
        score = res[0][0]

        if score > best_score:
            best_score = score
            best_label = label

    print(f"[MATCH] Best fit: '{best_label}' | Score: {best_score:.4f}")
    return best_label


def parse_base64_image(base64_str: str, templates: dict) -> str:
    if "," in base64_str:
        base64_str = base64_str.split(",")[1]

    img_bytes = base64.b64decode(base64_str)
    np_arr = np.frombuffer(img_bytes, np.uint8)
    img_grayscale = cv2.imdecode(np_arr, cv2.IMREAD_GRAYSCALE)

    crops = extract_character_crops(img_grayscale)
    word = "".join(
        [identify_character(crop, templates) for crop in crops]
    )

    return word


if __name__ == "__main__":
    templates = load_templates()

    # The Base64 string for "pull"
    test_base64_string = """
    data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACUAAAAQCAYAAACRKbYdAAAACXBIWXMAAAsTAAALEwEAmpwYAAACOUlEQVR4nM3VSajOYRQG8J/xmkVyu6IkkQVl2FAsDJGUIRaUREpcEpmSIWzugpWFQlKILoXFpchUkqGUjEVsTJHM1+zTq/PVv3/f963crqfexfed03mf9zzPOX/+LTZhB+qwFbUlcnpiDmZhKiajryZCKzxCIc5vPCiRNyaTk84vrGpKUnOxErvjstu5nBYYhAM4iif4jhVNRSpLbiJ+4qbyaIe9aMTyfDC1+TmG4w1e4i4mRLwtpuMSNsd/LdEfR7AlV68NpgSpaxVIdcI+fMTSfLCof2NG51TwDgajPZbgCw5mujESP3A5Vy89YlqZWBZdsR/vsLgUqWcYjW5B5CreYg06Yhk+R5GE1mHY5IcLuXpVmFkmlkX38FZSZ1EpUvdDkoQuWB9t3YXOYcRP2JORaBy+4UyuXurs7IidrUAqrYZDeIWFpUjdyrV1NT4EqfzvIqlJ+IqGXL0OMYUpdqoCqRocxgssKNepJFtCP5zDa2wISdeFR85nulkbF5/I1Utyz4/YyQqkeqMeTzGvFKlf4Zk3QSYVvBdmTnLMibz3IdfxIJPMfyxzyTbsxOl4xJ3wZZJnYHR4QNRLw3Ml5KsLjw6JnL+XXQ+2xel7GJ+Bqlh4fbA9Yl9jPayPiU0SJIyIVxdKnMfhsy5BplDm3ECvIqmzMVFJquo4abnJrICaeM1YDI3OzMCoyKkO2dJQrMXG+P7VxQOGRdfHx2qpj443xP0X40vQo0gqb9ZmRyEY/3do3dwEsvgDEH2jaLavGzgAAAAASUVORK5CYII=
    """.strip()

    test_image_id = "pull_base64_test"

    try:
        extracted_word = parse_base64_image(test_base64_string, templates)
        print(f"\n[SUCCESS] Extracted word: -> '{extracted_word}'")

        save_result_to_json(test_image_id, extracted_word)
        print(
            f"[SAVED] Result stored under ID '{test_image_id}' in '{DATABASE_FILE}'"
        )

    except Exception as e:
        print(f"[ERROR] Failed to process Base64 string: {e}")