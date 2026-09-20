import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv("variables.env")

print("starting test...")
print("key loaded:", bool(os.getenv("DEEPSEEK_API_KEY")))

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)

print("sending request...")

response = client.chat.completions.create(
    model="deepseek-flash",
    messages=[
        {
            "role": "user",
            "content": "Say hello in one sentence."
        }
    ],
    max_tokens=50,
)

print("response received")

print(response)
print("finish_reason:", response.choices[0].finish_reason)
print("content:", repr(response.choices[0].message.content))
print(
    "reasoning:",
    repr(response.choices[0].message.reasoning_content)
)
print("usage:", response.usage)