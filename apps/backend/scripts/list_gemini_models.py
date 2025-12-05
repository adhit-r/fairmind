import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

async def list_models():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("No API key found")
        return

    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            for model in data.get('models', []):
                print(f"- {model['name']}")
        else:
            print(response.text)

if __name__ == "__main__":
    asyncio.run(list_models())
