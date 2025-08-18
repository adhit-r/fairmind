const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

// Documentation and app pages to capture
const BASE_URL_WEBSITE = process.env.WEBSITE_URL || 'http://localhost:4321';
const BASE_URL_APP = process.env.APP_URL || 'http://localhost:3000';

const documentationPages = [
  // App (Fairmind) screenshots
  { name: 'app-dashboard', url: `${BASE_URL_APP}/`, description: 'App Dashboard' },
  { name: 'app-bias-detection', url: `${BASE_URL_APP}/bias-detection`, description: 'Bias Detection' },
  { name: 'app-models', url: `${BASE_URL_APP}/models`, description: 'Model Registry' },
  { name: 'app-monitoring', url: `${BASE_URL_APP}/monitoring`, description: 'Monitoring' },
  { name: 'app-provenance', url: `${BASE_URL_APP}/provenance`, description: 'Model Provenance' },
  // Website screenshots used in docs cards
  { name: 'docs-overview', url: `${BASE_URL_WEBSITE}/docs`, description: 'Documentation Overview' },
  { name: 'docs-fumadocs', url: `${BASE_URL_WEBSITE}/docs/fumadocs`, description: 'Docs Landing' },
  { name: 'features', url: `${BASE_URL_WEBSITE}/features`, description: 'Features Page' },
  { name: 'about', url: `${BASE_URL_WEBSITE}/about`, description: 'About Page' },
  { name: 'contact', url: `${BASE_URL_WEBSITE}/contact`, description: 'Contact Page' },
  { name: 'references', url: `${BASE_URL_WEBSITE}/blog`, description: 'References Page' },
  { name: 'demo', url: `${BASE_URL_WEBSITE}/demo`, description: 'Demo Page' }
];

// Create screenshots directory
const screenshotsDir = path.join(__dirname, '../fairmind-website/public/screenshots');
if (!fs.existsSync(screenshotsDir)) {
  fs.mkdirSync(screenshotsDir, { recursive: true });
}

async function captureScreenshots() {
  console.log('🚀 Starting screenshot capture...');
  
  const browser = await puppeteer.launch({
    headless: true,
    defaultViewport: { width: 1920, height: 1080 },
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  try {
    for (const page of documentationPages) {
      console.log(`📸 Capturing ${page.name}...`);
      
      const browserPage = await browser.newPage();
      
      // Set viewport for desktop
      await browserPage.setViewport({ width: 1920, height: 1080 });
      
      // Navigate to page
      await browserPage.goto(page.url, { 
        waitUntil: 'networkidle2',
        timeout: 30000 
      });
      
      // Wait for content to load - longer wait for app pages
      const waitTime = page.url.includes('localhost:300') ? 8000 : 3000;
      await new Promise(resolve => setTimeout(resolve, waitTime));
      
      // For app pages, wait for specific content to load
      if (page.url.includes('localhost:300')) {
        try {
          await browserPage.waitForSelector('main, .main-content, [data-testid="main-content"]', { timeout: 10000 });
        } catch (e) {
          console.log(`⚠️  No main content selector found for ${page.name}, proceeding anyway`);
        }
      }
      
      // Take screenshot
      const screenshotPath = path.join(screenshotsDir, `${page.name}.png`);
      await browserPage.screenshot({
        path: screenshotPath,
        fullPage: true
      });
      
      console.log(`✅ Captured ${page.name} → ${screenshotPath}`);
      
      await browserPage.close();
    }
    
    console.log('🎉 All screenshots captured successfully!');
    
  } catch (error) {
    console.error('❌ Error capturing screenshots:', error);
  } finally {
    await browser.close();
  }
}

// Wait for server to be ready, then capture screenshots
async function main() {
  console.log('⏳ Waiting for server to be ready...');
  
  // Wait 10 seconds for server to start
  await new Promise(resolve => setTimeout(resolve, 10000));
  
  // Check if server is running
  try {
    const response = await fetch('http://localhost:4321');
    if (response.ok) {
      console.log('✅ Server is ready!');
      await captureScreenshots();
    } else {
      console.log('❌ Server not responding');
    }
  } catch (error) {
    console.log('❌ Server not ready yet, retrying...');
    // Retry after 5 more seconds
    await new Promise(resolve => setTimeout(resolve, 5000));
    await captureScreenshots();
  }
}

main().catch(console.error);
