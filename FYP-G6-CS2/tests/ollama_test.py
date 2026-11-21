'''
import os
from ollama import Client
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file
OLLAMA_KEY = os.getenv("OLLAMA_API_KEY")
print(f"Using Ollama API Key: {OLLAMA_KEY[:4]}...{OLLAMA_KEY[-4:]}")
# Initialize the client pointing directly to Ollama's Cloud API
client = Client(
    host="https://ollama.com",
    headers={
        "Authorization": f"Bearer {OLLAMA_KEY}"
    }
)

# Call a cloud-hosted model (cloud models use the '-cloud' suffix)
response = client.chat(
    model="gemma4:31b-cloud",
    messages=[
        {
            "role": "user",
            "content": "Write a python function to check if a number is prime."
        }
    ]
)

print(response.message.content)
'''

import ollama

stream = ollama.chat(
    model="gemma3:270m",
    messages=[{"role": "user", "content": "Write a short poem about coding."}],
    stream=True,  # Enables streaming
)

for chunk in stream:
    print(chunk['message']['content'], end='', flush=True)
print()
