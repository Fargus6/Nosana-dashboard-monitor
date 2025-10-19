#!/usr/bin/env python3
"""
Debug pagination - check what pagination elements exist
"""
import asyncio
import sys
sys.path.append('/app/backend')

import os
os.environ['PLAYWRIGHT_BROWSERS_PATH'] = '/pw-browsers'

from playwright.async_api import async_playwright

async def debug_pagination():
    node_address = "9hsWPkJUBiDQnc2p7dKi2gMKHp6LwscA6Z5qAF8NGsyV"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        url = f"https://dashboard.nosana.com/host/{node_address}"
        print(f"📡 Loading: {url}\n")
        
        await page.goto(url, wait_until='networkidle', timeout=30000)
        await page.wait_for_selector('table', timeout=10000)
        
        # Debug: Check pagination elements
        pagination_info = await page.evaluate('''() => {
            const info = {
                navigation_elements: [],
                buttons_with_numbers: [],
                links_with_numbers: [],
                next_buttons: [],
                all_text: []
            };
            
            // Check for navigation role
            const nav = document.querySelector('[role="navigation"]');
            if (nav) {
                info.navigation_elements.push(nav.outerHTML.substring(0, 500));
                
                // Get all buttons and links in navigation
                const buttons = nav.querySelectorAll('button');
                buttons.forEach(btn => {
                    const text = btn.textContent.trim();
                    info.all_text.push(text);
                    if (/^\d+$/.test(text)) {
                        info.buttons_with_numbers.push({
                            text: text,
                            disabled: btn.disabled,
                            className: btn.className
                        });
                    }
                    if (text.toLowerCase().includes('next') || text === '›' || text === '>') {
                        info.next_buttons.push({
                            text: text,
                            disabled: btn.disabled,
                            className: btn.className
                        });
                    }
                });
                
                const links = nav.querySelectorAll('a');
                links.forEach(link => {
                    const text = link.textContent.trim();
                    info.all_text.push(text);
                    if (/^\d+$/.test(text)) {
                        info.links_with_numbers.push({
                            text: text,
                            href: link.href,
                            className: link.className
                        });
                    }
                });
            }
            
            // Also check for any pagination outside navigation
            const allButtons = document.querySelectorAll('button');
            allButtons.forEach(btn => {
                const text = btn.textContent.trim();
                if (/^[1-9]\d*$/.test(text)) {
                    info.buttons_with_numbers.push({
                        text: text,
                        disabled: btn.disabled,
                        className: btn.className,
                        location: 'outside-nav'
                    });
                }
            });
            
            return info;
        }''')
        
        print("="*100)
        print("PAGINATION DEBUG INFO")
        print("="*100 + "\n")
        
        print("📋 All text in navigation:")
        print(pagination_info['all_text'])
        print()
        
        print("🔢 Buttons with numbers:")
        for btn in pagination_info['buttons_with_numbers']:
            print(f"   • {btn}")
        print()
        
        print("🔗 Links with numbers:")
        for link in pagination_info['links_with_numbers']:
            print(f"   • {link}")
        print()
        
        print("➡️  Next buttons:")
        for btn in pagination_info['next_buttons']:
            print(f"   • {btn}")
        print()
        
        print("📄 Navigation HTML (first 500 chars):")
        for nav_html in pagination_info['navigation_elements']:
            print(nav_html)
        print()
        
        # Take screenshot
        await page.screenshot(path='/app/backend/pagination_debug.png', full_page=True)
        print("📸 Screenshot saved: /app/backend/pagination_debug.png")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_pagination())
