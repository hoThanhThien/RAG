import urllib.request, json

api_key = "sk-447fbba1d2602589-xn5eog-e44ed208"
base_url = "https://gatecheap.io.vn/v1"
model = "cx/gpt-5.5"

payload = json.dumps({
    "model": model,
    "messages": [{"role": "user", "content": "Xin chào, trả lời 1 câu ngắn."}],
    "max_tokens": 50
}).encode()

req = urllib.request.Request(
    f"{base_url}/chat/completions",
    data=payload,
    headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
    },
    method="POST"
)
try:
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read())
        print("OK:", data["choices"][0]["message"]["content"])
except urllib.error.HTTPError as e:
    body = e.read().decode(errors="replace")
    print(f"HTTP ERROR {e.code}: {body[:300]}")
except Exception as e:
    print("ERROR:", e)
