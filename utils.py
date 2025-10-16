import base64
from io import BytesIO
from PIL import Image
import requests
from duckduckgo_search import DDGS



def write_excel(df):
    from io import BytesIO
    import pandas as pd
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

def generate_short_description(product):
    name = product.get("Item Description", "Product")
    return f"{name} - High quality and reliable."

def generate_long_description(product):
    name = product.get("Item Description", "Product")
    desc = product.get("description", "")
    return f"{name} is a premium product. {desc} Perfect for customers who want quality and performance."



def generate_product_image(keyword: str) -> str:
    try:
        with DDGS() as ddgs:
            results = ddgs.images(keyword, max_results=1)
            results = list(results)  # DDGS returns a generator
            if results:
                image_url = results[0]["image"]
                resp = requests.get(image_url, timeout=10)
                img = Image.open(BytesIO(resp.content)).convert("RGB")
            else:
                img = Image.new("RGB", (200, 200), color=(255, 255, 255))

        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return f"data:image/png;base64,{img_str}"

    except Exception as e:
        print("Image fetch failed:", e)
        img = Image.new("RGB", (200, 200), color=(255, 255, 255))
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return f"data:image/png;base64,{img_str}"
