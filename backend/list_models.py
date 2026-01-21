from google import genai
from config import config

client = genai.Client(api_key=config.GEMINI_API_KEY)
print('Available Gemini models:')
models = client.models.list()
for model in models:
    if 'gemini' in model.name.lower():
        print(f'  - {model.name}')
