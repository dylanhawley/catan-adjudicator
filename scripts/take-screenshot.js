#!/usr/bin/env node

/**
 * Takes a screenshot of the running web app and saves it to docs/app-preview.png
 * This script is used by the GitHub Actions workflow to automatically update
 * the README screenshot.
 */

const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const SCREENSHOT_PATH = path.join(__dirname, '..', 'docs', 'app-preview.png');
const APP_URL = process.env.APP_URL || 'http://localhost:3000';
const VIEWPORT_WIDTH = 1280;
const VIEWPORT_HEIGHT = 720;

async function takeScreenshot() {
  console.log(`Taking screenshot of ${APP_URL}...`);
  
  // Ensure docs directory exists
  const docsDir = path.dirname(SCREENSHOT_PATH);
  if (!fs.existsSync(docsDir)) {
    fs.mkdirSync(docsDir, { recursive: true });
  }

  const browser = await chromium.launch({
    headless: true,
  });

  try {
    const context = await browser.newContext({
      viewport: {
        width: VIEWPORT_WIDTH,
        height: VIEWPORT_HEIGHT,
      },
    });

    const page = await context.newPage();
    
    // Navigate to the app
    console.log(`Navigating to ${APP_URL}...`);
    await page.goto(APP_URL, {
      waitUntil: 'networkidle',
      timeout: 30000,
    });

    // Wait for the main content to be visible
    // Adjust selector based on your app structure
    try {
      await page.waitForSelector('main', { timeout: 10000 });
      console.log('Main content loaded');
    } catch (e) {
      console.warn('Main selector not found, proceeding anyway...');
    }

    // Wait a bit more for any animations or lazy loading
    await page.waitForTimeout(2000);

    // Take screenshot
    console.log(`Saving screenshot to ${SCREENSHOT_PATH}...`);
    await page.screenshot({
      path: SCREENSHOT_PATH,
      fullPage: false, // Use viewport size for consistent screenshots
    });

    console.log('Screenshot saved successfully!');
  } catch (error) {
    console.error('Error taking screenshot:', error);
    process.exit(1);
  } finally {
    await browser.close();
  }
}

takeScreenshot().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
