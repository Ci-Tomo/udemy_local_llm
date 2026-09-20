from openai import OpenAI

client = OpenAI(api_key="ollama", base_url="http://localhost:12000/v1")

response = client.chat.completions.create(
    model="llama3.1",
    messages=[{"role": "user", "content": "こんにちは、LLMについて教えて"}],
    temperature=0.3,
)

print(response)
print(response.choices[0].message.content)
