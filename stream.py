from openai import OpenAI

client = OpenAI(api_key="ollama", base_url="http://localhost:12000/v1")

stream_response = client.chat.completions.create(
    model="llama3.1",
    messages=[{"role": "user", "content": "こんにちは"}],
    temperature=0.3,
    stream=True,
)

for chunk in stream_response:
    print(chunk.choices[0].delta.content)
