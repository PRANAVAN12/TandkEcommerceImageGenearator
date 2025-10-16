import google.generativeai as genai
from config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)

def generate_image(keyword):
    if not keyword:
        return ""
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        prompt = f"Generate realistic product image of '{keyword}' on white background."
        result = model.generate_content(prompt)

        if result and result.candidates:
            for part in result.candidates[0].content.parts:
                if hasattr(part, "inline_data"):
                    img_base64 = part.inline_data.data
                    return f"data:image/png;base64,{img_base64}"
        return ""
    except Exception:
        return ""
