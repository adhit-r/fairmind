"""
Playwright Demo: Automated Evidence Collection for Compliance
This script demonstrates how the compliance system automatically collects evidence
"""

import asyncio
from playwright.async_api import async_playwright

async def demo_automated_compliance():
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False, slow_mo=1000)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            record_video_dir="./artifacts",
            record_video_size={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        print("🎬 Starting Automated Evidence Collection Demo...")
        
        # Navigate to compliance dashboard
        print("📍 Navigating to Compliance Dashboard...")
        await page.goto('http://localhost:1111/compliance-dashboard')
        await page.wait_for_load_state('networkidle')
        await asyncio.sleep(2)
        
        # Highlight the automated evidence toggle
        print("✨ Showing Automated Evidence Collection Toggle...")
        await page.locator('text=Automated Evidence Collection Enabled').highlight()
        await asyncio.sleep(2)
        
        # Show the evidence source legend
        print("🎨 Highlighting Evidence Sources...")
        await page.locator('text=Automated Evidence Sources:').scroll_into_view_if_needed()
        await asyncio.sleep(2)
        
        # Select a model
        print("🤖 Selecting a model...")
        model_select = page.locator('label:has-text("Model") + div button')
        await model_select.click()
        await asyncio.sleep(1)
        await page.locator('text=Demo Model 001').click()
        await asyncio.sleep(1)
        
        # Select framework
        print("📋 Selecting EU AI Act framework...")
        framework_select = page.locator('label:has-text("Framework") + div button')
        await framework_select.click()
        await asyncio.sleep(1)
        await page.locator('text=EU AI Act').first.click()
        await asyncio.sleep(1)
        
        # Click Check Compliance
        print("🔍 Running Automated Compliance Check...")
        check_button = page.locator('button:has-text("Check Compliance (Auto)")')
        await check_button.click()
        
        # Wait for results
        print("⏳ Waiting for automated evidence collection...")
        await page.wait_for_selector('text=Automated Evidence Collection', timeout=10000)
        await asyncio.sleep(2)
        
        # Scroll to automated evidence sources card
        print("📊 Showing Automated Evidence Sources Card...")
        evidence_card = page.locator('text=Automated Evidence Collection').locator('..')
        await evidence_card.scroll_into_view_if_needed()
        await asyncio.sleep(3)
        
        # Highlight each evidence source
        print("🎯 Highlighting individual evidence sources...")
        sources = [
            "Dataset Service",
            "Bias Detection",
            "Model Registry",
            "Monitoring",
            "Security Tests"
        ]
        
        for source in sources:
            try:
                source_element = page.locator(f'text={source}').first
                if await source_element.is_visible():
                    await source_element.highlight()
                    print(f"   ✓ {source}")
                    await asyncio.sleep(1)
            except:
                print(f"   ⚠ {source} not found")
        
        # Scroll to requirements table
        print("📝 Showing Requirements with Evidence Sources...")
        await page.locator('text=Requirements').click()
        await asyncio.sleep(2)
        
        # Scroll through some requirements
        await page.mouse.wheel(0, 500)
        await asyncio.sleep(2)
        
        # Show gaps tab
        print("⚠️ Showing Compliance Gaps...")
        await page.locator('text=Recommendations').click()
        await asyncio.sleep(3)
        
        # Final overview
        print("📈 Showing Final Compliance Score...")
        await page.locator('text=Overall Score').scroll_into_view_if_needed()
        await asyncio.sleep(3)
        
        print("✅ Demo Complete!")
        print("📹 Video saved to ./artifacts/")
        
        # Keep browser open for a moment
        await asyncio.sleep(2)
        
        await context.close()
        await browser.close()

if __name__ == "__main__":
    print("=" * 60)
    print("AUTOMATED EVIDENCE COLLECTION DEMO")
    print("=" * 60)
    print()
    print("This demo shows how FairMind automatically collects")
    print("compliance evidence from existing features:")
    print()
    print("  🗄️  Dataset Service → Dataset quality metrics")
    print("  🧠 Bias Detection → Training data bias analysis")
    print("  📁 Model Registry → Versioning, access controls")
    print("  📊 Monitoring → Performance drift, fairness metrics")
    print("  🔒 Security Tests → Adversarial robustness")
    print()
    print("=" * 60)
    print()
    
    asyncio.run(demo_automated_compliance())
