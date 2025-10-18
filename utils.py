import base64
from io import BytesIO
from PIL import Image
import pandas as pd
import streamlit as st
import google.generativeai as genai

# -----------------------------
# Gemini client setup
# -----------------------------


def init_gemini_client(api_key: str):
    genai.configure(api_key=api_key)
    return genai

# -----------------------------
# Excel export
# -----------------------------
def write_excel(df: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()



def generate_product_image(client, product: dict) -> str:
    item_desc = product.get("Item Description", "Product")
    prompt = f"High-quality e-commerce product photo of {item_desc}, white background, realistic, studio lighting"
    try:
        chat = client.chats.create(
            model="gemini-2.5-flash-image",
            config=types.GenerateContentConfig(response_modalities=["IMAGE"])
        )
        response = chat.send_message(prompt)
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                img_bytes = part.inline_data.data
                img_base64 = base64.b64encode(img_bytes).decode("utf-8")
                return f"data:image/png;base64,{img_base64}"
    except Exception as e:
        print("Gemini Image generation error:", e)
    # Fallback white image
    img = Image.new("RGB", (256, 256), (255, 255, 255))
    buf = BytesIO()
    img.save(buf, format="PNG")
    return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode('utf-8')}"

def generate_short_description(client, product: dict) -> str:
    item_desc = product.get("Item Description", "Product")
    prompt = (
        f"Write a short, concise paragraph describing '{item_desc}' for e-commerce. "
        "Highlight quality and key features in 1–2 sentences."
    )
    try:
        chat = client.chats.create(model="gemini-2.0-flash")
        response = chat.send_message(prompt)
        text_output = "".join([p.text for p in response.candidates[0].content.parts if p.text])
        return text_output.strip()
    except Exception as e:
        print("Gemini Short Description error:", e)
        return f"{item_desc} is a high-quality, reliable product for e-commerce."

def generate_long_description(product: dict) -> str:
    item_desc = product.get("Item Description", "Product")
    return f"{item_desc} is a premium product suitable for your e-commerce store. Features high quality, durability, and excellent value for customers."
