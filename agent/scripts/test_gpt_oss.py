import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
api_key = os.getenv("GROQ_API_KEY", "").strip()
client = Groq(api_key=api_key)

resp = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[
        {"role": "system", "content": "You are a helpful assistant. Output valid JSON."},
        {"role": "user", "content": 'Respond with {"status": "ok", "message": "hello world"}'}
    ],
    response_format={"type": "json_object"},
    max_tokens=50
)
print("Response content:", resp.choices[0].message.content)
