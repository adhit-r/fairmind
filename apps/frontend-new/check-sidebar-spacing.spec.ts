import { test, expect } from '@playwright/test'

test.describe('Sidebar Spacing Check', () => {
  test('check sidebar vertical spacing', async ({ page }) => {
    // Navigate to dashboard
    await page.goto('http://localhost:1111/dashboard')
    
    // Wait for page to load
    await page.waitForLoadState('networkidle')
    
    // Wait for sidebar to be visible
    const sidebar = page.locator('[data-sidebar="sidebar"]').first()
    await expect(sidebar).toBeVisible()
    
    // Get sidebar bounding box
    const sidebarBox = await sidebar.boundingBox()
    
    // Get the navigation container (first scrollable div inside sidebar)
    const navContainer = sidebar.locator('div.flex-1.overflow-y-auto').first()
    await expect(navContainer).toBeVisible()
    
    const navBox = await navContainer.boundingBox()
    
    // Get the first navigation item
    const firstNavItem = navContainer.locator('button, a').first()
    await expect(firstNavItem).toBeVisible()
    
    const firstItemBox = await firstNavItem.boundingBox()
    
    // Calculate spacing
    if (sidebarBox && navBox && firstItemBox) {
      const topSpacing = firstItemBox.y - sidebarBox.y
      const navTopSpacing = firstItemBox.y - navBox.y
      
      console.log('=== SIDEBAR SPACING ANALYSIS ===')
      console.log(`Sidebar top: ${sidebarBox.y}px`)
      console.log(`Sidebar height: ${sidebarBox.height}px`)
      console.log(`Navigation container top: ${navBox.y}px`)
      console.log(`Navigation container height: ${navBox.height}px`)
      console.log(`First nav item top: ${firstItemBox.y}px`)
      console.log(`Top spacing (sidebar to first item): ${topSpacing}px`)
      console.log(`Nav container top spacing: ${navTopSpacing}px`)
      console.log('================================')
      
      // Check if there's excessive spacing (more than 80px would be too much)
      if (topSpacing > 80) {
        console.error(`⚠️  EXCESSIVE SPACING DETECTED: ${topSpacing}px from sidebar top to first item`)
      } else {
        console.log(`✅ Spacing looks reasonable: ${topSpacing}px`)
      }
    }
    
    // Take a screenshot for visual inspection
    await page.screenshot({ 
      path: 'sidebar-spacing-check.png',
      fullPage: true 
    })
    
    // Also get computed styles
    const navContainerStyles = await navContainer.evaluate((el) => {
      const styles = window.getComputedStyle(el)
      return {
        paddingTop: styles.paddingTop,
        marginTop: styles.marginTop,
        padding: styles.padding,
        margin: styles.margin,
      }
    })
    
    console.log('Navigation container styles:', navContainerStyles)
  })
})

