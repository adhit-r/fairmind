import { test } from '@playwright/test'

test('debug all spacing', async ({ page }) => {
  await page.goto('http://localhost:1111/dashboard')
  await page.waitForLoadState('networkidle')
  
  // Get all relevant elements
  const header = page.locator('header').first()
  const sidebar = page.locator('[data-sidebar="sidebar"]').first()
  const mainContent = page.locator('main').first()
  const mainWrapper = page.locator('div.flex.flex-col.flex-1').first()
  
  // Get all bounding boxes
  const headerBox = await header.boundingBox()
  const sidebarBox = await sidebar.boundingBox()
  const mainContentBox = await mainContent.boundingBox()
  const mainWrapperBox = await mainWrapper.boundingBox()
  
  // Get computed styles for all elements
  const headerStyles = await header.evaluate(el => {
    const s = getComputedStyle(el)
    return {
      height: s.height,
      borderBottom: s.borderBottom,
      position: s.position,
      top: s.top,
      zIndex: s.zIndex
    }
  })
  
  const mainContentStyles = await mainContent.evaluate(el => {
    const s = getComputedStyle(el)
    return {
      marginTop: s.marginTop,
      paddingTop: s.paddingTop,
      marginLeft: s.marginLeft,
      padding: s.padding,
      margin: s.margin
    }
  })
  
  const mainWrapperStyles = await mainWrapper.evaluate(el => {
    const s = getComputedStyle(el)
    return {
      marginTop: s.marginTop,
      paddingTop: s.paddingTop,
      marginLeft: s.marginLeft,
      padding: s.padding,
      margin: s.margin
    }
  })
  
  const sidebarNavStyles = await sidebar.locator('div.flex-1.overflow-y-auto').first().evaluate(el => {
    const s = getComputedStyle(el)
    return {
      paddingTop: s.paddingTop,
      marginTop: s.marginTop
    }
  })
  
  console.log('\n============ COMPLETE SPACING DEBUG ============')
  console.log('\n📏 HEADER:')
  console.log('  Box:', headerBox)
  console.log('  Styles:', headerStyles)
  
  console.log('\n📏 SIDEBAR:')
  console.log('  Box:', sidebarBox)
  console.log('  Nav padding:', sidebarNavStyles)
  
  console.log('\n📏 MAIN WRAPPER (div.flex.flex-col.flex-1):')
  console.log('  Box:', mainWrapperBox)
  console.log('  Styles:', mainWrapperStyles)
  
  console.log('\n📏 MAIN CONTENT (<main>):')
  console.log('  Box:', mainContentBox)
  console.log('  Styles:', mainContentStyles)
  
  // Calculate gaps
  if (headerBox && mainContentBox && sidebarBox) {
    const headerBottom = headerBox.y + headerBox.height
    const mainContentTop = mainContentBox.y
    const verticalGap = mainContentTop - headerBottom
    
    console.log('\n🔍 GAP ANALYSIS:')
    console.log(`  Header bottom: ${headerBottom}px`)
    console.log(`  Main content top: ${mainContentTop}px`)
    console.log(`  ⚠️  VERTICAL GAP: ${verticalGap}px`)
    
    if (verticalGap > 1) {
      console.log(`  ❌ PROBLEM FOUND: ${verticalGap}px gap between header and main content`)
    } else {
      console.log(`  ✅ No gap detected`)
    }
  }
  
  // Get first nav item position
  const firstNavItem = sidebar.locator('button, a').first()
  const firstNavBox = await firstNavItem.boundingBox()
  
  if (headerBox && firstNavBox) {
    const headerBottom = headerBox.y + headerBox.height
    const navItemTop = firstNavBox.y
    const navGap = navItemTop - headerBottom
    
    console.log('\n🔍 SIDEBAR NAV GAP:')
    console.log(`  Header bottom: ${headerBottom}px`)
    console.log(`  First nav item top: ${navItemTop}px`)
    console.log(`  Gap: ${navGap}px`)
    
    if (Math.abs(navGap) > 1) {
      console.log(`  ⚠️  Misalignment: ${navGap}px`)
    } else {
      console.log(`  ✅ Aligned correctly`)
    }
  }
  
  console.log('\n================================================\n')
  
  // Take full page screenshot
  await page.screenshot({ 
    path: 'debug-spacing.png',
    fullPage: true 
  })
  
  console.log('Screenshot saved: debug-spacing.png\n')
})

