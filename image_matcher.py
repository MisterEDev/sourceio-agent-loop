import base64
import io
import json
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
import imagehash
from loguru import logger
from PIL import Image

load_dotenv()

DATABASE_FILE = "word_database.json"
HAMMING_DISTANCE_THRESHOLD = 2 

client = genai.Client()

_CACHE: dict[str, str] = {}


def _load_cache() -> dict[str, str]:
    global _CACHE
    if os.path.exists(DATABASE_FILE):
        try:
            with open(DATABASE_FILE, "r") as f:
                _CACHE = json.load(f)
        except json.JSONDecodeError:
            _CACHE = {}
    return _CACHE


def _save_cache() -> None:
    with open(DATABASE_FILE, "w") as f:
        json.dump(_CACHE, f, indent=4)

_load_cache()


def convert_b64_to_image_bytes(b64_str: str):
    if "," in b64_str:
        b64_str = b64_str.split(",")[1]
    return base64.b64decode(b64_str.strip())


def get_perceptual_hash(image_bytes: bytes):
    img = Image.open(io.BytesIO(image_bytes))

    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        background = Image.new("RGBA", img.size, (255, 255, 255))
        alpha = img.convert("RGBA").split()[3]
        background.paste(img, mask=alpha)
        img = background.convert("L")
    else:
        img = img.convert("L")

    return imagehash.dhash(img, hash_size=8)


def send_image_to_llm(image_bytes: bytes):
    contents = [
        (
            "Return ONLY the exact single word shown in this image, in"
            " lowercase, with no extra formatting, quotes, or punctuation."
        ),
        types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
    ]

    config = types.GenerateContentConfig(tools=[])

    response = client.models.generate_content(
        model="gemma-4-26b-a4b-it", contents=contents, config=config
    )

    return response.text if response.text else ""


def lookup_in_cache(current_hash: imagehash.ImageHash):
    current_hash_str = str(current_hash)

    if current_hash_str in _CACHE:
        return _CACHE[current_hash_str]

    for cached_hash_str, word in _CACHE.items():
        cached_hash = imagehash.hex_to_hash(cached_hash_str)
        if (current_hash - cached_hash) <= HAMMING_DISTANCE_THRESHOLD:
            logger.info(
                f"Fuzzy pHash HIT ({current_hash - cached_hash} bits diff) for"
                f" '{current_hash_str}' -> '{word}'"
            )
            return word

    return None


def get_image_word(b64_str: str):
    image_bytes = convert_b64_to_image_bytes(b64_str)
    current_hash = get_perceptual_hash(image_bytes)
    hash_str = str(current_hash)

    cached_word = lookup_in_cache(current_hash)
    if cached_word:
        logger.info(f"Cache HIT for visual hash '{hash_str}' -> '{cached_word}'")
        return cached_word

    logger.info(f"Cache MISS for visual hash '{hash_str}'. Querying LLM...")
    raw_response = send_image_to_llm(image_bytes)

    extracted_word = (
        raw_response.replace("`", "").replace('"', "").lower().strip()
    )

    _CACHE[hash_str] = extracted_word
    _save_cache()

    logger.success(
        f"Saved visual hash '{hash_str}' mapped to '{extracted_word}'"
    )
    return extracted_word