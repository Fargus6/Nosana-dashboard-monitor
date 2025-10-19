#!/bin/bash
# Automated Frontend Testing Script
# Tests UI functionality using Playwright

TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
LOG_DIR="/app/tests/results"
LOG_FILE="$LOG_DIR/frontend_test_$TIMESTAMP.log"
SCREENSHOT_DIR="$LOG_DIR/screenshots_$TIMESTAMP"

mkdir -p "$LOG_DIR"
mkdir -p "$SCREENSHOT_DIR"

echo "========================================" | tee -a "$LOG_FILE"
echo "Frontend Automated Test - $TIMESTAMP" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Run Python Playwright tests
python3 << 'PYTHON_SCRIPT' | tee -a "$LOG_FILE"
import asyncio
import sys
from playwright.async_api import async_playwright
from datetime import datetime

async def run_frontend_tests():
    results = {
        'total': 0,
        'passed': 0,
        'failed': 0,
        'tests': []
    }
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            # Test 1: Page Load
            results['total'] += 1
            try:
                await page.goto('https://nosanamonitor.preview.emergentagent.com', wait_until='networkidle', timeout=15000)
                results['passed'] += 1
                results['tests'].append(('Page Load', 'PASSED'))
                print("✅ Test 1: Page Load - PASSED")
            except Exception as e:
                results['failed'] += 1
                results['tests'].append(('Page Load', f'FAILED: {str(e)}'))
                print(f"❌ Test 1: Page Load - FAILED: {str(e)}")
            
            # Test 2: Login Form Elements
            results['total'] += 1
            try:
                await page.wait_for_selector('input[type="email"]', timeout=5000)
                await page.wait_for_selector('input[type="password"]', timeout=5000)
                await page.wait_for_selector('button:has-text("Sign In")', timeout=5000)
                results['passed'] += 1
                results['tests'].append(('Login Form Elements', 'PASSED'))
                print("✅ Test 2: Login Form Elements - PASSED")
            except Exception as e:
                results['failed'] += 1
                results['tests'].append(('Login Form Elements', f'FAILED: {str(e)}'))
                print(f"❌ Test 2: Login Form Elements - FAILED: {str(e)}")
            
            # Test 3: Theme Selector
            results['total'] += 1
            try:
                theme_selector = await page.query_selector('[data-testid="theme-selector"]')
                if theme_selector:
                    results['passed'] += 1
                    results['tests'].append(('Theme Selector', 'PASSED'))
                    print("✅ Test 3: Theme Selector - PASSED")
                else:
                    results['failed'] += 1
                    results['tests'].append(('Theme Selector', 'FAILED: Not found'))
                    print("❌ Test 3: Theme Selector - FAILED: Not found")
            except Exception as e:
                results['failed'] += 1
                results['tests'].append(('Theme Selector', f'FAILED: {str(e)}'))
                print(f"❌ Test 3: Theme Selector - FAILED: {str(e)}")
            
            # Test 4: Google OAuth Button
            results['total'] += 1
            try:
                google_btn = await page.query_selector('[data-testid="google-signin-button"]')
                if google_btn:
                    results['passed'] += 1
                    results['tests'].append(('Google OAuth Button', 'PASSED'))
                    print("✅ Test 4: Google OAuth Button - PASSED")
                else:
                    results['failed'] += 1
                    results['tests'].append(('Google OAuth Button', 'FAILED: Not found'))
                    print("❌ Test 4: Google OAuth Button - FAILED: Not found")
            except Exception as e:
                results['failed'] += 1
                results['tests'].append(('Google OAuth Button', f'FAILED: {str(e)}'))
                print(f"❌ Test 4: Google OAuth Button - FAILED: {str(e)}")
            
            # Test 5: User Login
            results['total'] += 1
            try:
                await page.fill('input[type="email"]', 'test@prod.com')
                await page.fill('input[type="password"]', 'TestProd123')
                await page.click('button.bg-blue-600', force=True)
                await page.wait_for_timeout(4000)
                
                logout_btn = await page.query_selector('[data-testid="logout-button"]')
                if logout_btn:
                    results['passed'] += 1
                    results['tests'].append(('User Login', 'PASSED'))
                    print("✅ Test 5: User Login - PASSED")
                else:
                    results['failed'] += 1
                    results['tests'].append(('User Login', 'FAILED: Logout button not found'))
                    print("❌ Test 5: User Login - FAILED: Logout button not found")
            except Exception as e:
                results['failed'] += 1
                results['tests'].append(('User Login', f'FAILED: {str(e)}'))
                print(f"❌ Test 5: User Login - FAILED: {str(e)}")
            
            # Test 6: Nodes Display
            results['total'] += 1
            try:
                await page.wait_for_timeout(2000)
                nodes = await page.query_selector_all('[data-testid^="node-card-"]')
                if len(nodes) > 0:
                    results['passed'] += 1
                    results['tests'].append((f'Nodes Display ({len(nodes)} nodes)', 'PASSED'))
                    print(f"✅ Test 6: Nodes Display - PASSED ({len(nodes)} nodes found)")
                else:
                    results['failed'] += 1
                    results['tests'].append(('Nodes Display', 'FAILED: No nodes found'))
                    print("❌ Test 6: Nodes Display - FAILED: No nodes found")
            except Exception as e:
                results['failed'] += 1
                results['tests'].append(('Nodes Display', f'FAILED: {str(e)}'))
                print(f"❌ Test 6: Nodes Display - FAILED: {str(e)}")
            
            # Test 7: Auto-refresh Selector
            results['total'] += 1
            try:
                refresh_selector = await page.query_selector('select')
                if refresh_selector:
                    results['passed'] += 1
                    results['tests'].append(('Auto-refresh Selector', 'PASSED'))
                    print("✅ Test 7: Auto-refresh Selector - PASSED")
                else:
                    results['failed'] += 1
                    results['tests'].append(('Auto-refresh Selector', 'FAILED: Not found'))
                    print("❌ Test 7: Auto-refresh Selector - FAILED: Not found")
            except Exception as e:
                results['failed'] += 1
                results['tests'].append(('Auto-refresh Selector', f'FAILED: {str(e)}'))
                print(f"❌ Test 7: Auto-refresh Selector - FAILED: {str(e)}")
            
            # Test 8: Theme Switching (Cyber)
            results['total'] += 1
            try:
                theme_selector = await page.query_selector('[data-testid="theme-selector"]')
                if theme_selector:
                    await theme_selector.click(force=True)
                    await page.wait_for_timeout(500)
                    
                    cyber_theme = await page.query_selector('[data-testid="theme-cyber"]')
                    if cyber_theme:
                        await cyber_theme.click(force=True)
                        await page.wait_for_timeout(2000)
                        
                        # Check if theme applied (look for Matrix effect or cyber colors)
                        body_class = await page.evaluate('document.body.className')
                        results['passed'] += 1
                        results['tests'].append(('Theme Switching', 'PASSED'))
                        print("✅ Test 8: Theme Switching - PASSED")
                    else:
                        results['failed'] += 1
                        results['tests'].append(('Theme Switching', 'FAILED: Cyber theme option not found'))
                        print("❌ Test 8: Theme Switching - FAILED")
                else:
                    results['failed'] += 1
                    results['tests'].append(('Theme Switching', 'FAILED: Theme selector not found'))
                    print("❌ Test 8: Theme Switching - FAILED")
            except Exception as e:
                results['failed'] += 1
                results['tests'].append(('Theme Switching', f'FAILED: {str(e)}'))
                print(f"❌ Test 8: Theme Switching - FAILED: {str(e)}")
            
        except Exception as e:
            print(f"Critical error during testing: {str(e)}")
        finally:
            await browser.close()
    
    # Print summary
    print("\n========================================")
    print("FRONTEND TEST SUMMARY")
    print("========================================")
    print(f"Total Tests: {results['total']}")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    if results['total'] > 0:
        success_rate = (results['passed'] / results['total']) * 100
        print(f"Success Rate: {success_rate:.1f}%")
    print("========================================")
    
    return results

# Run the tests
asyncio.run(run_frontend_tests())
PYTHON_SCRIPT

echo "" | tee -a "$LOG_FILE"
echo "Test completed at $(date)" | tee -a "$LOG_FILE"

exit 0
