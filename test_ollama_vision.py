import base64
import requests

image_path = r"C:\Users\sakur\Downloads\5925957191263260374.jpg"

with open(image_path, "rb") as f:
    image_data = base64.b64encode(f.read()).decode("utf-8")

payload = {
"model": "qwen3.8:27b",
"messages": [{
"role": "user",
"content": "Опиши изображение по-русски. Перечисли видимые детали. Не выдумывай технические характеристики.",
"images": [image_data]
}],
"stream": False
}

print("Передаю изображение в Qwen...")
response = requests.post(
"http://localhost:11434/api/chat",
json=payload,
timeout=600
)
response.raise_for_status()
print("\nОтвет Qwen:\n")
print(response.json()["message"]["content"])
