#!/usr/bin/env python3
"""
Test Python Prisma client
"""

import asyncio
from prisma import Prisma

async def test_prisma():
    """Test Prisma connection"""
    try:
        prisma = Prisma()
        await prisma.connect()
        
        # Test a simple query
        profiles = await prisma.profile.find_many(take=5)
        print(f"✅ Successfully connected to database")
        print(f"✅ Found {len(profiles)} profiles")
        
        await prisma.disconnect()
        return True
        
    except Exception as e:
        print(f"❌ Prisma test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_prisma())
    if success:
        print("🎉 Python Prisma client is working!")
    else:
        print("💥 Python Prisma client has issues")
