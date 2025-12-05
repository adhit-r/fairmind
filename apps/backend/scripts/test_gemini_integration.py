import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.services.ai_compliance_automation_service import AIComplianceAutomationService, LLMProvider
from config.settings import settings

async def test_gemini():
    print("Testing Gemini Integration...")
    
    # Check for API Key
    api_key = settings.google_api_key or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GOOGLE_API_KEY not found in settings or environment variables.")
        print("Please set GOOGLE_API_KEY in your .env file.")
        return

    try:
        service = AIComplianceAutomationService(provider=LLMProvider.GEMINI)
        
        print(f"✓ Service initialized with provider: {service.provider}")
        print("Sending test request to Gemini...")
        
        response = await service._call_llm(
            system_prompt="You are a helpful assistant.",
            user_prompt="Say 'Hello from Gemini!' if you can hear me.",
            max_tokens=50
        )
        
        print("✓ Response received:")
        print(f"  {response}")
        print("\nGemini integration is working correctly! 🎉")
        
    except Exception as e:
        print(f"❌ Error testing Gemini: {e}")

if __name__ == "__main__":
    asyncio.run(test_gemini())
