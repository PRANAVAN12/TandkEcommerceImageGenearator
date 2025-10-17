

from google import genai
from google.genai import types

API_KEY = "AIzaSyA-rBHw05nPOAYg8X_GBgnLLQBKMrxjGos"
client = genai.Client(api_key=API_KEY)


chat = client.chats.create(
    model="gemini-2.5-flash-image",
    config=types.GenerateContentConfig(response_modalities=["IMAGE"])
)

response = chat.send_message("A high-quality red apple on white background")

for i, part in enumerate(response.candidates[0].content.parts):
    if part.inline_data:
        filename = f"test_image_{i+1}.png"
        with open(filename, "wb") as f:
            f.write(part.inline_data.data)
        print(f"✅ Image saved as {filename}")

