import pandas as pd
import base64
from io import BytesIO
from PIL import Image
import requests

# ------------------------
# Excel helper
# ------------------------
def write_excel(df: pd.DataFrame) -> bytes:
    """Convert DataFrame to Excel bytes for download"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

# ------------------------
# Image helper
# ------------------------
def image_to_base64(image_path: str) -> str:
    """Convert local image to base64"""
    try:
        with open(image_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
            return f"data:image/png;base64,{encoded}"
    except Exception as e:
        print(f"Error encoding image: {e}")
        return ""

# ------------------------
# AI Generation helpers (placeholders)
# ------------------------
def generate_short_description(product: dict) -> str:
    """Generate a short description for a product"""
    name = product.get("product_name", "Product")
    return f"{name} - High quality and reliable."

def generate_long_description(product: dict) -> str:
    """Generate a long description for a product"""
    name = product.get("product_name", "Product")
    desc = product.get("description", "")
    return f"{name} is a premium product. {desc} Perfect for customers who want quality and performance."

def generate_product_image(product: dict) -> str:
    """Generate base64 image for product (placeholder)"""
    # Here you can call your Gemini/OpenAI image API
    # For now, we return a placeholder blank image
    img = Image.new("RGB", (200, 200), color=(255, 255, 255))
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{img_str}"
