import base64
import json
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from loguru import logger

load_dotenv()

DATABASE_FILE = "word_database.json"
client = genai.Client()

def convert_b64_image(b64_str: str):
    if "," in b64_str:
        b64_str = b64_str.split(",")[1]

    image_bytes = base64.b64decode(b64_str.strip())

    return types.Part.from_bytes(data=image_bytes, mime_type="image/png")


def send_image_to_llm(b64_list: list[str]):
    contents = [
        "Return ONLY the exact single word shown in this image, in lowercase, with no extra formatting, quotes, or punctuation."
    ]

    for b64 in b64_list:
        image_part = convert_b64_image(b64)
        contents.append(image_part)

    config = types.GenerateContentConfig(tools=[])

    response = client.models.generate_content(
        model="gemma-4-26b-a4b-it", contents=contents, config=config
    )

    return response.text if response.text else ""


def get_image_word(b64_str: str):
    clean_key = (
        b64_str.split(",")[1] if "," in b64_str else b64_str
    ).strip()

    cache = {}
    if os.path.exists(DATABASE_FILE):
        try:
            with open(DATABASE_FILE, "r") as f:
                cache = json.load(f)
        except json.JSONDecodeError:
            cache = {}

    if clean_key in cache:
        logger.info(f"Cache hit for key starting with '{clean_key[:10]}...'")
        return cache[clean_key]

    logger.info(f"Cache miss. Sending image payload to LLM...")
    raw_response = send_image_to_llm([clean_key])

    extracted_word = (
        raw_response.replace("`", "").replace('"', "").lower().strip()
    )

    cache[clean_key] = extracted_word
    with open(DATABASE_FILE, "w") as f:
        json.dump(cache, f, indent=4)

    logger.success(f"Saved new word mapping: '{extracted_word}'")
    return extracted_word
