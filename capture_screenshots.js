const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

// Dashboard pages to capture
const dashboardPages = [
  { name: 'main-dashboard', url: 'http://localhost:3000', description: 'Main Dashboard Overview' },
  { name: 'bias-detection', url: 'http://localhost:3000/bias-detection', description: 'Advanced Bias Detection with SHAP/LIME' },
  { name: 'knowledge-graph', url: 'http://localhost:3000/knowledge-graph', description: 'Knowledge Graph Integration' },
  { name: 'geographic-bias', url: 'http://localhost:3000/geographic-bias', description: 'Geographic Bias Analysis' },
  { name: 'model-dna', url: 'http://localhost:3000/model-dna', description: 'Model DNA Signatures' },
  { name: 'monitoring', url: 'http://localhost:3000/monitoring', description: 'Real-time Monitoring' },
  { name: 'compliance', url: 'http://localhost:3000/compliance', description: 'Compliance Tracking' },
  { name: 'analytics', url: 'http://localhost:3000/analytics', description: 'Analytics Dashboard' }
];

// Create screenshots directory
const screenshotsDir = path.join(__dirname, 'docs/v2/fairmind-website/public/screenshots/dashboard');
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
    for (const page of dashboardPages) {
      console.log(`📸 Capturing ${page.name}...`);
      
      const browserPage = await browser.newPage();
      
      // Set viewport for desktop
      await browserPage.setViewport({ width: 1920, height: 1080 });
      
      // Navigate to page
      await browserPage.goto(page.url, { 
        waitUntil: 'networkidle2',
        timeout: 30000 
      });
      
      // Wait for content to load
      await new Promise(resolve => setTimeout(resolve, 3000));
      
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
    const response = await fetch('http://localhost:3000');
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
