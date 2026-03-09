import requests

response = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "mistral",
        "prompt": "Extract price from HTML: <span class='price'>$199</span>",
        "stream": False
    }
)

print(response.json()["response"])