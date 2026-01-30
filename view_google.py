"""Open Google.com and capture what's visible."""

from playwright.sync_api import sync_playwright

print("Opening Google.com...")

with sync_playwright() as p:
    # Try headless mode
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    page.goto("https://www.google.com")
    page.wait_for_load_state("networkidle")

    # Take screenshot
    page.screenshot(path="google_screenshot.png")
    print("Screenshot saved: google_screenshot.png")

    # Get page title
    print(f"\nPage Title: {page.title()}")

    # Get visible text elements
    print("\n--- Visible Elements ---")

    # Search box
    search_box = page.query_selector('textarea[name="q"], input[name="q"]')
    if search_box:
        print("✓ Search box found")

    # Logo
    logo = page.query_selector('img[alt="Google"]')
    if logo:
        print("✓ Google logo found")

    # Buttons
    buttons = page.query_selector_all('input[type="submit"], button')
    button_texts = [b.get_attribute("value") or b.inner_text() for b in buttons[:5]]
    print(f"✓ Buttons: {button_texts}")

    # Links in footer/header
    links = page.query_selector_all('a')
    link_texts = [l.inner_text().strip() for l in links if l.inner_text().strip()][:10]
    print(f"✓ Links: {link_texts}")

    # Any special doodle or message
    doodle = page.query_selector('#hplogo, .hplogo')
    if doodle:
        alt = doodle.get_attribute("alt") or doodle.get_attribute("title")
        if alt:
            print(f"✓ Doodle/Logo text: {alt}")

    browser.close()
    print("\nDone!")
